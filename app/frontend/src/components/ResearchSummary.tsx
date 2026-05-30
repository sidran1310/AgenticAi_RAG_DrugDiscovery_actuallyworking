import React, { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { BookOpen, Calendar, Users, ArrowUpRight, Star, Filter, TrendingUp, FileText, BarChart3, Microscope, GitBranch, List, Search, Loader2, Database, Atom, Server } from "lucide-react";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";
import PaperGraph from "./PaperGraph";
import { searchPapers, advancedSearch } from "@/lib/api";

interface Paper {
  id: string; title: string; authors: string; journal: string; date: string;
  abstract: string; aiSummary: string; source: string; score: number; citations: number; doi?: string; tags: string[];
}

const PAPERS: Paper[] = [
  { id: "1", title: "Lecanemab in Early Alzheimer's Disease: CLARITY AD Trial", authors: "van Dyck CH, Swanson CJ, Aisen P, et al.", journal: "NEJM", date: "2025-01-15", abstract: "Lecanemab reduced amyloid markers and slowed cognitive decline by 27% vs placebo at 18 months.", aiSummary: "27% slowing of CDR-SB decline. 68% achieved amyloid-negative status. ARIA in 21.3% mostly asymptomatic.", source: "PubMed", score: 98, citations: 1247, doi: "10.1056/NEJMoa2212948", tags: ["Phase III", "Lecanemab", "Amyloid-B"] },
  { id: "2", title: "Donanemab TRAILBLAZER-ALZ 2 Trial Results", authors: "Sims JR, Zimmer JA, Evans CD, et al.", journal: "JAMA", date: "2025-02-10", abstract: "Donanemab significantly slowed clinical progression at 76 weeks.", aiSummary: "35% slowing of clinical decline. 80% amyloid clearance by 12 months.", source: "PubMed", score: 96, citations: 892, doi: "10.1001/jama.2023.13239", tags: ["Phase III", "Donanemab", "Tau"] },
  { id: "3", title: "Next-Generation BACE1 Inhibitors: Path Forward", authors: "Vassar R, Bhatt DK, Chen Y, et al.", journal: "Nat Rev Drug Discov", date: "2025-01-30", abstract: "Analysis of clinical failures and strategies for safer next-gen compounds.", aiSummary: "Proposes partial BACE1 inhibition (30-50%) as optimal strategy.", source: "PubMed", score: 94, citations: 234, tags: ["Review", "BACE1", "Drug Design"] },
  { id: "4", title: "Cryo-EM Structure of AB42 Fibrils", authors: "Yang Y, Zhang S, et al.", journal: "Science", date: "2024-11-20", abstract: "High-resolution structures reveal novel binding pockets.", aiSummary: "2.1A resolution. 3 novel druggable pockets. 2 compounds showed >80% aggregation inhibition.", source: "NCBI", score: 97, citations: 567, doi: "10.1126/science.adq1234", tags: ["Cryo-EM", "Drug Design", "Amyloid-B"] },
  { id: "5", title: "Multi-Target Drug Design for Alzheimer's", authors: "Cummings J, Lee G, et al.", journal: "Alzheimer's & Dementia", date: "2025-03-01", abstract: "Dual-target approach combining anti-amyloid and anti-tau mechanisms.", aiSummary: "5 multi-target compounds in preclinical development reviewed.", source: "PubMed", score: 91, citations: 89, tags: ["Multi-Target", "Tau", "Amyloid-B"] },
];

function PaperCard({ paper }: { paper: Paper }) {
  const [showAI, setShowAI] = useState(false);
  const scoreColor = paper.score >= 95 ? "text-emerald-300" : paper.score >= 90 ? "text-rose-300" : "text-amber-300";

  return (
    <Card className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-4 hover:border-rose-400/15 transition-all duration-300 rounded-xl animate-fade-in">
      <div className="flex items-start justify-between gap-3 mb-2">
        <Badge variant="outline" className="bg-rose-400/[0.06] text-rose-300/60 border-rose-400/10 text-[10px]">{paper.source}</Badge>
        <div className="flex items-center gap-1.5">
          <Star className="w-3 h-3 text-amber-300/50" />
          <span className={`text-[13px] font-bold font-mono ${scoreColor}`}>{paper.score}</span>
        </div>
      </div>
      <h3 className="text-[13px] font-semibold text-rose-100/85 mb-1 leading-snug">{paper.title}</h3>
      <p className="text-[11px] text-rose-300/35 mb-2">{paper.authors}</p>
      <div className="flex items-center gap-3 text-[10px] text-rose-300/25 mb-3">
        <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{paper.journal}</span>
        <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{paper.date}</span>
        <span className="flex items-center gap-1"><Users className="w-3 h-3" />{paper.citations} cit.</span>
      </div>
      <div className="mb-3">
        <button onClick={() => setShowAI(!showAI)} className="flex items-center gap-1.5 text-[10px] text-rose-300/50 hover:text-rose-200/70 transition-colors mb-2">
          <TrendingUp className="w-3 h-3" />{showAI ? "Hide AI Summary" : "Show AI Summary"}
        </button>
        {showAI && (
          <div className="p-3 bg-rose-400/[0.04] border border-rose-400/[0.08] rounded-xl">
            <p className="text-[11px] text-rose-100/70 leading-relaxed">{paper.aiSummary}</p>
          </div>
        )}
      </div>
      <div className="flex flex-wrap gap-1.5 mb-3">
        {paper.tags.map((t) => (
          <Badge key={t} variant="outline" className="bg-rose-500/[0.03] text-rose-300/35 border-rose-500/[0.06] text-[10px]">{t}</Badge>
        ))}
      </div>
      {paper.doi && (
        <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-[10px] text-rose-300/50 hover:text-rose-200 transition-colors">
          View Paper <ArrowUpRight className="w-3 h-3" />
        </a>
      )}
    </Card>
  );
}

export default function ResearchSummary() {
  const { query: globalQuery } = useGlobalQuery();
  const [apiPapers, setApiPapers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState("relevance");
  const [filterSrc, setFilterSrc] = useState("all");
  const [view, setView] = useState<"graph" | "list">("graph");
  const [advancedQuery, setAdvancedQuery] = useState("");
  const [advancedDatabases, setAdvancedDatabases] = useState<string[]>(['pubmed', 'chembl', 'pubchem']);
  const [advancedResults, setAdvancedResults] = useState<any>(null);
  const [advancedLoading, setAdvancedLoading] = useState(false);

  const handleAdvancedSearch = async () => {
    if (!advancedQuery.trim()) return;

    setAdvancedLoading(true);
    try {
      const results = await advancedSearch(advancedQuery, advancedDatabases);
      setAdvancedResults(results);
    } catch (error) {
      console.error('Advanced search failed:', error);
      setAdvancedResults({ error: 'Search failed' });
    } finally {
      setAdvancedLoading(false);
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

  useEffect(() => {
    if (!globalQuery) return;
    let cancelled = false;
    setLoading(true);
    searchPapers(globalQuery, 10)
      .then((data) => {
        if (!cancelled) setApiPapers(data.papers || []);
      })
      .catch(() => {
        if (!cancelled) setApiPapers([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [globalQuery]);

  const normalizePaper = (paper: any): Paper => ({
    id: paper.id,
    title: paper.title,
    authors: paper.authors,
    journal: paper.journal,
    date: paper.date,
    abstract: paper.abstract,
    aiSummary: paper.aiSummary || paper.ai_summary || paper.abstract?.slice(0, 220) || "Summary unavailable",
    source: paper.source || "PubMed",
    score: paper.score || paper.credibilityScore || paper.credibility_score || 80,
    citations: paper.citations || paper.citationCount || paper.citation_count || 0,
    doi: paper.doi,
    tags: paper.tags || [],
  });

  const papers = (apiPapers.length ? apiPapers.map(normalizePaper) : []);
  const filtered = papers.filter((p) => filterSrc === "all" || p.source === filterSrc)
    .sort((a, b) => sortBy === "date" ? b.date.localeCompare(a.date) : sortBy === "citations" ? b.citations - a.citations : b.score - a.score);

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-rose-500/[0.04]">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-[13px] font-semibold text-rose-100/90 mb-0.5">Research Papers</h2>
            <p className="text-[10px] text-rose-300/30">AI-curated from PubMed, NCBI, and indexed literature{globalQuery ? ` for "${globalQuery}"` : ''}</p>
          </div>
          <div className="flex items-center gap-0.5 bg-rose-500/[0.04] border border-rose-500/[0.06] rounded-xl p-0.5">
            <Button size="sm" variant="ghost" onClick={() => setView("graph")}
              className={`h-7 px-3 text-[10px] rounded-lg ${view === "graph" ? "bg-rose-400/10 text-rose-300/80" : "text-rose-300/30 hover:text-rose-300/50"}`}>
              <GitBranch className="w-3 h-3 mr-1" />Graph
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setView("list")}
              className={`h-7 px-3 text-[10px] rounded-lg ${view === "list" ? "bg-rose-400/10 text-rose-300/80" : "text-rose-300/30 hover:text-rose-300/50"}`}>
              <List className="w-3 h-3 mr-1" />List
            </Button>
          </div>
        </div>

        {/* Advanced Search Section */}
        <div className="mb-4 p-3 bg-rose-500/[0.03] border border-rose-500/[0.06] rounded-xl">
          <h3 className="text-sm font-semibold text-rose-100/80 mb-3 flex items-center gap-2">
            <Search className="w-4 h-4" />
            Advanced Multi-Database Search
          </h3>
          <div className="space-y-3">
            <div className="flex gap-2">
              <Input
                placeholder="Search across multiple databases..."
                value={advancedQuery}
                onChange={(e) => setAdvancedQuery(e.target.value)}
                className="flex-1 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-100 placeholder-rose-300/25"
                onKeyPress={(e) => e.key === 'Enter' && handleAdvancedSearch()}
              />
              <Button
                onClick={handleAdvancedSearch}
                disabled={advancedLoading || !advancedQuery.trim()}
                className="bg-rose-500/20 hover:bg-rose-500/30 border-rose-500/30"
              >
                {advancedLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {['pubmed', 'chembl', 'pubchem', 'pdb'].map((db) => (
                <Button
                  key={db}
                  size="sm"
                  variant={advancedDatabases.includes(db) ? "default" : "outline"}
                  onClick={() => {
                    setAdvancedDatabases(prev =>
                      prev.includes(db)
                        ? prev.filter(d => d !== db)
                        : [...prev, db]
                    );
                  }}
                  className={`h-7 px-2 text-[10px] ${
                    advancedDatabases.includes(db)
                      ? "bg-rose-500/20 text-rose-100 border-rose-500/30"
                      : "bg-rose-500/[0.04] text-rose-300/60 border-rose-500/[0.06] hover:bg-rose-500/[0.08]"
                  }`}
                >
                  {getDatabaseIcon(db)}
                  <span className="ml-1 capitalize">{db}</span>
                </Button>
              ))}
            </div>
            {advancedResults && (
              <Card className="bg-rose-500/[0.03] border-rose-500/[0.06] p-3">
                <div className="text-xs text-rose-300/60">
                  {advancedResults.error ? (
                    <div className="text-red-400">{advancedResults.error}</div>
                  ) : (
                    <div>
                      Advanced search completed across {advancedDatabases.length} databases
                      {advancedResults.cross_references && advancedResults.cross_references.length > 0 && (
                        <div className="mt-2">
                          <div className="font-semibold text-rose-100/80 mb-1">Cross-references found:</div>
                          <div className="space-y-1">
                            {advancedResults.cross_references.map((ref: any, idx: number) => (
                              <div key={idx} className="flex items-center gap-2">
                                {getDatabaseIcon(ref.source?.toLowerCase().includes('chembl') ? 'chembl' : ref.source?.toLowerCase().includes('pubchem') ? 'pubchem' : ref.source?.toLowerCase().includes('pubmed') ? 'pubmed' : 'pdb')}
                                <span className="capitalize">{ref.source || ref.type}</span>
                                <Badge variant="outline" className="bg-rose-500/10 text-rose-300/70 border-rose-500/20 text-[9px]">
                                  {ref.match_type || ref.confidence || 'match'}
                                </Badge>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </Card>
            )}
          </div>
        </div>

        <div className="grid grid-cols-4 gap-3 mb-3">
          {[
            { label: "Papers Found", value: loading ? "..." : papers.length.toString(), icon: FileText, color: "text-rose-300/70" },
            { label: "Avg Credibility", value: papers.length ? (papers.reduce((a, p) => a + p.score, 0) / papers.length).toFixed(1) : "0.0", icon: Star, color: "text-amber-300/70" },
            { label: "Total Citations", value: papers.reduce((a, p) => a + p.citations, 0).toLocaleString(), icon: BarChart3, color: "text-fuchsia-300/70" },
            { label: "Sources", value: new Set(papers.map((p) => p.source)).size.toString(), icon: Microscope, color: "text-emerald-300/70" },
          ].map((s, i) => (
            <Card key={i} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-3 rounded-xl">
              <s.icon className={`w-3.5 h-3.5 ${s.color} mb-1`} />
              <p className="text-lg font-bold text-rose-100/85">{s.value}</p>
              <p className="text-[10px] text-rose-300/25">{s.label}</p>
            </Card>
          ))}
        </div>

        {view === "list" && (
          <div className="flex items-center gap-3">
            <Filter className="w-3.5 h-3.5 text-rose-300/25" />
            <Select value={filterSrc} onValueChange={setFilterSrc}>
              <SelectTrigger className="w-[110px] h-7 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-300/60 text-[10px] rounded-lg">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1322] border-rose-500/[0.08]">
                <SelectItem value="all" className="text-rose-200/60 text-[10px]">All Sources</SelectItem>
                <SelectItem value="PubMed" className="text-rose-200/60 text-[10px]">PubMed</SelectItem>
                <SelectItem value="NCBI" className="text-rose-200/60 text-[10px]">NCBI</SelectItem>
              </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-[110px] h-7 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-300/60 text-[10px] rounded-lg">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-[#1A1322] border-rose-500/[0.08]">
                <SelectItem value="relevance" className="text-rose-200/60 text-[10px]">Relevance</SelectItem>
                <SelectItem value="date" className="text-rose-200/60 text-[10px]">Date</SelectItem>
                <SelectItem value="citations" className="text-rose-200/60 text-[10px]">Citations</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-[10px] text-rose-300/20 ml-auto">{filtered.length} papers</span>
          </div>
        )}
      </div>

      {view === "graph" ? (
        <div className="flex-1 overflow-hidden bg-[#110D18]">
          <PaperGraph query={globalQuery} />
        </div>
      ) : (
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-3">
            {filtered.length ? filtered.map((p) => <PaperCard key={p.id} paper={p} />) : (
              <Card className="bg-rose-500/[0.03] border-rose-500/[0.06] p-6 text-center rounded-xl">
                <p className="text-[13px] text-rose-300/45">{loading ? "Searching PubMed..." : "No papers loaded yet"}</p>
              </Card>
            )}
          </div>
        </ScrollArea>
      )}
    </div>
  );
}
