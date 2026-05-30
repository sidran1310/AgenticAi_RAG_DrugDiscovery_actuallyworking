import { getAPIBaseURL } from './config';

// Backend API base URL
const apiUrl = (path: string) => `${getAPIBaseURL()}${path}`;

// Types for API responses
export interface ChatResponse {
  response: string;
  thought_process: Array<{
    step: number;
    content: string;
  }>;
  actions: Array<{
    tool: string;
    input: string;
    result: string;
  }>;
  observations: Array<string | {
    content: string;
    confidence?: number;
    source?: string;
  }>;
  metadata: {
    topic: string;
    pubmed_count: number;
    pubmed_ids: string[];
    pdb_count: number;
    pdb_ids: string[];
    compound: any;
    gene_id: string | null;
    rag_sources: number;
    timestamp: string;
  };
  status: string;
}

export interface AgentInfo {
  id: string;
  name: string;
  description: string;
  status?: string;
}

export interface AgentsResponse {
  agents: AgentInfo[];
  langchain_available: boolean;
  langgraph_available: boolean;
}

export interface ConfigResponse {
  status: string;
  agentName: string;
  version: string;
  capabilities: string[];
  groq_available: boolean;
  gemini_available?: boolean;
  agent_types?: AgentInfo[];
  tool_stats?: {
    [key: string]: {
      status: string;
      callCount: number;
      avgLatency: string;
      lastCalled: string;
    };
  };
}

export interface RAGResponse {
  chunks: Array<{
    id: string;
    source: string;
    title: string;
    content: string;
    relevanceScore: number;
    chunkIndex: number;
    totalChunks: number;
    metadata: {
      database: string;
      date: string;
      pubmed_id?: string;
    };
  }>;
  total: number;
  query: string;
}

export interface CompoundsResponse {
  compounds: Array<{
    id: string;
    name: string;
    chemblId: string;
    smiles: string;
    molecularWeight: number;
    logP: number;
    tpsa: number;
    hbd: number;
    hba: number;
    rotBonds: number;
    phase: string;
    indication: string;
    mechanism: string;
    dockingScore?: number;
    ic50?: string;
    lipinskiPass: boolean;
  }>;
  total: number;
  query: string;
}

export interface PapersResponse {
  papers: Array<{
    id: string;
    title: string;
    authors: string;
    journal: string;
    date: string;
    abstract: string;
    aiSummary: string;
    source: string;
    credibilityScore: number;
    citationCount: number;
    doi?: string;
    tags: string[];
  }>;
  total: number;
  query: string;
}

export interface MemoryResponse {
  memory_entries: Array<{
    id: string;
    type: string;
    content: string;
    timestamp: string;
    relevance: number;
    source: string;
  }>;
  plan_steps: Array<{
    id: string;
    description: string;
    status: string;
    tool?: string;
  }>;
  few_shot_examples: Array<{
    id: string;
    query: string;
    reasoning: string;
    tools: string[];
    outcome: string;
  }>;
}

// Function to send chat message to backend
export async function sendChatMessage(message: string, agentType?: string): Promise<ChatResponse> {
  const payload: Record<string, any> = { message };
  if (agentType) {
    payload.agentType = agentType;
  }

  const maxRetries = 3;
  const timeout = 30000; // 30 seconds

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(apiUrl('/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `HTTP error! status: ${response.status}`;

        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch {
          // If not JSON, use the text
          if (errorText) {
            errorMessage = errorText;
          }
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();
      return data;

    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Request timed out. Please try again.');
      }

      if (attempt === maxRetries) {
        if (error instanceof Error) {
          throw error;
        }
        throw new Error('An unexpected error occurred');
      }

      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
    }
  }

  throw new Error('Failed to send message after retries');
}

// Function to get available agents
export async function getAvailableAgents(): Promise<AgentsResponse> {
  const response = await fetch(apiUrl('/agents'));
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
}

// Function to get backend config
export async function getBackendConfig(): Promise<ConfigResponse> {
  const response = await fetch(apiUrl('/config'));

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to check backend health
export async function getBackendHealth() {
  const response = await fetch(apiUrl('/health'));

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to search RAG database
export async function searchRAG(query: string, limit: number = 10): Promise<RAGResponse> {
  const response = await fetch(apiUrl('/rag'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to search compounds
export async function searchCompounds(query: string, limit: number = 10): Promise<CompoundsResponse> {
  const response = await fetch(apiUrl('/compounds'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to perform manual search on specific database
export async function manualSearch(type: 'pubmed' | 'chembl' | 'pubchem' | 'pdb', query: string, filters?: any, limit: number = 20): Promise<any> {
  const response = await fetch(apiUrl('/search/manual'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ type, query, filters, limit }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to perform advanced multi-database search
export async function advancedSearch(query: string, databases?: string[], filters?: any): Promise<any> {
  const response = await fetch(apiUrl('/search/advanced'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      databases: databases || ['pubmed', 'chembl', 'pubchem'],
      filters
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to search papers
export async function searchPapers(query: string, limit: number = 10): Promise<PapersResponse> {
  const response = await fetch(apiUrl('/papers'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query, limit }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Function to get agent memory
export async function getAgentMemory(): Promise<MemoryResponse> {
  const response = await fetch(apiUrl('/memory'));

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function searchStructures(query: string) {
  const response = await fetch(apiUrl('/structures/search'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function downloadStructure(pdbId: string) {
  const response = await fetch(apiUrl(`/structures/download/${encodeURIComponent(pdbId)}`));

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export async function runDocking(compound: string, pdbId: string) {
  const response = await fetch(apiUrl('/dock'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ compound, pdb_id: pdbId }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}
