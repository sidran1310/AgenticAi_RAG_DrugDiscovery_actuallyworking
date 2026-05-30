"""
Service layer for the Drug Discovery AI Agent.
Provides business logic orchestration and data processing.
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from functools import wraps

from config import get_config, is_service_available
from models import (
    ChatRequest, ChatResponse, ThoughtProcess, Action, Observation, Metadata,
    RAGSearchRequest, RAGResponse, RAGChunk,
    CompoundsResponse, CompoundData,
    PapersResponse, PaperData,
    AgentType, ServiceStatus
)
from database import update_tool_stats, log_system_event

logger = logging.getLogger(__name__)


class AgentService:
    """Main agent orchestration service"""

    def __init__(self):
        self.config = get_config()
        self._load_dependencies()

    def _load_dependencies(self):
        """Load all required dependencies"""
        try:
            # Add modules to path
            import sys
            modules_path = os.path.join(os.path.dirname(__file__), '..', 'modules')
            if modules_path not in sys.path:
                sys.path.insert(0, modules_path)

            # Import core modules
            from main_agent import extract_topic_nlp
            from groq_api import initialize_groq, ask_groq
            from gemini_api import initialize_gemini, ask_gemini
            from pubmed_api import get_pubmed
            from pdb_api import search_pdb
            from pubchem_api import get_pubchem
            from ncbi_api import get_gene
            from rag_database import (
                create_vector_database,
                fetch_pubmed_abstracts,
                search_vector_database,
            )
            from langchain_agents import run_agent_by_type

            self.extract_topic_nlp = extract_topic_nlp
            self.initialize_groq = initialize_groq
            self.ask_groq = ask_groq
            self.initialize_gemini = initialize_gemini
            self.ask_gemini = ask_gemini
            self.get_pubmed = get_pubmed
            self.search_pdb = search_pdb
            self.get_pubchem = get_pubchem
            self.get_gene = get_gene
            self.create_vector_database = create_vector_database
            self.fetch_pubmed_abstracts = fetch_pubmed_abstracts
            self.search_vector_database = search_vector_database
            self.run_agent_by_type = run_agent_by_type

            # Initialize clients
            self.groq_client = None
            self.gemini_client = None

            if self.config.api.groq_api_key:
                self.groq_client = self.initialize_groq(self.config.api.groq_api_key)

            if self.config.api.gemini_api_key:
                self.gemini_client = self.initialize_gemini(self.config.api.gemini_api_key)

            logger.info("AgentService dependencies loaded successfully")

        except Exception as e:
            logger.error(f"Failed to load AgentService dependencies: {e}")
            raise

    def classify_query(self, query: str) -> Dict[str, Any]:
        """Classify query into categories to prevent wrong outputs"""
        query_lower = query.lower()
        
        # Disease-related keywords
        disease_keywords = ['alzheimer', 'cancer', 'diabetes', 'parkinson', 'tb', 'tuberculosis', 'hiv', 'covid', 'flu', 'infection']
        drug_keywords = ['inhibitor', 'drug', 'compound', 'molecule', 'treatment', 'therapy', 'medicine']
        molecular_keywords = ['protein', 'gene', 'dna', 'rna', 'enzyme', 'receptor', 'kinase', 'pdb', 'structure']
        paper_keywords = ['paper', 'study', 'research', 'publication', 'review', 'clinical trial', 'phase']
        
        categories = {
            'disease': any(kw in query_lower for kw in disease_keywords),
            'drug': any(kw in query_lower for kw in drug_keywords),
            'molecular': any(kw in query_lower for kw in molecular_keywords),
            'papers': any(kw in query_lower for kw in paper_keywords),
        }
        
        # Default to drug discovery if no specific category
        if not any(categories.values()):
            categories['drug'] = True
            
        return categories

    def candidate_terms_for_query(self, query: str, topic: str, categories: Dict[str, Any]) -> List[str]:
        """Choose biologically plausible compound/search terms for the query."""
        query_lower = query.lower()
        if "bace1" in query_lower or "bace-1" in query_lower or "beta-secretase" in query_lower:
            return ["verubecestat", "lanabecestat", "atabecestat"]

        disease_candidates = {
            "alzheimer": ["lecanemab", "donanemab", "aducanumab"],
            "parkinson": ["levodopa", "rasagiline", "pramipexole"],
            "diabetes": ["metformin", "semaglutide", "empagliflozin"],
            "cancer": ["imatinib", "pembrolizumab", "paclitaxel"],
            "tuberculosis": ["isoniazid", "rifampicin", "ethambutol"],
            "tb": ["isoniazid", "rifampicin", "ethambutol"],
            "hiv": ["dolutegravir", "tenofovir", "lamivudine"],
            "covid": ["nirmatrelvir", "remdesivir"],
        }

        for disease, candidates in disease_candidates.items():
            if disease in query_lower:
                return candidates

        if categories["drug"]:
            return [topic]

        return []

    def format_molecule(self, compound_data: Dict[str, Any], indication: str, rank: int = 0) -> Dict[str, Any]:
        """Normalize PubChem output for the molecule viewer."""
        name = compound_data.get("compound") or compound_data.get("name") or indication
        mw = compound_data.get("molecular_weight") or compound_data.get("weight") or 0
        logp = compound_data.get("logp") or 0
        tpsa = compound_data.get("tpsa") or 0
        hbd = compound_data.get("hbd") or 0
        hba = compound_data.get("hba") or 0
        rotatable_bonds = compound_data.get("rotatable_bonds") or 0
        lipinski_pass = bool(compound_data.get("lipinski_pass"))

        return {
            "id": f"{name.lower().replace(' ', '-')[:32]}-{rank + 1}",
            "name": name,
            "chemblId": "Not assigned",
            "smiles": compound_data.get("smiles", "N/A"),
            "formula": compound_data.get("formula", "Unknown"),
            "molecularWeight": mw,
            "molecular_weight": mw,
            "logP": logp,
            "logp": logp,
            "tpsa": tpsa,
            "hbd": hbd,
            "hba": hba,
            "rotBonds": rotatable_bonds,
            "rotatable_bonds": rotatable_bonds,
            "drugClass": "Candidate compound",
            "relevance": max(68, 94 - rank * 6),
            "indication": indication,
            "mechanism": "Mechanism requires literature confirmation",
            "phase": "Research",
            "props": {
                "mw": mw,
                "logP": logp,
                "hbd": hbd,
                "hba": hba,
                "tpsa": tpsa,
                "rotBonds": rotatable_bonds,
            },
            "dock": {
                "target": "Target structure pending",
                "score": None,
                "pose": "Not docked",
                "rmsd": None,
            },
            "admet": {
                "solubility": "Needs assay",
                "permeability": "Needs assay",
                "cyp3a4": "Unknown",
                "herg": "Unknown",
                "hepatotox": "Unknown",
                "bbb": "Unknown",
            },
            "lipinski": {
                "passes": lipinski_pass,
                "violations": 0 if lipinski_pass else 1,
            },
            "lipinskiPass": lipinski_pass,
            "source": "PubChem",
        }

    def format_rag_result(self, item: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Normalize RAG search output for the frontend explorer."""
        content = item.get("abstract") or item.get("content") or item.get("text") or ""
        score = item.get("similarity_score") or item.get("score") or item.get("confidence") or 0.75
        year = str(item.get("publication_date", ""))[:4]
        try:
            year_value = int(year)
        except ValueError:
            year_value = datetime.now().year

        return {
            "id": f"rag-{index + 1}",
            "title": item.get("title", f"Retrieved source {index + 1}"),
            "content": content,
            "source": item.get("url") or item.get("source") or "PubMed",
            "score": round(float(score), 3),
            "confidence": round(float(score), 3),
            "meta": {
                "year": year_value,
                "disease": "Query-specific",
                "docType": "PubMed Abstract",
                "doi": item.get("doi"),
            },
            "keywords": [word.strip(".,;:").lower() for word in content.split()[:8] if len(word.strip(".,;:")) > 4][:5],
            "metadata": {
                "pubmed_id": item.get("pubmed_id"),
                "journal": item.get("journal"),
                "authors": item.get("authors"),
            },
        }

    def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        """Process a chat request and return structured response"""
        start_time = time.time()
        thought_process = []
        actions = []
        observations = []
        
        try:
            # Step 1: Classify query
            categories = self.classify_query(request.message)
            thought_process.append(ThoughtProcess(
                step=1,
                content=f"Classified query: {', '.join([k for k,v in categories.items() if v])}",
                timestamp=datetime.now()
            ))

            # Step 2: Extract topic from user message
            topic = self.extract_topic_nlp(request.message)
            thought_process.append(ThoughtProcess(
                step=2,
                content=f"Extracted topic: '{topic}'",
                timestamp=datetime.now()
            ))

            # Initialize results
            molecules = []
            papers_graph = {}
            rag_results = []
            tools_used = []
            pubmed_ids = []
            pdb_ids = []
            compound_data_for_llm = None

            # Step 3: Search PubChem for compounds only when a plausible compound term exists
            candidate_terms = self.candidate_terms_for_query(request.message, topic, categories)
            for rank, term in enumerate(candidate_terms[:3]):
                pubchem_result = self.get_pubchem(term)
                if pubchem_result:
                    compound_data_for_llm = compound_data_for_llm or pubchem_result
                    molecules.append(self.format_molecule(pubchem_result, request.message, rank))
            tools_used.append({
                'tool': 'PubChem',
                'status': 'success' if molecules else 'idle',
                'time': 1.2,
                'result': f"Found {len(molecules)} candidate molecule(s)"
            })
            actions.append(Action(
                tool="PubChem",
                input=", ".join(candidate_terms) if candidate_terms else topic,
                result=f"Found {len(molecules)} candidate molecule(s)",
                duration=1.2,
                success=True
            ))
            if molecules:
                observations.append(Observation(
                    content=f"Found {len(molecules)} PubChem-backed candidate molecule(s)",
                    confidence=0.85,
                    source="PubChem"
                ))

            # Step 4: Search PDB for structures
            if categories['molecular']:
                pdb_ids = self.search_pdb(topic)
                if pdb_ids:
                    tools_used.append({'tool': 'PDB', 'status': 'success', 'time': 0.8})
                    actions.append(Action(
                        tool="PDB",
                        input=topic,
                        result=f"Found {len(pdb_ids)} PDB structures",
                        duration=0.8,
                        success=True
                    ))
                    observations.append(Observation(
                        content=f"Found {len(pdb_ids)} PDB structures",
                        confidence=0.85,
                        source="PDB"
                    ))

            # Step 5: Search PubMed for papers
            if categories['papers'] or categories['disease']:
                pubmed_ids = self.get_pubmed(request.message, max_results=8)
                if pubmed_ids:
                    tools_used.append({'tool': 'PubMed', 'status': 'success', 'time': 1.5})
                    actions.append(Action(
                        tool="PubMed",
                        input=request.message,
                        result=f"Found {len(pubmed_ids)} PubMed paper(s)",
                        duration=1.5,
                        success=True
                    ))
                    observations.append(Observation(
                        content=f"Found {len(pubmed_ids)} relevant PubMed paper(s)",
                        confidence=0.85,
                        source="PubMed"
                    ))
                    papers_graph = {
                        'nodes': [
                            {
                                'id': f'pmid-{pid}',
                                'title': f'PubMed {pid}',
                                'year': datetime.now().year,
                                'pubmedId': pid,
                                'url': f'https://pubmed.ncbi.nlm.nih.gov/{pid}/'
                            }
                            for pid in pubmed_ids[:6]
                        ],
                        'edges': []
                    }

            # Step 6: Search RAG database
            if pubmed_ids:
                abstracts = self.fetch_pubmed_abstracts(pubmed_ids[:6])
                if abstracts:
                    self.create_vector_database(pubmed_ids[:6])
            rag_result = self.search_vector_database(request.message, n_results=5)
            if rag_result:
                tools_used.append({'tool': 'RAG', 'status': 'success', 'time': 0.5})
                actions.append(Action(
                    tool="RAG",
                    input=request.message,
                    result=f"Retrieved {len(rag_result)} relevant knowledge item(s)",
                    duration=0.5,
                    success=True
                ))
                if isinstance(rag_result, list):
                    rag_results = [self.format_rag_result(item, i) for i, item in enumerate(rag_result[:5])]
                else:
                    rag_results = [{'id': 'rag-1', 'content': str(rag_result), 'score': 0.75, 'confidence': 0.75, 'source': 'RAG', 'meta': {'year': datetime.now().year, 'disease': 'Query-specific', 'docType': 'Knowledge Base'}, 'keywords': []}]
                observations.append(Observation(
                    content=f"Retrieved {len(rag_results)} relevant knowledge base items",
                    confidence=0.85,
                    source="RAG"
                ))

            # Step 7: Generate AI response
            context = f"""
Topic: {topic}
Query: {request.message}
Categories: {categories}
            Candidate Molecules Found: {len(molecules)}
            Papers Found: {len(papers_graph.get('nodes', []))}
            RAG Results: {len(rag_results)}
            """

            ai_response = None
            if self.groq_client:
                ai_response = self.ask_groq(
                    self.groq_client,
                    context,
                    request.message,
                    compound_data=compound_data_for_llm,
                    pdb_ids=pdb_ids[:3],
                )
            elif self.gemini_client:
                ai_response = self.ask_gemini(self.gemini_client, context, request.message)
            
            if not ai_response:
                ai_response = f"Query Analysis - Topic: {topic}. Please see the search results and recommendations above."

            actions.append(Action(
                tool="AI Generation",
                input=request.message,
                result=ai_response[:200],
                duration=0.5,
                success=True
            ))

            # Create response with all data
            processing_time = time.time() - start_time
            response = ChatResponse(
                chat=ai_response,
                response=ai_response,
                thought_process=thought_process,
                actions=actions,
                observations=observations,
                metadata=Metadata(
                    topic=topic,
                    pubmed_count=len(pubmed_ids),
                    pubmed_ids=pubmed_ids[:8],
                    pdb_count=len(pdb_ids),
                    pdb_ids=pdb_ids[:5],
                    compound=compound_data_for_llm,
                    rag_sources=len(rag_results),
                    timestamp=datetime.now().isoformat(),
                    session_id=request.session_id or "default",
                    processing_time=processing_time
                ),
                status="success",
                molecules=molecules,
                papers_graph=papers_graph,
                rag_results=rag_results,
                tools=tools_used,
                tools_used=tools_used
            )

            return response

        except Exception as e:
            logger.error(f"Error processing chat request: {e}", exc_info=True)
            processing_time = time.time() - start_time
            return ChatResponse(
                chat="I apologize, but I encountered an error while processing your request. Please try again.",
                response="I apologize, but I encountered an error while processing your request. Please try again.",
                thought_process=thought_process,
                actions=actions,
                observations=[Observation(content=f"Error: {str(e)}", confidence=0.0)] if not observations else observations,
                metadata=Metadata(
                    topic="error",
                    pubmed_count=0,
                    pdb_count=0,
                    timestamp=datetime.now().isoformat(),
                    session_id=request.session_id or "default",
                    processing_time=processing_time
                ),
                status="error",
                molecules=[],
                papers_graph={"nodes": [], "edges": []},
                rag_results=[],
                tools=[],
                tools_used=[]
            )


# Placeholder services (to be implemented)
class RAGService:
    """RAG database service"""
    def search_rag(self, request: RAGSearchRequest) -> RAGResponse:
        try:
            from rag_database import search_vector_database

            results = search_vector_database(request.query, n_results=request.limit)
            chunks = []
            for index, item in enumerate(results):
                content = item.get("abstract") or item.get("content") or ""
                score = float(item.get("similarity_score") or 0.75)
                chunks.append(RAGChunk(
                    id=f"rag-{index + 1}",
                    source=item.get("url") or "PubMed",
                    title=item.get("title") or f"Retrieved source {index + 1}",
                    content=content,
                    relevance_score=max(0.0, min(1.0, score)),
                    chunk_index=index + 1,
                    total_chunks=max(1, len(results)),
                    metadata={
                        "database": "ChromaDB",
                        "date": item.get("publication_date") or datetime.now().strftime("%Y-%m-%d"),
                        "pubmed_id": item.get("pubmed_id"),
                        "journal": item.get("journal"),
                    }
                ))
            return RAGResponse(chunks=chunks, total=len(chunks), query=request.query)
        except Exception as e:
            logger.error(f"RAG search failed: {e}", exc_info=True)
            return RAGResponse(chunks=[], total=0, query=request.query)


class CompoundService:
    """Compound data service"""
    def search_compounds(self, query: str, limit: int = 10) -> CompoundsResponse:
        try:
            from pubchem_api import get_pubchem

            result = get_pubchem(query)
            compounds = []
            if result:
                compounds.append(CompoundData(
                    id=str(result.get("cid", query.lower().replace(" ", "-")))[:32],
                    name=result.get("name", query),
                    chembl_id=None,
                    smiles=result.get("smiles"),
                    molecular_weight=result.get("molecular_weight", 0.0),
                    logp=result.get("logp"),
                    tpsa=result.get("tpsa", 0.0),
                    hbd=result.get("hbd", 0),
                    hba=result.get("hba", 0),
                    rotatable_bonds=result.get("rotatable_bonds", 0),
                    phase="Research",
                    indication=query,
                    mechanism="Mechanism requires literature confirmation",
                    lipinski_pass=result.get("lipinski_pass", False),
                ))
            return CompoundsResponse(compounds=compounds, total=len(compounds), query=query)
        except Exception as e:
            logger.error(f"Compound search failed: {e}", exc_info=True)
            return CompoundsResponse(compounds=[], total=0, query=query)


class PaperService:
    """Paper data service"""
    def search_papers(self, query: str, limit: int = 10) -> PapersResponse:
        try:
            from pubmed_api import get_pubmed
            from rag_database import fetch_pubmed_abstracts

            pubmed_ids = get_pubmed(query, max_results=limit)
            abstracts = fetch_pubmed_abstracts(pubmed_ids)
            papers = []
            for index, item in enumerate(abstracts):
                papers.append(PaperData(
                    id=item.get("id", f"paper-{index + 1}"),
                    title=item.get("title", f"Paper {index + 1}"),
                    authors=", ".join(item.get("authors", [])) if isinstance(item.get("authors"), list) else item.get("authors", "Unknown authors"),
                    journal=item.get("journal", "Unknown journal"),
                    date=item.get("publication_date", "Unknown"),
                    abstract=item.get("abstract", "Abstract not available"),
                    ai_summary=(item.get("abstract", "")[:240] + "...") if len(item.get("abstract", "")) > 240 else item.get("abstract", "Summary unavailable"),
                    source="PubMed",
                    credibility_score=max(70, 96 - index * 3),
                    citation_count=0,
                    tags=[query.lower(), "pubmed", "biomedical"],
                    pubmed_id=item.get("id"),
                ))
            return PapersResponse(papers=papers, total=len(papers), query=query)
        except Exception as e:
            logger.error(f"Paper search failed: {e}", exc_info=True)
            return PapersResponse(papers=[], total=0, query=query)


# Initialize service instances
agent_service = AgentService()
rag_service = RAGService()
paper_service = PaperService()
compound_service = CompoundService()
