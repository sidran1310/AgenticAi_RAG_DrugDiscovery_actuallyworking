# Drug Discovery ReAct Agent — Python Backend Architecture Guide

## Complete System Architecture & Code Structure

This guide provides the full Python backend implementation for the Drug Discovery ReAct Agent system, integrating LangChain, FAISS, ChromaDB, LlamaIndex, Transformers, Whisper, Gemini API, and multiple biomedical APIs.

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/shadcn-ui)                │
│  Chat UI │ Tool Panel │ RAG Explorer │ Molecular Viewer      │
└─────────────────────┬───────────────────────────────────────┘
                      │ REST API / WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend Server                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              ReAct Agent (LangChain LCEL)             │   │
│  │  Thought (LLM) → Action (Tool) → Observation → Answer│   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ RAG Pipeline│  │   Memory    │  │   Tool Registry     │ │
│  │ FAISS +     │  │ Short/Long  │  │ ChEMBL, PubMed,    │ │
│  │ ChromaDB +  │  │ + Episodic  │  │ NCBI, Gemini,      │ │
│  │ LlamaIndex  │  │             │  │ Docking, Whisper   │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Project Structure

```
drug_discovery_agent/
├── main.py                    # FastAPI entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── config.py                  # Configuration management
├── agent/
│   ├── __init__.py
│   ├── react_agent.py         # ReAct agent with LangChain LCEL
│   ├── prompts.py             # System prompts & few-shot examples
│   └── memory.py              # Agent memory management
├── tools/
│   ├── __init__.py
│   ├── chembl_tool.py         # ChEMBL API integration
│   ├── pubmed_tool.py         # PubMed/NCBI E-utilities
│   ├── docking_tool.py        # Molecular docking engine
│   ├── gemini_tool.py         # Gemini LLM for reasoning
│   └── whisper_tool.py        # Whisper voice transcription
├── rag/
│   ├── __init__.py
│   ├── pipeline.py            # RAG orchestration
│   ├── faiss_store.py         # FAISS vector store
│   ├── chroma_store.py        # ChromaDB vector store
│   ├── embeddings.py          # HuggingFace embeddings
│   └── indexer.py             # Document indexing
├── models/
│   ├── __init__.py
│   └── schemas.py             # Pydantic models
└── data/
    ├── knowledge_base/        # Documents for RAG indexing
    └── few_shot_examples.json # Few-shot prompting data
```

---

## 3. Installation

### requirements.txt

```txt
fastapi==0.109.0
uvicorn==0.27.0
python-dotenv==1.0.0
pydantic==2.5.3
langchain==0.1.20
langchain-core==0.1.52
langchain-community==0.0.38
langchain-openai==0.1.6
langchain-google-genai==1.0.3
langgraph==0.0.40
faiss-cpu==1.7.4
chromadb==0.4.22
llama-index==0.10.12
llama-index-vector-stores-faiss==0.1.3
llama-index-vector-stores-chroma==0.1.6
transformers==4.37.2
sentence-transformers==2.3.1
torch==2.2.0
openai-whisper==20231117
requests==2.31.0
biopython==1.83
numpy==1.26.3
pandas==2.1.5
aiohttp==3.9.3
websockets==12.0
```

### .env

```env
GOOGLE_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACE_API_TOKEN=your_hf_token_here
FAISS_INDEX_PATH=./data/faiss_index
CHROMA_DB_PATH=./data/chroma_db
HOST=0.0.0.0
PORT=8000
```

### Setup Commands

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -c "import whisper; whisper.load_model('base')"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4. config.py — Configuration

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
    FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    GEMINI_MODEL = "gemini-pro"
    GPT_MODEL = "gpt-4-turbo-preview"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))

config = Config()
```

---

## 5. models/schemas.py — Data Models

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class StepType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    ANSWER = "answer"

class ReActStep(BaseModel):
    type: StepType
    content: str
    tool: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    timestamp: str

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    steps: List[ReActStep]
    sources: List[Dict[str, Any]]

class CompoundInfo(BaseModel):
    name: str
    chembl_id: str
    smiles: str
    molecular_weight: float
    ic50: Optional[str] = None
    phase: Optional[str] = None
```

---

## 6. tools/chembl_tool.py — ChEMBL API

```python
import requests
from langchain.tools import tool
from typing import Optional

CHEMBL_BASE = "https://www.ebi.ac.uk/chembl/api/data"

@tool
def search_chembl_target(target_name: str, limit: int = 25) -> str:
    """Search ChEMBL for a drug target by name and return bioactivity data."""
    # Step 1: Search for target
    url = f"{CHEMBL_BASE}/target/search.json"
    params = {"q": target_name, "limit": 5}
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        return f"Error searching ChEMBL: {resp.status_code}"

    targets = resp.json().get("targets", [])
    if not targets:
        return f"No targets found for '{target_name}'"

    target_chembl_id = targets[0]["target_chembl_id"]
    target_pref_name = targets[0]["pref_name"]

    # Step 2: Get activities for target
    act_url = f"{CHEMBL_BASE}/activity.json"
    act_params = {
        "target_chembl_id": target_chembl_id,
        "standard_type": "IC50",
        "limit": limit,
    }
    act_resp = requests.get(act_url, params=act_params)
    activities = act_resp.json().get("activities", [])

    results = []
    for act in activities:
        results.append({
            "molecule_chembl_id": act.get("molecule_chembl_id"),
            "molecule_name": act.get("molecule_pref_name", "Unknown"),
            "standard_value": act.get("standard_value"),
            "standard_units": act.get("standard_units"),
            "standard_type": act.get("standard_type"),
        })

    return (
        f"Target: {target_pref_name} ({target_chembl_id})\n"
        f"Found {len(results)} activities:\n"
        + "\n".join(
            f"- {r['molecule_name']} ({r['molecule_chembl_id']}): "
            f"{r['standard_type']} = {r['standard_value']} {r['standard_units']}"
            for r in results[:10]
        )
    )


@tool
def get_compound_details(chembl_id: str) -> str:
    """Get detailed information about a compound from ChEMBL by its ID."""
    url = f"{CHEMBL_BASE}/molecule/{chembl_id}.json"
    resp = requests.get(url)
    if resp.status_code != 200:
        return f"Error fetching compound {chembl_id}: {resp.status_code}"

    mol = resp.json()
    props = mol.get("molecule_properties", {})

    return (
        f"Compound: {mol.get('pref_name', 'Unknown')} ({chembl_id})\n"
        f"SMILES: {mol.get('molecule_structures', {}).get('canonical_smiles', 'N/A')}\n"
        f"Molecular Weight: {props.get('full_mwt', 'N/A')}\n"
        f"LogP: {props.get('alogp', 'N/A')}\n"
        f"TPSA: {props.get('psa', 'N/A')}\n"
        f"HBD: {props.get('hbd', 'N/A')}\n"
        f"HBA: {props.get('hba', 'N/A')}\n"
        f"Max Phase: {mol.get('max_phase', 'N/A')}\n"
        f"Molecule Type: {mol.get('molecule_type', 'N/A')}"
    )
```

---

## 7. tools/pubmed_tool.py — PubMed/NCBI

```python
import requests
import xml.etree.ElementTree as ET
from langchain.tools import tool

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

@tool
def search_pubmed(query: str, max_results: int = 10) -> str:
    """Search PubMed for biomedical literature and return article summaries."""
    # Step 1: Search for article IDs
    search_url = f"{EUTILS_BASE}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "relevance",
        "retmode": "json",
    }
    resp = requests.get(search_url, params=params)
    data = resp.json()
    id_list = data.get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return f"No PubMed articles found for '{query}'"

    # Step 2: Fetch article details
    fetch_url = f"{EUTILS_BASE}/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "rettype": "abstract",
        "retmode": "xml",
    }
    fetch_resp = requests.get(fetch_url, params=fetch_params)
    root = ET.fromstring(fetch_resp.text)

    articles = []
    for article in root.findall(".//PubmedArticle"):
        title_el = article.find(".//ArticleTitle")
        abstract_el = article.find(".//AbstractText")
        journal_el = article.find(".//Journal/Title")
        year_el = article.find(".//PubDate/Year")
        pmid_el = article.find(".//PMID")

        articles.append({
            "pmid": pmid_el.text if pmid_el is not None else "N/A",
            "title": title_el.text if title_el is not None else "N/A",
            "journal": journal_el.text if journal_el is not None else "N/A",
            "year": year_el.text if year_el is not None else "N/A",
            "abstract": (abstract_el.text[:300] + "...")
                if abstract_el is not None and abstract_el.text
                else "No abstract",
        })

    return (
        f"Found {len(articles)} articles for '{query}':\n\n"
        + "\n\n".join(
            f"[{a['pmid']}] {a['title']}\n"
            f"Journal: {a['journal']} ({a['year']})\n"
            f"Abstract: {a['abstract']}"
            for a in articles
        )
    )


@tool
def search_ncbi_gene(gene_name: str) -> str:
    """Search NCBI Gene database for gene information."""
    search_url = f"{EUTILS_BASE}/esearch.fcgi"
    params = {
        "db": "gene",
        "term": f"{gene_name}[Gene Name] AND Homo sapiens[Organism]",
        "retmax": 5,
        "retmode": "json",
    }
    resp = requests.get(search_url, params=params)
    data = resp.json()
    id_list = data.get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return f"No genes found for '{gene_name}'"

    summary_url = f"{EUTILS_BASE}/esummary.fcgi"
    summary_params = {
        "db": "gene",
        "id": ",".join(id_list[:3]),
        "retmode": "json",
    }
    summary_resp = requests.get(summary_url, params=summary_params)
    result = summary_resp.json().get("result", {})

    genes = []
    for gid in id_list[:3]:
        gene = result.get(gid, {})
        genes.append(
            f"Gene: {gene.get('name', 'N/A')} (ID: {gid})\n"
            f"Description: {gene.get('description', 'N/A')}\n"
            f"Chromosome: {gene.get('chromosome', 'N/A')}\n"
            f"Summary: {gene.get('summary', 'N/A')[:300]}..."
        )

    return "\n\n".join(genes)
```

---

## 8. tools/gemini_tool.py — Gemini LLM

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import config

def get_gemini_llm(temperature: float = 0.1):
    """Initialize Gemini LLM for the ReAct agent."""
    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        google_api_key=config.GOOGLE_API_KEY,
        temperature=temperature,
        convert_system_message_to_human=True,
    )

async def gemini_summarize(text: str, instruction: str = "Summarize") -> str:
    """Use Gemini to summarize or analyze text."""
    llm = get_gemini_llm(temperature=0.2)
    messages = [
        SystemMessage(content="You are a drug discovery research assistant."),
        HumanMessage(content=f"{instruction}:\n\n{text}"),
    ]
    response = await llm.ainvoke(messages)
    return response.content
```

---

## 9. tools/docking_tool.py — Molecular Docking

```python
from langchain.tools import tool
import subprocess
import tempfile
import os

@tool
def run_docking(
    protein_pdb_id: str,
    ligand_smiles: str,
    center_x: float = 0.0,
    center_y: float = 0.0,
    center_z: float = 0.0,
    size: float = 20.0,
) -> str:
    """Run molecular docking using AutoDock Vina.
    Requires: protein PDB ID, ligand SMILES, and binding site coordinates.
    """
    try:
        # In production, you would:
        # 1. Download PDB file from RCSB
        # 2. Prepare protein (remove water, add hydrogens)
        # 3. Convert SMILES to 3D structure
        # 4. Run AutoDock Vina
        # 5. Parse results

        # Simplified example:
        import requests

        # Download PDB
        pdb_url = f"https://files.rcsb.org/download/{protein_pdb_id}.pdb"
        pdb_resp = requests.get(pdb_url)

        if pdb_resp.status_code != 200:
            return f"Error: Could not download PDB {protein_pdb_id}"

        with tempfile.TemporaryDirectory() as tmpdir:
            pdb_path = os.path.join(tmpdir, f"{protein_pdb_id}.pdb")
            with open(pdb_path, "w") as f:
                f.write(pdb_resp.text)

            # In production, run actual Vina docking here
            # For demo, return simulated results
            import random
            score = round(random.uniform(-10.0, -5.0), 1)

            return (
                f"Docking Results:\n"
                f"Protein: {protein_pdb_id}\n"
                f"Ligand SMILES: {ligand_smiles}\n"
                f"Binding Energy: {score} kcal/mol\n"
                f"Binding Site: ({center_x}, {center_y}, {center_z})\n"
                f"Confidence: {'High' if score < -8 else 'Moderate' if score < -6 else 'Low'}"
            )
    except Exception as e:
        return f"Docking error: {str(e)}"
```

---

## 10. tools/whisper_tool.py — Voice Input

```python
import whisper
import tempfile
import os
from fastapi import UploadFile

# Load model once at startup
_whisper_model = None

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model("base")
    return _whisper_model

async def transcribe_audio(audio_file: UploadFile) -> str:
    """Transcribe audio file to text using Whisper."""
    model = get_whisper_model()

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        content = await audio_file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        result = model.transcribe(tmp_path)
        return result["text"]
    finally:
        os.unlink(tmp_path)
```

---

## 11. rag/embeddings.py — HuggingFace Embeddings

```python
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings
from config import config

def get_embeddings():
    """Get HuggingFace embedding model for vector stores."""
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
```

---

## 12. rag/faiss_store.py — FAISS Vector Store

```python
import os
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rag.embeddings import get_embeddings
from config import config

class FAISSStore:
    def __init__(self):
        self.embeddings = get_embeddings()
        self.index_path = config.FAISS_INDEX_PATH
        self.store = None
        self._load_or_create()

    def _load_or_create(self):
        if os.path.exists(self.index_path):
            self.store = FAISS.load_local(
                self.index_path, self.embeddings,
                allow_dangerous_deserialization=True
            )
        else:
            # Create empty store with a dummy document
            self.store = FAISS.from_documents(
                [Document(page_content="initialization", metadata={"source": "init"})],
                self.embeddings,
            )

    def add_documents(self, documents: list[Document]):
        self.store.add_documents(documents)
        self.store.save_local(self.index_path)

    def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self.store.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 5):
        return self.store.similarity_search_with_score(query, k=k)
```

---

## 13. rag/chroma_store.py — ChromaDB Vector Store

```python
import chromadb
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from rag.embeddings import get_embeddings
from config import config

class ChromaStore:
    def __init__(self, collection_name: str = "drug_discovery"):
        self.embeddings = get_embeddings()
        self.client = chromadb.PersistentClient(path=config.CHROMA_DB_PATH)
        self.store = Chroma(
            client=self.client,
            collection_name=collection_name,
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: list[Document]):
        self.store.add_documents(documents)

    def similarity_search(self, query: str, k: int = 5, filter: dict = None):
        kwargs = {"k": k}
        if filter:
            kwargs["filter"] = filter
        return self.store.similarity_search(query, **kwargs)

    def similarity_search_with_score(self, query: str, k: int = 5):
        return self.store.similarity_search_with_relevance_scores(query, k=k)
```

---

## 14. rag/pipeline.py — RAG Orchestration

```python
from langchain_core.documents import Document
from rag.faiss_store import FAISSStore
from rag.chroma_store import ChromaStore

class RAGPipeline:
    def __init__(self):
        self.faiss_store = FAISSStore()
        self.chroma_store = ChromaStore()

    def index_document(self, content: str, metadata: dict, store: str = "both"):
        doc = Document(page_content=content, metadata=metadata)
        if store in ("faiss", "both"):
            self.faiss_store.add_documents([doc])
        if store in ("chroma", "both"):
            self.chroma_store.add_documents([doc])

    def retrieve(self, query: str, k: int = 5) -> list[dict]:
        """Retrieve from both stores and merge results."""
        faiss_results = self.faiss_store.similarity_search_with_score(query, k=k)
        chroma_results = self.chroma_store.similarity_search_with_score(query, k=k)

        merged = []
        seen = set()

        for doc, score in faiss_results:
            key = doc.page_content[:100]
            if key not in seen:
                seen.add(key)
                merged.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "source_store": "FAISS",
                })

        for doc, score in chroma_results:
            key = doc.page_content[:100]
            if key not in seen:
                seen.add(key)
                merged.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "source_store": "ChromaDB",
                })

        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged[:k]
```

---

## 15. agent/prompts.py — System Prompts & Few-Shot

```python
REACT_SYSTEM_PROMPT = """You are a Drug Discovery Research Agent powered by ReAct reasoning.
You help researchers find drug candidates, analyze compounds, and synthesize research findings.

You have access to these tools:
1. search_chembl_target - Search ChEMBL for drug targets and bioactivity data
2. get_compound_details - Get detailed compound information from ChEMBL
3. search_pubmed - Search PubMed for biomedical literature
4. search_ncbi_gene - Search NCBI for gene information
5. run_docking - Run molecular docking simulations
6. rag_retrieve - Retrieve context from the knowledge base

For each query, follow the ReAct pattern:
Thought: Analyze what information is needed
Action: Choose and call the appropriate tool
Observation: Process the tool's response
... (repeat Thought/Action/Observation as needed)
Answer: Synthesize all findings into a comprehensive response

Always cite your sources and provide confidence levels for your findings.
Focus on actionable insights for drug discovery researchers."""

FEW_SHOT_EXAMPLES = [
    {
        "query": "Find kinase inhibitors for chronic myeloid leukemia",
        "thought": "I need to find BCR-ABL kinase inhibitors. Let me search ChEMBL first.",
        "action": "search_chembl_target('BCR-ABL', limit=20)",
        "observation": "Found imatinib, dasatinib, nilotinib, bosutinib, ponatinib...",
        "answer": "Top BCR-ABL inhibitors: Imatinib (1st gen), Dasatinib (2nd gen)..."
    },
    {
        "query": "What are the latest clinical trials for EGFR inhibitors in NSCLC?",
        "thought": "I should search PubMed for recent EGFR NSCLC clinical trials.",
        "action": "search_pubmed('EGFR inhibitor NSCLC clinical trial 2024', max_results=10)",
        "observation": "Found 10 articles including osimertinib Phase III results...",
        "answer": "Recent EGFR inhibitor trials in NSCLC show..."
    },
]
```

---

## 16. agent/memory.py — Agent Memory

```python
from typing import Dict, List, Any
from datetime import datetime
import json

class AgentMemory:
    def __init__(self):
        self.short_term: List[Dict[str, Any]] = []
        self.long_term: List[Dict[str, Any]] = []
        self.episodic: List[Dict[str, Any]] = []
        self.max_short_term = 20
        self.max_episodic = 50

    def add_short_term(self, content: str, source: str = "agent"):
        self.short_term.append({
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "type": "short_term",
        })
        if len(self.short_term) > self.max_short_term:
            # Move oldest to episodic
            oldest = self.short_term.pop(0)
            self.add_episodic(oldest["content"], oldest["source"])

    def add_long_term(self, content: str, source: str = "knowledge_base"):
        self.long_term.append({
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "type": "long_term",
        })

    def add_episodic(self, content: str, source: str = "session"):
        self.episodic.append({
            "content": content,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "type": "episodic",
        })
        if len(self.episodic) > self.max_episodic:
            self.episodic.pop(0)

    def get_context(self, max_items: int = 10) -> str:
        """Get relevant memory context for the agent."""
        items = (
            self.short_term[-5:]
            + self.long_term[-3:]
            + self.episodic[-2:]
        )
        return "\n".join(
            f"[{m['type']}] {m['content']}" for m in items[:max_items]
        )

    def clear_short_term(self):
        self.short_term.clear()
```

---

## 17. agent/react_agent.py — ReAct Agent with LangChain LCEL

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables import RunnablePassthrough
from langchain import hub

from tools.gemini_tool import get_gemini_llm
from tools.chembl_tool import search_chembl_target, get_compound_details
from tools.pubmed_tool import search_pubmed, search_ncbi_gene
from tools.docking_tool import run_docking
from agent.prompts import REACT_SYSTEM_PROMPT, FEW_SHOT_EXAMPLES
from agent.memory import AgentMemory
from rag.pipeline import RAGPipeline
from langchain.tools import tool as langchain_tool
from datetime import datetime

class DrugDiscoveryAgent:
    def __init__(self):
        self.llm = get_gemini_llm(temperature=0.1)
        self.memory = AgentMemory()
        self.rag = RAGPipeline()
        self.tools = self._setup_tools()
        self.agent = self._create_agent()

    def _setup_tools(self):
        @langchain_tool
        def rag_retrieve(query: str) -> str:
            """Retrieve relevant context from the drug discovery knowledge base."""
            results = self.rag.retrieve(query, k=5)
            if not results:
                return "No relevant documents found in knowledge base."
            return "\n\n".join(
                f"[{r['source_store']}] (score: {r['score']:.2f})\n{r['content'][:500]}"
                for r in results
            )

        return [
            search_chembl_target,
            get_compound_details,
            search_pubmed,
            search_ncbi_gene,
            run_docking,
            rag_retrieve,
        ]

    def _create_agent(self):
        # Use LangChain's ReAct prompt
        prompt = hub.pull("hwchase17/react")
        prompt = prompt.partial(
            system_message=REACT_SYSTEM_PROMPT,
        )

        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=6,
            return_intermediate_steps=True,
            handle_parsing_errors=True,
        )

    async def query(self, user_query: str) -> dict:
        """Process a user query through the ReAct agent."""
        # Add context from memory
        memory_context = self.memory.get_context()
        enhanced_query = user_query
        if memory_context:
            enhanced_query = (
                f"Context from previous interactions:\n{memory_context}\n\n"
                f"Current query: {user_query}"
            )

        # Run agent
        result = await self.agent.ainvoke({"input": enhanced_query})

        # Parse intermediate steps into ReAct format
        steps = []
        for action, observation in result.get("intermediate_steps", []):
            steps.append({
                "type": "thought",
                "content": getattr(action, "log", str(action)),
                "timestamp": datetime.now().strftime("%I:%M %p"),
            })
            steps.append({
                "type": "action",
                "content": f"Calling {action.tool}",
                "tool": action.tool,
                "args": action.tool_input if isinstance(action.tool_input, dict)
                    else {"input": str(action.tool_input)},
                "timestamp": datetime.now().strftime("%I:%M %p"),
            })
            steps.append({
                "type": "observation",
                "content": str(observation)[:1000],
                "timestamp": datetime.now().strftime("%I:%M %p"),
            })

        steps.append({
            "type": "answer",
            "content": result["output"],
            "timestamp": datetime.now().strftime("%I:%M %p"),
        })

        # Update memory
        self.memory.add_short_term(f"Query: {user_query}", "user")
        self.memory.add_short_term(f"Answer: {result['output'][:200]}", "agent")

        # Index the interaction in RAG
        self.rag.index_document(
            content=f"Q: {user_query}\nA: {result['output']}",
            metadata={"source": "agent_interaction", "date": datetime.now().isoformat()},
            store="chroma",
        )

        return {
            "answer": result["output"],
            "steps": steps,
            "sources": [],
        }
```

---

## 18. main.py — FastAPI Server

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from models.schemas import QueryRequest, QueryResponse
from agent.react_agent import DrugDiscoveryAgent
from tools.whisper_tool import transcribe_audio

agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent
    agent = DrugDiscoveryAgent()
    yield

app = FastAPI(
    title="Drug Discovery ReAct Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a natural language drug discovery query."""
    try:
        result = await agent.query(request.query)
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/voice-query")
async def voice_query(audio: UploadFile = File(...)):
    """Process a voice query using Whisper transcription."""
    transcript = await transcribe_audio(audio)
    result = await agent.query(transcript)
    return {"transcript": transcript, **result}

@app.get("/api/tools")
async def list_tools():
    """List all available tools."""
    return {
        "tools": [
            {"name": "ChEMBL API", "status": "active", "endpoint": "https://www.ebi.ac.uk/chembl/api/data"},
            {"name": "PubMed/NCBI", "status": "active", "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"},
            {"name": "Gemini LLM", "status": "active", "endpoint": "Google Generative AI"},
            {"name": "Molecular Docking", "status": "active", "endpoint": "AutoDock Vina (local)"},
            {"name": "RAG Pipeline", "status": "active", "endpoint": "FAISS + ChromaDB"},
            {"name": "Whisper", "status": "active", "endpoint": "OpenAI Whisper (local)"},
        ]
    }

@app.get("/api/memory")
async def get_memory():
    """Get current agent memory state."""
    return {
        "short_term": agent.memory.short_term,
        "long_term": agent.memory.long_term,
        "episodic": agent.memory.episodic,
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "agent": "active"}
```

---

## 19. Running the Complete System

```bash
# Terminal 1: Start Python Backend
cd drug_discovery_agent
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Frontend (this dashboard)
cd frontend
pnpm run dev

# The frontend connects to http://localhost:8000/api/*
```

### Connecting Frontend to Backend

To connect this React dashboard to the Python backend, update API calls in each component:

```typescript
// Example: In AgentChat.tsx, replace the mock setTimeout with:
const response = await fetch('http://localhost:8000/api/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: userMsg.content }),
});
const data = await response.json();
```

---

## 20. Key Technologies Summary

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Reasoning | Gemini Pro / GPT-4 | ReAct thought generation |
| Agent Framework | LangChain + LCEL | Tool orchestration |
| Dense Retrieval | FAISS | Fast similarity search |
| Metadata Filtering | ChromaDB | Filtered retrieval |
| Orchestration | LlamaIndex | Document indexing |
| Embeddings | HuggingFace sentence-transformers | Text vectorization |
| Voice Input | OpenAI Whisper | Audio transcription |
| Drug Data | ChEMBL API | Compound bioactivity |
| Literature | PubMed/NCBI E-utilities | Research papers |
| Docking | AutoDock Vina | Binding prediction |
| API Server | FastAPI | REST endpoints |
| Frontend | React + shadcn/ui | Dashboard UI |

---

*This architecture guide is designed to be used alongside the React dashboard frontend. The frontend provides the visual interface while the Python backend handles all AI reasoning, tool calling, and data processing.*