import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Database, Search, FileText, Hash, ExternalLink, Sparkles, Filter, BarChart3, Layers, Loader2, BookOpen, Atom, Server } from "lucide-react";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";
import { searchRAG, manualSearch } from "@/lib/api";

interface Chunk {
  id: string; content: string; source: string; score: number;
  meta: { year: number; disease: string; docType: string; doi?: string };
  keywords: string[];
}

const CHUNKS: Chunk[] = [
  { id: "c1", content: "Lecanemab, a humanized IgG1 monoclonal antibody that selectively binds to large soluble AB protofibrils, demonstrated significant clinical benefit in the Phase 3 CLARITY AD trial. The primary endpoint showed a 27% reduction in CDR-SB decline compared to placebo (p<0.001).", source: "NEJM_2025_Lecanemab.pdf", score: 0.96, meta: { year: 2025, disease: "Alzheimer's", docType: "Clinical Trial", doi: "10.1056/NEJMoa2212948" }, keywords: ["lecanemab", "protofibrils", "CDR-SB", "CLARITY AD"] },
  { id: "c2", content: "The TRAILBLAZER-ALZ 2 trial demonstrated that donanemab slowed clinical progression by 35% in the combined tau population and 40% in the low/medium tau subgroup. 80% of participants achieved amyloid clearance by 12 months.", source: "JAMA_2025_Donanemab.pdf", score: 0.93, meta: { year: 2025, disease: "Alzheimer's", docType: "Clinical Trial", doi: "10.1001/jama.2023.13239" }, keywords: ["donanemab", "tau stratification", "amyloid clearance"] },
  { id: "c3", content: "First-generation BACE1 inhibitors failed due to: (1) excessive AB reduction impairing synaptic function, (2) off-target BACE2 inhibition causing retinal toxicity, (3) intervention too late in disease progression.", source: "NatRevDrugDiscov_2025.pdf", score: 0.89, meta: { year: 2025, disease: "Alzheimer's", docType: "Review" }, keywords: ["BACE1", "synaptic function", "BACE2", "retinal toxicity"] },
  { id: "c4", content: "High-resolution cryo-EM structures of AB42 fibrils at 2.1A resolution revealed three novel druggable binding pockets. Virtual screening of 50,000 compounds identified 12 hits with sub-micromolar binding affinity.", source: "Science_2024_CryoEM.pdf", score: 0.91, meta: { year: 2024, disease: "Alzheimer's", docType: "Research", doi: "10.1126/science.adq1234" }, keywords: ["cryo-EM", "AB42 fibrils", "druggable pockets", "virtual screening"] },
  { id: "c5", content: "Plasma p-tau217 demonstrated 96% accuracy (AUC 0.98) for detecting amyloid positivity in 1,200 participants. This blood-based biomarker could enable population-level screening in primary care.", source: "NatMed_2025_Biomarkers.pdf", score: 0.87, meta: { year: 2025, disease: "Alzheimer's", docType: "Research" }, keywords: ["p-tau217", "blood biomarker", "amyloid positivity", "screening"] },
];

function Highlight({ text, words }: { text: string; words: string[] }) {
  if (!words.length) return <span>{text}</span>;
  const pat = new RegExp(`(${words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  const parts = text.split(pat);
  return <span>{parts.map((p, i) => words.some((w) => w.toLowerCase() === p.toLowerCase()) ? <mark key={i} className="bg-rose-400/15 text-rose-200/90 rounded px-0.5">{p}</mark> : <span key={i}>{p}</span>)}</span>;
}

export default function RAGExplorer() {
  const { query: globalQuery, results } = useGlobalQuery();
  const [query, setQuery] = useState("");
  const [apiChunks, setApiChunks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [yearF, setYearF] = useState("all");
  const [diseaseF, setDiseaseF] = useState("all");
  const [minScore, setMinScore] = useState("0");
  const [searchType, setSearchType] = useState<'rag' | 'manual'>('rag');
  const [manualDatabase, setManualDatabase] = useState<'pubmed' | 'chembl' | 'pubchem' | 'pdb'>('pubmed');
  const [manualResults, setManualResults] = useState<any>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError("");

    try {
      if (searchType === 'manual') {
        const results = await manualSearch(manualDatabase, query);
        setManualResults(results);
        setApiChunks([]); // Clear RAG results
      } else {
        const results = await searchRAG(query);
        setApiChunks(results.chunks || []);
        setManualResults(null); // Clear manual results
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const getDatabaseIcon = (type: string) => {
    switch (type) {
      case 'pubmed': return <BookOpen className="w-4 h-4" />;
      case 'chembl': return <Atom className="w-4 h-4" />;
      case 'pubchem': return <Database className="w-4 h-4" />;
      case 'pdb': return <Server className="w-4 h-4" />;
      default: return <Search className="w-4 h-4" />;
    }
  };

  const normalizeChunk = (chunk: any, index: number) => ({
    id: chunk.id || `chunk-${index}`,
    content: chunk.content || chunk.abstract || chunk.text || "",
    source: chunk.source || chunk.title || "Knowledge base",
    score: chunk.score ?? chunk.confidence ?? chunk.relevanceScore ?? chunk.relevance_score ?? 0,
    meta: chunk.meta || {
      year: Number(String(chunk.metadata?.date || "").slice(0, 4)) || new Date().getFullYear(),
      disease: chunk.metadata?.disease || "Query-specific",
      docType: chunk.metadata?.docType || chunk.source || "Retrieved source",
      doi: chunk.metadata?.doi,
    },
    keywords: chunk.keywords || [],
  });

  const chunks = ((results.rag_results?.length ? results.rag_results : results.ragResults) || apiChunks).map(normalizeChunk);

  useEffect(() => { if (globalQuery) setQuery(globalQuery); }, [globalQuery]);

  useEffect(() => {
    if (!query.trim() || results.rag_results?.length || results.ragResults?.length) return;
    const controller = new AbortController();
    setLoading(true);
    setError("");
    const timeout = setTimeout(async () => {
      try {
        const data = await searchRAG(query.trim(), 10);
        if (!controller.signal.aborted) setApiChunks(data.chunks || []);
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "RAG search failed");
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 350);
    return () => {
      controller.abort();
      clearTimeout(timeout);
    };
  }, [query, results.rag_results?.length, results.ragResults?.length]);

  const min = parseFloat(minScore) || 0;
  const filtered = chunks.filter((c: any) => {
    if (yearF !== "all" && c.meta?.year?.toString() !== yearF) return false;
    if (diseaseF !== "all" && c.meta?.disease !== diseaseF) return false;
    if ((c.score || c.confidence || 0) < min) return false;
    if (query) { const q = query.toLowerCase(); return c.content?.toLowerCase().includes(q) || c.source?.toLowerCase().includes(q) || c.keywords?.some((k: string) => k.toLowerCase().includes(q)); }
    return true;
  });

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-rose-500/[0.04]">
        <h2 className="text-[13px] font-semibold text-rose-100/90 mb-0.5">RAG Knowledge Base</h2>
        <p className="text-[10px] text-rose-300/30 mb-3">FAISS & ChromaDB vector stores</p>
        <div className="grid grid-cols-3 gap-3 mb-3">
          {[
            { label: "Retrieved Chunks", value: chunks.length.toString(), icon: Database, color: "text-rose-300/70" },
            { label: "Backend Index", value: "Live", icon: Layers, color: "text-fuchsia-300/70" },
            { label: "Avg Score", value: chunks.length ? (chunks.reduce((a: number, c: any) => a + c.score, 0) / chunks.length).toFixed(2) : "0.00", icon: BarChart3, color: "text-emerald-300/70" },
          ].map((s, i) => (
            <Card key={i} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-3 rounded-xl">
              <s.icon className={`w-3.5 h-3.5 ${s.color} mb-1`} />
              <p className="text-lg font-bold text-rose-100/85">{s.value}</p>
              <p className="text-[10px] text-rose-300/25">{s.label}</p>
            </Card>
          ))}
        </div>
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-rose-300/25" />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search knowledge base..."
            className="pl-9 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-100 placeholder:text-rose-300/20 focus-visible:ring-rose-400/20 rounded-xl text-[12px]" />
        </div>

        {/* Search Type Selector */}
        <div className="flex items-center gap-2 mb-3">
          <Select value={searchType} onValueChange={(value: any) => setSearchType(value)}>
            <SelectTrigger className="flex-1 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-100/80 text-[11px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="rag">RAG Search</SelectItem>
              <SelectItem value="manual">Manual Database Search</SelectItem>
            </SelectContent>
          </Select>

          {searchType === 'manual' && (
            <Select value={manualDatabase} onValueChange={(value: any) => setManualDatabase(value)}>
              <SelectTrigger className="flex-1 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-100/80 text-[11px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pubmed">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-3 h-3" />
                    PubMed
                  </div>
                </SelectItem>
                <SelectItem value="chembl">
                  <div className="flex items-center gap-2">
                    <Atom className="w-3 h-3" />
                    ChEMBL
                  </div>
                </SelectItem>
                <SelectItem value="pubchem">
                  <div className="flex items-center gap-2">
                    <Database className="w-3 h-3" />
                    PubChem
                  </div>
                </SelectItem>
                <SelectItem value="pdb">
                  <div className="flex items-center gap-2">
                    <Server className="w-3 h-3" />
                    PDB
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          )}

          <Button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="bg-rose-500/20 hover:bg-rose-500/30 border-rose-500/30 px-3"
          >
            {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
          </Button>
        </div>

        <div className="flex items-center gap-3">
          <Filter className="w-3.5 h-3.5 text-rose-300/20 shrink-0" />
          <Select value={yearF} onValueChange={setYearF}>
            <SelectTrigger className="w-[90px] h-7 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-300/50 text-[10px] rounded-lg"><SelectValue /></SelectTrigger>
            <SelectContent className="bg-[#1A1322] border-rose-500/[0.08]">
              <SelectItem value="all" className="text-rose-200/60 text-[10px]">All Years</SelectItem>
              <SelectItem value="2025" className="text-rose-200/60 text-[10px]">2025</SelectItem>
              <SelectItem value="2024" className="text-rose-200/60 text-[10px]">2024</SelectItem>
            </SelectContent>
          </Select>
          <Select value={diseaseF} onValueChange={setDiseaseF}>
            <SelectTrigger className="w-[110px] h-7 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-300/50 text-[10px] rounded-lg"><SelectValue /></SelectTrigger>
            <SelectContent className="bg-[#1A1322] border-rose-500/[0.08]">
              <SelectItem value="all" className="text-rose-200/60 text-[10px]">All Diseases</SelectItem>
              <SelectItem value="Alzheimer's" className="text-rose-200/60 text-[10px]">Alzheimer&apos;s</SelectItem>
            </SelectContent>
          </Select>
          <Select value={minScore} onValueChange={setMinScore}>
            <SelectTrigger className="w-[100px] h-7 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-300/50 text-[10px] rounded-lg"><SelectValue /></SelectTrigger>
            <SelectContent className="bg-[#1A1322] border-rose-500/[0.08]">
              <SelectItem value="0" className="text-rose-200/60 text-[10px]">Any Score</SelectItem>
              <SelectItem value="0.85" className="text-rose-200/60 text-[10px]">0.85+</SelectItem>
              <SelectItem value="0.9" className="text-rose-200/60 text-[10px]">0.90+</SelectItem>
              <SelectItem value="0.95" className="text-rose-200/60 text-[10px]">0.95+</SelectItem>
            </SelectContent>
          </Select>
          <span className="text-[10px] text-rose-300/20 ml-auto">{loading ? "Searching..." : `${filtered.length} results`}</span>
        </div>
        {error && <p className="text-[10px] text-red-300/60 mt-2">{error}</p>}
      </div>
      <ScrollArea className="flex-1 p-4">
        {manualResults ? (
          // Manual Search Results
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-3">
              {getDatabaseIcon(manualDatabase)}
              <span className="text-sm font-semibold text-rose-100/80">
                {manualDatabase.toUpperCase()} Results
              </span>
              <Badge variant="outline" className="bg-rose-500/10 text-rose-300/70 border-rose-500/20">
                {manualResults.count || manualResults.length || 0} found
              </Badge>
            </div>

            {manualResults.error ? (
              <Card className="bg-red-500/[0.03] border-red-500/[0.06] p-4">
                <p className="text-red-300/70">{manualResults.error}</p>
              </Card>
            ) : manualResults.data ? (
              manualResults.data.map((item: any, index: number) => (
                <Card key={index} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-4 hover:border-rose-400/10 transition-all duration-300 rounded-xl">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2">
                      {getDatabaseIcon(manualDatabase)}
                      <span className="text-[10px] text-rose-300/40 font-mono">
                        {item.id || item.pubmed_id || item.chembl_id || item.cid || `item-${index + 1}`}
                      </span>
                    </div>
                    <Badge variant="outline" className="bg-rose-500/10 text-rose-300/70 border-rose-500/20 text-[9px]">
                      {manualDatabase}
                    </Badge>
                  </div>

                  <h4 className="text-[12px] font-semibold text-rose-100/90 mb-2 leading-tight">
                    {item.title || item.name || item.pref_name || item.iupac_name || 'No title available'}
                  </h4>

                  <p className="text-[11px] text-rose-200/60 mb-3 line-clamp-3">
                    {item.abstract || item.description || item.synopsis || item.smiles || 'No description available'}
                  </p>

                  <div className="flex items-center gap-2 flex-wrap">
                    {item.year && (
                      <Badge variant="outline" className="bg-blue-500/10 text-blue-300/70 border-blue-500/20 text-[9px]">
                        {item.year}
                      </Badge>
                    )}
                    {item.authors && (
                      <Badge variant="outline" className="bg-green-500/10 text-green-300/70 border-green-500/20 text-[9px]">
                        {item.authors.length} authors
                      </Badge>
                    )}
                    {item.molecular_weight && (
                      <Badge variant="outline" className="bg-purple-500/10 text-purple-300/70 border-purple-500/20 text-[9px]">
                        MW: {item.molecular_weight}
                      </Badge>
                    )}
                    {item.doi && (
                      <a href={`https://doi.org/${item.doi}`} target="_blank" rel="noopener noreferrer"
                         className="flex items-center gap-1 text-[9px] text-rose-300/50 hover:text-rose-200/70 transition-colors">
                        <ExternalLink className="w-3 h-3" />
                        DOI
                      </a>
                    )}
                  </div>
                </Card>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <Database className="w-10 h-10 text-rose-300/15 mb-3" />
                <p className="text-[13px] text-rose-300/30 mb-1">No results found</p>
                <p className="text-[10px] text-rose-300/15">Try adjusting your search query</p>
              </div>
            )}
          </div>
        ) : filtered.length === 0 ? (
          // RAG Search Empty State
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <Sparkles className="w-10 h-10 text-rose-300/15 mb-3" />
            <p className="text-[13px] text-rose-300/30 mb-1">No matching chunks</p>
            <p className="text-[10px] text-rose-300/15">Adjust filters or search query</p>
          </div>
        ) : (
          // RAG Search Results
          <div className="space-y-2.5">
            {filtered.map((chunk) => (
              <Card key={chunk.id} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-4 hover:border-rose-400/10 transition-all duration-300 rounded-xl animate-fade-in">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div className="flex items-center gap-2">
                    <FileText className="w-3.5 h-3.5 text-rose-300/40" />
                    <span className="text-[10px] text-rose-300/40 font-mono truncate max-w-[220px]">{chunk.source}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant="outline" className="bg-rose-500/[0.04] text-rose-300/35 border-rose-500/[0.06] text-[9px]">{chunk.meta.docType}</Badge>
                    <div className={`px-1.5 py-0.5 rounded text-[10px] font-bold font-mono ${chunk.score >= 0.95 ? "bg-emerald-400/[0.08] text-emerald-300/70" : chunk.score >= 0.9 ? "bg-rose-400/[0.08] text-rose-300/70" : "bg-amber-400/[0.08] text-amber-300/70"}`}>
                      {chunk.score.toFixed(2)}
                    </div>
                  </div>
                </div>
                <p className="text-[12px] text-rose-100/70 leading-relaxed mb-3">
                  <Highlight text={chunk.content} words={query ? query.split(" ").filter((w) => w.length > 2) : chunk.keywords} />
                </p>
                <div className="flex items-center gap-1.5 flex-wrap">
                  {chunk.keywords.map((kw) => (
                    <Badge key={kw} variant="outline" className="bg-rose-400/[0.03] text-rose-300/30 border-rose-400/[0.06] text-[9px]">
                      <Hash className="w-2 h-2 mr-0.5" />{kw}
                    </Badge>
                  ))}
                  <span className="text-[9px] text-rose-300/15 ml-auto">{chunk.meta.year}</span>
                  {chunk.meta.doi && (
                    <a href={`https://doi.org/${chunk.meta.doi}`} target="_blank" rel="noopener noreferrer" className="text-[9px] text-rose-300/40 hover:text-rose-200 flex items-center gap-0.5 transition-colors">
                      DOI <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
