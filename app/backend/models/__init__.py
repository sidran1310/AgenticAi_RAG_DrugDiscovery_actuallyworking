"""
Data models and schemas for the Drug Discovery AI Agent.
Uses Pydantic for validation and serialization.
"""
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class AgentType(str, Enum):
    """Available agent types"""
    DEFAULT = "default"
    GROQ = "groq"
    GEMINI = "gemini"
    LANGCHAIN = "langchain"
    GRAPH = "graph"

class ServiceStatus(str, Enum):
    """Service availability status"""
    READY = "ready"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    MAINTENANCE = "maintenance"

# Request Models
class ChatRequest(BaseModel):
    """Chat message request"""
    message: str = Field(..., min_length=1, max_length=2000, description="User's question or message")
    agent_type: Optional[AgentType] = Field(AgentType.DEFAULT, description="Agent type to use")
    session_id: Optional[str] = Field(None, description="User session identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

class SearchRequest(BaseModel):
    """Generic search request"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Maximum results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Search filters")

class RAGSearchRequest(SearchRequest):
    """RAG search specific request"""
    include_metadata: Optional[bool] = Field(True, description="Include document metadata")
    min_relevance: Optional[float] = Field(0.1, ge=0.0, le=1.0, description="Minimum relevance score")

# Response Models
class ThoughtProcess(BaseModel):
    """Agent thought process step"""
    step: int = Field(..., ge=1, description="Step number")
    content: str = Field(..., description="Step description")
    timestamp: Optional[datetime] = Field(None, description="Step timestamp")

class Action(BaseModel):
    """Agent action taken"""
    tool: str = Field(..., description="Tool or service used")
    input: str = Field(..., description="Input provided to tool")
    result: str = Field(..., description="Result from tool")
    duration: Optional[float] = Field(None, description="Execution time in seconds")
    success: Optional[bool] = Field(True, description="Whether action succeeded")

class Observation(BaseModel):
    """Agent observation"""
    content: str = Field(..., description="Observation content")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    source: Optional[str] = Field(None, description="Observation source")

class Metadata(BaseModel):
    """Response metadata"""
    topic: Optional[str] = Field(None, description="Extracted topic")
    pubmed_count: Optional[int] = Field(None, description="Number of PubMed results")
    pubmed_ids: Optional[List[str]] = Field(None, description="PubMed IDs found")
    pdb_count: Optional[int] = Field(None, description="Number of PDB structures")
    pdb_ids: Optional[List[str]] = Field(None, description="PDB IDs found")
    compound: Optional[Dict[str, Any]] = Field(None, description="Compound data")
    gene_id: Optional[str] = Field(None, description="NCBI gene ID")
    rag_sources: Optional[int] = Field(None, description="Number of RAG sources")
    timestamp: str = Field(..., description="Response timestamp")
    processing_time: Optional[float] = Field(None, description="Total processing time")
    session_id: Optional[str] = Field(None, description="Session identifier")

class ChatResponse(BaseModel):
    """Chat response"""
    chat: Optional[str] = Field(None, description="Standard chat answer")
    response: str = Field(..., description="AI generated response")
    thought_process: List[ThoughtProcess] = Field(default_factory=list, description="Agent reasoning steps")
    actions: List[Action] = Field(default_factory=list, description="Actions taken")
    observations: List[Observation] = Field(default_factory=list, description="Agent observations")
    metadata: Metadata = Field(..., description="Response metadata")
    status: str = Field(..., description="Response status")
    error: Optional[str] = Field(None, description="Error message if any")
    molecules: Optional[List[Dict[str, Any]]] = Field(None, description="Molecular compounds data")
    papers_graph: Optional[Dict[str, Any]] = Field(None, description="Research papers graph data")
    rag_results: Optional[List[Dict[str, Any]]] = Field(None, description="RAG search results")
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Standard tool execution records")
    tools_used: Optional[List[Dict[str, Any]]] = Field(None, description="Tools used with status")

class AgentInfo(BaseModel):
    """Agent information"""
    id: str = Field(..., description="Agent identifier")
    name: str = Field(..., description="Agent display name")
    description: str = Field(..., description="Agent description")
    status: ServiceStatus = Field(..., description="Agent availability status")
    capabilities: Optional[List[str]] = Field(None, description="Agent capabilities")
    version: Optional[str] = Field(None, description="Agent version")

class ConfigResponse(BaseModel):
    """Configuration response"""
    status: str = Field(..., description="Configuration status")
    agent_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    capabilities: List[str] = Field(..., description="System capabilities")
    groq_available: bool = Field(..., description="Groq API availability")
    gemini_available: bool = Field(..., description="Gemini API availability")
    agent_types: List[AgentInfo] = Field(..., description="Available agent types")
    tool_stats: Dict[str, Dict[str, Any]] = Field(..., description="Tool usage statistics")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Service status information")

class RAGChunk(BaseModel):
    """RAG search result chunk"""
    id: str = Field(..., description="Chunk identifier")
    source: str = Field(..., description="Data source")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Chunk content")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    chunk_index: int = Field(..., ge=1, description="Chunk position")
    total_chunks: int = Field(..., ge=1, description="Total chunks")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")

class RAGResponse(BaseModel):
    """RAG search response"""
    chunks: List[RAGChunk] = Field(..., description="Search result chunks")
    total: int = Field(..., description="Total chunks found")
    query: str = Field(..., description="Original query")
    search_metadata: Optional[Dict[str, Any]] = Field(None, description="Search metadata")

class CompoundData(BaseModel):
    """Compound information"""
    id: str = Field(..., description="Compound identifier")
    name: str = Field(..., description="Compound name")
    chembl_id: Optional[str] = Field(None, description="ChEMBL identifier")
    smiles: Optional[str] = Field(None, description="SMILES notation")
    molecular_weight: Optional[float] = Field(None, description="Molecular weight")
    logp: Optional[float] = Field(None, description="LogP value")
    tpsa: Optional[float] = Field(None, description="Topological polar surface area")
    hbd: Optional[int] = Field(None, description="Hydrogen bond donors")
    hba: Optional[int] = Field(None, description="Hydrogen bond acceptors")
    rotatable_bonds: Optional[int] = Field(None, description="Rotatable bonds")
    phase: Optional[str] = Field(None, description="Development phase")
    indication: Optional[str] = Field(None, description="Medical indication")
    mechanism: Optional[str] = Field(None, description="Mechanism of action")
    docking_score: Optional[float] = Field(None, description="Docking score")
    ic50: Optional[str] = Field(None, description="IC50 value")
    lipinski_pass: Optional[bool] = Field(None, description="Lipinski rule compliance")

class CompoundsResponse(BaseModel):
    """Compounds search response"""
    compounds: List[CompoundData] = Field(..., description="Found compounds")
    total: int = Field(..., description="Total compounds found")
    query: str = Field(..., description="Original query")

class PaperData(BaseModel):
    """Research paper information"""
    id: str = Field(..., description="Paper identifier")
    title: str = Field(..., description="Paper title")
    authors: str = Field(..., description="Paper authors")
    journal: str = Field(..., description="Journal name")
    date: str = Field(..., description="Publication date")
    abstract: str = Field(..., description="Paper abstract")
    ai_summary: str = Field(..., description="AI-generated summary")
    source: str = Field(..., description="Data source")
    credibility_score: float = Field(..., ge=0.0, le=100.0, description="Credibility score")
    citation_count: int = Field(..., ge=0, description="Citation count")
    doi: Optional[str] = Field(None, description="DOI identifier")
    tags: List[str] = Field(..., description="Paper tags")
    pubmed_id: Optional[str] = Field(None, description="PubMed ID")

class PapersResponse(BaseModel):
    """Papers search response"""
    papers: List[PaperData] = Field(..., description="Found papers")
    total: int = Field(..., description="Total papers found")
    query: str = Field(..., description="Original query")

class MemoryEntry(BaseModel):
    """Agent memory entry"""
    id: str = Field(..., description="Memory entry ID")
    type: str = Field(..., description="Memory type")
    content: str = Field(..., description="Memory content")
    timestamp: str = Field(..., description="Entry timestamp")
    relevance: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    source: str = Field(..., description="Memory source")

class PlanStep(BaseModel):
    """Agent plan step"""
    id: str = Field(..., description="Step ID")
    description: str = Field(..., description="Step description")
    status: str = Field(..., description="Step status")
    tool: Optional[str] = Field(None, description="Tool used")

class FewShotExample(BaseModel):
    """Few-shot learning example"""
    id: str = Field(..., description="Example ID")
    query: str = Field(..., description="Example query")
    reasoning: str = Field(..., description="Reasoning process")
    tools: List[str] = Field(..., description="Tools used")
    outcome: str = Field(..., description="Outcome")

class MemoryResponse(BaseModel):
    """Agent memory response"""
    memory_entries: List[MemoryEntry] = Field(..., description="Memory entries")
    plan_steps: List[PlanStep] = Field(..., description="Current plan steps")
    few_shot_examples: List[FewShotExample] = Field(..., description="Few-shot examples")

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Service health status")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")

# Error Models
class ErrorResponse(BaseModel):
    """Error response"""
    error: str = Field(..., description="Error message")
    status: str = Field("error", description="Response status")
    code: Optional[int] = Field(None, description="HTTP status code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    traceback: Optional[str] = Field(None, description="Error traceback (debug mode only)")
