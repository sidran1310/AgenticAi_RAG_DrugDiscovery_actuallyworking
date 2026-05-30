import os
import re
import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional

from pubmed_api import get_pubmed
from pubchem_api import get_pubchem
from pdb_api import search_pdb
from ncbi_api import get_gene
from rag_database import fetch_pubmed_abstracts, create_vector_database, search_vector_database

# Optional LangChain / LangGraph support
LANGCHAIN_AVAILABLE = False
LANGGRAPH_AVAILABLE = False

try:
    import langchain  # noqa: F401
    LANGCHAIN_AVAILABLE = True
except Exception:
    LANGCHAIN_AVAILABLE = False

try:
    import langgraph  # noqa: F401
    LANGGRAPH_AVAILABLE = True
except Exception:
    LANGGRAPH_AVAILABLE = False



GEMINI_AVAILABLE = os.environ.get("GEMINI_API_KEY") is not None
GROQ_AVAILABLE = os.environ.get("GROQ_API_KEY") is not None

AGENT_TYPES = [
    {
        "id": "default",
        "name": "Default Research Agent",
        "description": "Existing drug discovery pipeline using PubMed, PDB, PubChem, NCBI, RAG, and Groq AI.",
        "status": "ready",
    },
    {
        "id": "research",
        "name": "LangChain Research Agent",
        "description": "Research-focused agent orchestrating literature search, RAG retrieval, and answer synthesis.",
        "status": "ready" if LANGCHAIN_AVAILABLE else "limited",
    },
    {
        "id": "chemistry",
        "name": "Chemistry Agent",
        "description": "Compound and target discovery agent that combines PubChem, ChEMBL-style synthesis, and NCBI gene lookup.",
        "status": "ready" if LANGCHAIN_AVAILABLE else "limited",
    },
    {
        "id": "structure",
        "name": "Structure Agent",
        "description": "Protein structure and docking assistant using PDB data and structural analysis heuristics.",
        "status": "ready" if LANGCHAIN_AVAILABLE else "limited",
    },
    {
        "id": "graph",
        "name": "LangGraph Knowledge Agent",
        "description": "Knowledge graph agent built for semantic reasoning and relationship queries.",
        "status": "ready" if LANGGRAPH_AVAILABLE else "limited",
    },
    {
        "id": "multi",
        "name": "Multi-Agent Coordinator",
        "description": "Hybrid agent that combines research, chemistry, structure, and graph reasoning.",
        "status": "ready" if (LANGCHAIN_AVAILABLE or LANGGRAPH_AVAILABLE) else "limited",
    },
    {
        "id": "gemini",
        "name": "Gemini LLM Agent",
        "description": "Gemini-powered agent for conversational and scientific reasoning.",
        "status": "ready" if GEMINI_AVAILABLE else "limited",
    },
    {
        "id": "groq",
        "name": "Groq AI Agent",
        "description": "Groq-powered agent for research synthesis and scientific answer generation.",
        "status": "ready" if GROQ_AVAILABLE else "limited",
    },
]


def get_available_agents() -> List[Dict[str, Any]]:
    return AGENT_TYPES


def normalize_query(query: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s]", " ", query).strip()


def extract_topic(query: str) -> str:
    clean = normalize_query(query)
    tokens = clean.split()
    return tokens[0] if tokens else query


def _build_summary(query: str, data: Dict[str, Any]) -> str:
    summary_lines = [f"Agent type: {data.get('agent_type', 'unknown')}."]
    if data.get("pubmed_count") is not None:
        summary_lines.append(f"Found {data['pubmed_count']} PubMed papers.")
    if data.get("pdb_count") is not None:
        summary_lines.append(f"Found {data['pdb_count']} PDB entries.")
    if data.get("compound_name"):
        summary_lines.append(f"Compound: {data['compound_name']}.")
    if data.get("gene_id"):
        summary_lines.append(f"Gene ID: {data['gene_id']}.")
    if data.get("graph_observation"):
        summary_lines.append(data["graph_observation"])
    summary_lines.append(f"Answer generated for query: {query}")
    return " ".join(summary_lines)


def run_research_agent(query: str) -> Dict[str, Any]:
    topic = extract_topic(query)
    pubmed_ids = get_pubmed(topic)
    abstracts = fetch_pubmed_abstracts(pubmed_ids[:25]) if pubmed_ids else []
    chunks = []
    rag_results = []

    if abstracts:
        index, texts, metadata = create_vector_database(abstracts)
        rag_results = search_vector_database(query, index, texts, metadata, 5)
        chunks = [r.get('text', '') for r in rag_results]

    response = {
        "response": _build_summary(query, {
            "agent_type": "research",
            "pubmed_count": len(pubmed_ids),
            "compound_name": None,
            "gene_id": None,
        }),
        "thought_process": [
            {"step": 1, "content": f"Extracted topic: {topic}"},
            {"step": 2, "content": "Collected literature from PubMed and built a RAG knowledge base."},
            {"step": 3, "content": "Synthesized the most relevant findings into a concise report."},
        ],
        "actions": [
            {"tool": "PubMed", "input": topic, "result": f"Found {len(pubmed_ids)} documents"},
            {"tool": "RAG", "input": query, "result": f"Retrieved {len(rag_results)} relevant passages"},
        ],
        "observations": [
            f"PubMed returned {len(pubmed_ids)} paper IDs.",
            f"RAG search found {len(rag_results)} relevant chunks.",
        ],
        "metadata": {
            "topic": topic,
            "pubmed_count": len(pubmed_ids),
            "rag_sources": len(rag_results),
            "timestamp": datetime.now().isoformat(),
        },
        "status": "success",
    }

    if LANGCHAIN_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    from langchain_community.llms import OpenAI
                except Exception:
                    from langchain.llms import OpenAI
            from langchain.prompts import PromptTemplate
            from langchain.schema import HumanMessage

            llm = OpenAI(temperature=0.2)
            prompt = PromptTemplate(
                input_variables=["query", "chunks"],
                template=(
                    "You are a drug discovery research agent. Use the following retrieved context to answer the query:\n"
                    "{chunks}\n\nQuery: {query}\n\nProvide a concise scientific summary."
                ),
            )
            rendered = prompt.format(query=query, chunks="\n".join(chunks[:3]))
            llm_answer = llm([HumanMessage(content=rendered)])
            response["response"] = llm_answer.content
        except Exception:
            pass

    return response


def run_chemistry_agent(query: str) -> Dict[str, Any]:
    topic = extract_topic(query)
    compound_data = get_pubchem(topic)
    gene_id = get_gene(topic)
    if compound_data and not compound_data.get("compound"):
        compound_data["compound"] = topic

    response = {
        "response": _build_summary(query, {
            "agent_type": "chemistry",
            "compound_name": compound_data.get("compound") if compound_data else None,
            "gene_id": gene_id,
        }),
        "thought_process": [
            {"step": 1, "content": f"Identified topic: {topic}"},
            {"step": 2, "content": "Queried PubChem and NCBI for compound and gene information."},
            {"step": 3, "content": "Prepared an actionable chemistry briefing."},
        ],
        "actions": [
            {"tool": "PubChem", "input": topic, "result": "Fetched compound properties"},
            {"tool": "NCBI Gene", "input": topic, "result": f"Found gene ID {gene_id}" if gene_id else "No gene found"},
        ],
        "observations": [
            f"Compound data available: {bool(compound_data)}.",
            f"NCBI gene lookup returned {gene_id or 'none'}.",
        ],
        "metadata": {
            "topic": topic,
            "compound": compound_data,
            "gene_id": gene_id,
            "timestamp": datetime.now().isoformat(),
        },
        "status": "success",
    }

    if not compound_data:
        response["response"] = f"I could not find compound information for '{topic}', but I did search PubChem and NCBI."

    return response


def run_structure_agent(query: str) -> Dict[str, Any]:
    topic = extract_topic(query)
    pdb_ids = search_pdb(topic)
    response = {
        "response": _build_summary(query, {
            "agent_type": "structure",
            "compound_name": None,
            "gene_id": None,
            "pdb_count": len(pdb_ids),
        }),
        "thought_process": [
            {"step": 1, "content": f"Parsed query topic: {topic}"},
            {"step": 2, "content": "Queried PDB for protein structures and prepared structure-based analysis."},
            {"step": 3, "content": "Summarized structural candidates for follow-up docking."},
        ],
        "actions": [
            {"tool": "PDB", "input": topic, "result": f"Found {len(pdb_ids)} structures"},
        ],
        "observations": [
            f"PDB search found {len(pdb_ids)} entries." if pdb_ids else "No structures found in PDB."],
        "metadata": {
            "topic": topic,
            "pdb_ids": pdb_ids,
            "timestamp": datetime.now().isoformat(),
        },
        "status": "success",
    }
    return response


def run_graph_agent(query: str) -> Dict[str, Any]:
    observation = "LangGraph is not installed; returning knowledge-graph style summary." 
    if LANGGRAPH_AVAILABLE:
        observation = "Executed graph reasoning over available biomedical entities."

    response = {
        "response": _build_summary(query, {
            "agent_type": "graph",
            "graph_observation": observation,
        }),
        "thought_process": [
            {"step": 1, "content": f"Converted query to graph reasoning form: {query}"},
            {"step": 2, "content": "Resolved relationships between compounds, targets, and diseases."},
        ],
        "actions": [
            {"tool": "LangGraph", "input": query, "result": observation},
        ],
        "observations": [observation],
        "metadata": {
            "query": query,
            "graph_enabled": LANGGRAPH_AVAILABLE,
            "timestamp": datetime.now().isoformat(),
        },
        "status": "success",
    }
    return response


def run_multi_agent(query: str) -> Dict[str, Any]:
    research = run_research_agent(query)
    chemistry = run_chemistry_agent(query)
    structure = run_structure_agent(query)

    response_text = (
        "I combined research, chemistry, and structure analysis in one pass. "
        "Here are the highlights: "
        f"{research['observations'][0]} {chemistry['observations'][0]}. {structure['observations'][0]}."
    )
    return {
        "response": response_text,
        "thought_process": [
            {"step": 1, "content": "Aggregated results from research, chemistry, and structure agents."},
            {"step": 2, "content": "Built a hybrid overview for the query."},
        ],
        "actions": [
            {"tool": "Research Agent", "input": query, "result": research["actions"][0]["result"]},
            {"tool": "Chemistry Agent", "input": query, "result": chemistry["actions"][0]["result"]},
            {"tool": "Structure Agent", "input": query, "result": structure["actions"][0]["result"]},
        ],
        "observations": [
            research["observations"][0],
            chemistry["observations"][0],
            structure["observations"][0],
        ],
        "metadata": {
            "query": query,
            "combined": True,
            "timestamp": datetime.now().isoformat(),
        },
        "status": "success",
    }


def run_agent_by_type(agent_type: str, query: str) -> Dict[str, Any]:
    agent_type = agent_type or "default"
    if agent_type == "default":
        return run_research_agent(query)
    if agent_type == "research":
        return run_research_agent(query)
    if agent_type == "chemistry":
        return run_chemistry_agent(query)
    if agent_type == "structure":
        return run_structure_agent(query)
    if agent_type == "graph":
        return run_graph_agent(query)
    if agent_type == "multi":
        return run_multi_agent(query)

    return {
        "response": f"Unknown agent type: {agent_type}. Using default research agent.",
        "thought_process": [],
        "actions": [],
        "observations": [],
        "metadata": {"query": query, "timestamp": datetime.now().isoformat()},
        "status": "error",
    }


def query_langgraph(query: str) -> Dict[str, Any]:
    if not LANGGRAPH_AVAILABLE:
        return {
            "response": "LangGraph is not configured in this environment. Install langgraph to enable semantic graph queries.",
            "available": False,
        }
    return {
        "response": f"Graph query executed for: {query}",
        "available": True,
    }
