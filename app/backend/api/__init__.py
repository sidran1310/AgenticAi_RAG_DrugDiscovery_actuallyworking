"""
API route handlers for the Drug Discovery AI Agent.
Organized by functionality with proper error handling and validation.
"""
import os
import time
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, g, send_file
from typing import Dict, Any
from pydantic import ValidationError

from config import get_config, get_service_status, is_service_available
from models import (
    ChatRequest, ChatResponse, ConfigResponse, HealthResponse,
    RAGSearchRequest, RAGResponse, CompoundsResponse, PapersResponse,
    MemoryResponse, AgentInfo, ErrorResponse
)
from services import agent_service, rag_service, paper_service, compound_service
from middleware import api_middleware, rate_limit
from database import get_tool_stats, log_chat_message
from database import db_manager, get_db_session, ChatMessage
from langchain_agents import get_available_agents

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)
APP_STARTED_AT = time.time()


def model_to_dict(model):
    """Serialize Pydantic v1/v2 models without deprecation warnings."""
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()

@api_bp.route('/health', methods=['GET'])
@api_middleware(rate_limit_enabled=False, cache_enabled=True)
def health_check():
    """Health check endpoint"""
    config = get_config()

    services_status = get_service_status()
    database_ok = db_manager.health_check()

    overall_status = "healthy" if all(status['available'] for status in services_status.values()) and database_ok else "degraded"

    response = HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        version=config.version,
        services=services_status,
        uptime=time.time() - APP_STARTED_AT
    )

    return jsonify(model_to_dict(response)), 200

@api_bp.route('/config', methods=['GET'])
@api_middleware(cache_enabled=True)
def get_config_endpoint():
    """Get backend configuration and status"""
    config = get_config()

    # Get available agents
    agents = []
    for agent in get_available_agents():
        agents.append(AgentInfo(
            id=agent['id'],
            name=agent['name'],
            description=agent['description'],
            status='ready' if agent['status'] == 'ready' else 'unavailable',
            capabilities=["AI Analysis", "Research", "Data Integration"]
        ))

    # Get tool statistics
    tool_stats = get_tool_stats()

    response = ConfigResponse(
        status="ok",
        agent_name=config.name,
        version=config.version,
        capabilities=["ChEMBL Search", "PubMed Integration", "PDB Structure", "Molecular Docking", "RAG Search"],
        groq_available=is_service_available('groq'),
        gemini_available=is_service_available('gemini'),
        agent_types=agents,
        tool_stats=tool_stats,
        services=get_service_status()
    )

    payload = model_to_dict(response)
    payload["agentName"] = payload.get("agent_name")
    return jsonify(payload)

@api_bp.route('/chat', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def chat():
    """Process chat messages"""
    try:
        # Parse and validate request
        data = request.get_json()
        if not data:
            return jsonify(model_to_dict(ErrorResponse(
                error="No JSON data provided",
                code=400
            ))), 400

        try:
            chat_request = ChatRequest(
                message=(data.get('message') or '').strip(),
                agent_type=data.get('agentType', 'default'),
                session_id=getattr(g, 'session_id', None)
            )
        except ValidationError as validation_error:
            return jsonify(model_to_dict(ErrorResponse(
                error="Invalid chat request",
                code=400,
                details={"errors": str(validation_error)}
            ))), 400

        # Process request
        start_time = time.time()
        response = agent_service.process_chat_request(chat_request)
        processing_time = time.time() - start_time

        # Log to database
        try:
            log_chat_message(
                session_id=chat_request.session_id,
                message=chat_request.message,
                response=response.response,
                agent_type=chat_request.agent_type.value,
                processing_time=processing_time
            )
        except Exception as e:
            # Don't fail the request if logging fails
            logger.warning(f"Failed to log chat message: {e}")

        return jsonify(model_to_dict(response))

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to process chat request",
            code=500,
            details={"error": str(e)}
        ))), 500

@api_bp.route('/agents', methods=['GET'])
@api_middleware(cache_enabled=True)
def list_agents():
    """Get available agents"""
    try:
        agents = []
        for agent in get_available_agents():
            agents.append(AgentInfo(
                id=agent['id'],
                name=agent['name'],
                description=agent['description'],
                status='ready' if agent['status'] == 'ready' else 'unavailable'
            ))

        return jsonify({
            "agents": [model_to_dict(agent) for agent in agents],
            "langchain_available": is_service_available('langchain'),
            "langgraph_available": is_service_available('langgraph')
        })

    except Exception as e:
        logger.error(f"Agents endpoint error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to retrieve agents",
            code=500,
            details={"error": str(e)}
        ))), 500

@api_bp.route('/graph/query', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def graph_query():
    """Run LangGraph queries"""
    try:
        from langchain_agents import query_langgraph

        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify(model_to_dict(ErrorResponse(
                error="Query parameter required",
                code=400
            ))), 400

        query = data['query']
        result = query_langgraph(query)

        return jsonify({"data": result, "message": "LangGraph query executed successfully"})

    except Exception as e:
        logger.error(f"LangGraph query error: {str(e)}")
        return jsonify(model_to_dict(ErrorResponse(
            error=f"LangGraph query failed: {str(e)}",
            code=500
        ))), 500

@api_bp.route('/search/manual', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def manual_search():
    """Manual search endpoint for advanced scientific queries"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(model_to_dict(ErrorResponse(
                error="No JSON data provided",
                code=400
            ))), 400

        search_type = data.get('type', 'pubmed')
        query = (data.get('query') or '').strip()
        filters = data.get('filters', {})
        limit = min(int(data.get('limit', 20)), 100)

        if not query:
            return jsonify(model_to_dict(ErrorResponse(
                error="Query parameter required",
                code=400
            ))), 400

        results = {}

        if search_type == 'pubmed':
            from modules.pubmed_api import search_pubmed_advanced
            results = search_pubmed_advanced(query, filters, limit)

        elif search_type == 'chembl':
            from modules.chembl_api import search_chembl, search_chembl_targets
            molecules = search_chembl(query, limit)
            targets = search_chembl_targets(query, limit)
            results = {
                "molecules": molecules,
                "targets": targets,
                "query": query
            }

        elif search_type == 'pubchem':
            from modules.pubchem_api import get_pubchem, search_pubchem_similar
            compound = get_pubchem(query)
            similar = []
            if compound and compound.get('smiles'):
                similar = search_pubchem_similar(compound['smiles'], limit=5)
            results = {
                "compound": compound,
                "similar_compounds": similar,
                "query": query
            }

        elif search_type == 'pdb':
            from modules.pdb_api import search_pdb
            pdb_results = search_pdb(query)
            results = {
                "structures": pdb_results,
                "query": query,
                "count": len(pdb_results)
            }

        else:
            return jsonify(model_to_dict(ErrorResponse(
                error=f"Unknown search type: {search_type}",
                code=400
            ))), 400

        return jsonify({
            "success": True,
            "search_type": search_type,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Manual search error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to perform manual search",
            code=500,
            details={"error": str(e)}
        ))), 500

@api_bp.route('/search/advanced', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def advanced_search():
    """Advanced multi-database search for scientific research"""
    try:
        data = request.get_json()
        if not data:
            return jsonify(model_to_dict(ErrorResponse(
                error="No JSON data provided",
                code=400
            ))), 400

        query = (data.get('query') or '').strip()
        databases = data.get('databases', ['pubmed', 'chembl', 'pubchem'])
        filters = data.get('filters', {})

        if not query:
            return jsonify(model_to_dict(ErrorResponse(
                error="Query parameter required",
                code=400
            ))), 400

        results = {
            "query": query,
            "databases_searched": databases,
            "results": {},
            "cross_references": [],
            "timestamp": datetime.now().isoformat()
        }

        # PubMed search
        if 'pubmed' in databases:
            from modules.pubmed_api import search_pubmed_advanced
            pubmed_results = search_pubmed_advanced(query, filters.get('pubmed', {}), 15)
            results["results"]["pubmed"] = pubmed_results

        # ChEMBL search
        if 'chembl' in databases:
            from modules.chembl_api import search_chembl, search_chembl_targets
            chembl_molecules = search_chembl(query, 10)
            chembl_targets = search_chembl_targets(query, 10)
            results["results"]["chembl"] = {
                "molecules": chembl_molecules,
                "targets": chembl_targets
            }

        # PubChem search
        if 'pubchem' in databases:
            from modules.pubchem_api import get_pubchem
            pubchem_compound = get_pubchem(query)
            results["results"]["pubchem"] = pubchem_compound

        # PDB search
        if 'pdb' in databases:
            from modules.pdb_api import search_pdb
            pdb_results = search_pdb(query)
            results["results"]["pdb"] = {
                "structures": pdb_results,
                "count": len(pdb_results)
            }

        # Generate cross-references
        results["cross_references"] = _generate_cross_references(results["results"])

        return jsonify({
            "success": True,
            "data": results
        })

    except Exception as e:
        logger.error(f"Advanced search error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to perform advanced search",
            code=500,
            details={"error": str(e)}
        ))), 500

def _generate_cross_references(results):
    """Generate cross-references between different databases"""
    cross_refs = []

    # Extract entities from each database
    pubchem_compounds = []
    chembl_compounds = []
    pubmed_pmids = []

    if "pubchem" in results and results["pubchem"]:
        pubchem_compounds.append(results["pubchem"])

    if "chembl" in results and "molecules" in results["chembl"]:
        chembl_compounds = results["chembl"]["molecules"]

    if "pubmed" in results and "results" in results["pubmed"]:
        pubmed_pmids = [r["pmid"] for r in results["pubmed"]["results"]]

    # Find matches between PubChem and ChEMBL
    for pc_compound in pubchem_compounds:
        pc_name = pc_compound.get("name", "").lower()
        pc_smiles = pc_compound.get("smiles")

        for cb_compound in chembl_compounds:
            cb_name = cb_compound.get("name", "").lower()
            cb_smiles = cb_compound.get("smiles")

            # Name similarity check
            if pc_name and cb_name and (pc_name in cb_name or cb_name in pc_name):
                cross_refs.append({
                    "type": "compound_match",
                    "source": "PubChem-ChEMBL",
                    "pubchem_cid": pc_compound.get("cid"),
                    "chembl_id": cb_compound.get("chembl_id"),
                    "confidence": "high",
                    "match_type": "name"
                })

            # SMILES similarity check
            elif pc_smiles and cb_smiles and pc_smiles == cb_smiles:
                cross_refs.append({
                    "type": "compound_match",
                    "source": "PubChem-ChEMBL",
                    "pubchem_cid": pc_compound.get("cid"),
                    "chembl_id": cb_compound.get("chembl_id"),
                    "confidence": "exact",
                    "match_type": "smiles"
                })

    return cross_refs

@api_bp.route('/rag', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def search_rag():
    """Search RAG database"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify(model_to_dict(ErrorResponse(
                error="Query parameter required",
                code=400
            ))), 400

        rag_request = RAGSearchRequest(
            query=data['query'],
            limit=data.get('limit', 10),
            include_metadata=data.get('include_metadata', True),
            min_relevance=data.get('min_relevance', 0.1)
        )

        response = rag_service.search_rag(rag_request)
        return jsonify(model_to_dict(response))

    except Exception as e:
        logger.error(f"RAG search error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to search RAG database",
            code=500,
            details={"error": str(e)}
        ))), 500

@api_bp.route('/compounds', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def search_compounds():
    """Search for compounds"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify(model_to_dict(ErrorResponse(
                error="Query parameter required",
                code=400
            ))), 400

        query = data['query']
        limit = data.get('limit', 10)

        response = compound_service.search_compounds(query, limit)
        return jsonify(model_to_dict(response))

    except Exception as e:
        logger.error(f"Compound search error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to search compounds",
            code=500,
            details={"error": str(e)}
        ))), 500

@api_bp.route('/papers', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def search_papers():
    """Search for research papers"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify(model_to_dict(ErrorResponse(
                error="Query parameter required",
                code=400
            ))), 400

        query = data['query']
        limit = data.get('limit', 10)

        response = paper_service.search_papers(query, limit)
        return jsonify(model_to_dict(response))

    except Exception as e:
        logger.error(f"Paper search error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to search papers",
            code=500,
            details={"error": str(e)}
        ))), 500

@api_bp.route('/structures/search', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def search_structures():
    """Search PDB structures for a protein, disease, or target term."""
    try:
        data = request.get_json() or {}
        query = (data.get("query") or "").strip()
        if not query:
            return jsonify(model_to_dict(ErrorResponse(error="Query parameter required", code=400))), 400

        from modules.pdb_api import search_pdb

        pdb_ids = search_pdb(query)
        return jsonify({
            "query": query,
            "structures": [
                {
                    "pdb_id": pdb_id,
                    "id": pdb_id,
                    "source": "RCSB PDB",
                    "url": f"https://www.rcsb.org/structure/{pdb_id}",
                    "download_url": f"/api/structures/download/{pdb_id}",
                }
                for pdb_id in pdb_ids
            ],
            "total": len(pdb_ids),
        })
    except Exception as e:
        logger.error(f"Structure search error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(error="Failed to search structures", code=500, details={"error": str(e)}))), 500

@api_bp.route('/structures/download/<pdb_id>', methods=['GET'])
@api_middleware(rate_limit_enabled=False)
def download_structure(pdb_id: str):
    """Download a PDB/CIF file and return metadata plus a local serving URL."""
    try:
        from modules.downloader import download_structures

        files = download_structures([pdb_id])
        if not files:
            return jsonify(model_to_dict(ErrorResponse(error=f"Structure {pdb_id} not found", code=404))), 404

        file_path = os.path.abspath(files[0])
        return jsonify({
            "pdb_id": pdb_id.upper(),
            "file_name": os.path.basename(file_path),
            "format": os.path.splitext(file_path)[1].lstrip(".").lower(),
            "file_path": file_path,
            "viewer_url": f"/api/structures/file/{os.path.basename(file_path)}",
        })
    except Exception as e:
        logger.error(f"Structure download error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(error="Failed to download structure", code=500, details={"error": str(e)}))), 500

@api_bp.route('/structures/file/<path:file_name>', methods=['GET'])
@api_middleware(rate_limit_enabled=False)
def serve_structure_file(file_name: str):
    """Serve downloaded PDB/CIF files for browser molecular viewers."""
    allowed_dirs = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "pdb_files")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "pdb_files")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docking_results")),
    ]
    file_path = None
    for base_dir in allowed_dirs:
        candidate = os.path.abspath(os.path.join(base_dir, file_name))
        if candidate.startswith(base_dir) and os.path.exists(candidate):
            file_path = candidate
            break
    if not file_path:
        return jsonify(model_to_dict(ErrorResponse(error="Structure file not found", code=404))), 404
    return send_file(file_path, mimetype="chemical/x-pdb" if file_path.endswith(".pdb") else "chemical/x-cif")

@api_bp.route('/dock', methods=['POST'])
@api_middleware()
@rate_limit(limit=10000)
def run_docking():
    """Run the available docking pipeline or return a transparent fallback result."""
    try:
        data = request.get_json() or {}
        compound = (data.get("compound") or data.get("ligand") or "").strip()
        pdb_ids = data.get("pdb_ids") or ([data.get("pdb_id")] if data.get("pdb_id") else [])
        if not compound or not pdb_ids:
            return jsonify(model_to_dict(ErrorResponse(error="compound and pdb_id/pdb_ids are required", code=400))), 400

        from modules.downloader import download_structures
        from modules.docking import run_docking_pipeline

        structures = download_structures(pdb_ids)
        raw_results, pose_file, receptor_file = run_docking_pipeline(compound, structures)
        scores = []
        for item in raw_results:
            match = __import__("re").search(r"(-?\d+(?:\.\d+)?)\s*kcal", item)
            if match:
                scores.append(float(match.group(1)))

        best_score = min(scores) if scores else None
        return jsonify({
            "status": "success" if raw_results else "no_results",
            "compound": compound,
            "pdb_ids": pdb_ids,
            "results": raw_results,
            "best_score": best_score,
            "binding_affinity": best_score,
            "pose_file": pose_file,
            "receptor_file": receptor_file,
            "pose_viewer_url": f"/api/structures/file/{os.path.basename(pose_file)}" if pose_file else None,
        })
    except Exception as e:
        logger.error(f"Docking error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(error="Failed to run docking", code=500, details={"error": str(e)}))), 500

@api_bp.route('/memory', methods=['GET'])
@api_middleware()
def get_memory():
    """Get agent memory and session information"""
    try:
        from models import MemoryEntry, PlanStep, FewShotExample

        db = get_db_session()
        try:
            rows = (
                db.query(ChatMessage)
                .order_by(ChatMessage.created_at.desc())
                .limit(8)
                .all()
            )
        finally:
            db.close()

        memory_entries = []
        for index, row in enumerate(rows):
            memory_entries.append(MemoryEntry(
                id=f"chat-{row.id}",
                type="short_term" if index < 3 else "episodic",
                content=row.message[:500],
                timestamp=row.created_at.strftime("%Y-%m-%d %H:%M"),
                relevance=max(0.45, 0.98 - index * 0.06),
                source=row.agent_type or "default"
            ))

        plan_steps = [
            PlanStep(id="p1", description="Classify biomedical intent and extract search topic", status="completed", tool="NLP"),
            PlanStep(id="p2", description="Query public biomedical databases", status="completed", tool="PubMed/PubChem/PDB"),
            PlanStep(id="p3", description="Retrieve ranked literature context", status="completed", tool="RAG"),
            PlanStep(id="p4", description="Synthesize answer and expose UI artifacts", status="completed", tool="AI Orchestrator"),
        ]

        few_shot_examples = [
            FewShotExample(
                id="fs1",
                query="Find drugs for Alzheimer's disease",
                reasoning="Search multiple databases: PubMed, PDB, ChEMBL, NCBI",
                tools=["PubMed", "PDB", "ChEMBL", "NCBI", "RAG", "Groq"],
                outcome="Comprehensive drug discovery analysis"
            )
        ]

        response = MemoryResponse(
            memory_entries=memory_entries,
            plan_steps=plan_steps,
            few_shot_examples=few_shot_examples
        )

        return jsonify(model_to_dict(response))

    except Exception as e:
        logger.error(f"Memory endpoint error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to retrieve memory",
            code=500,
            details={"error": str(e)}
        ))), 500

# WebSocket support for real-time updates (placeholder for future implementation)
@api_bp.route('/ws/status', methods=['GET'])
@api_middleware()
def websocket_status():
    """WebSocket connection status (placeholder)"""
    return jsonify({
        "websocket_supported": False,
        "message": "WebSocket support coming soon for real-time updates"
    })

# Admin endpoints (protected)
@api_bp.route('/admin/stats', methods=['GET'])
@api_middleware()
def admin_stats():
    """Admin statistics endpoint"""
    # TODO: Add authentication check
    try:
        tool_stats = get_tool_stats()
        service_status = get_service_status()

        return jsonify({
            "tool_stats": tool_stats,
            "service_status": service_status,
            "timestamp": time.time()
        })

    except Exception as e:
        logger.error(f"Admin stats error: {e}", exc_info=True)
        return jsonify(model_to_dict(ErrorResponse(
            error="Failed to retrieve admin stats",
            code=500,
            details={"error": str(e)}
        ))), 500
