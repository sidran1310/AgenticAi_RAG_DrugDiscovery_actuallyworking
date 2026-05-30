import React, { useState, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Wrench, CheckCircle2, Clock, AlertCircle, Loader2, ChevronDown, ChevronRight, Activity, Zap, Server, Search, Database, Atom, BookOpen, Filter } from "lucide-react";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";
import { getBackendConfig, manualSearch } from "@/lib/api";

interface ToolCall { id: string; timestamp: string; query: string; status: "success" | "error" | "loading"; duration: string; output: string; }
interface Tool { id: string; name: string; desc: string; status: "active" | "idle" | "error"; calls: number; latency: string; lastUsed: string; recent: ToolCall[]; }

const TOOLS: Tool[] = [
  { id: "chembl", name: "ChEMBL API", desc: "Chemical database for drug-like molecules", status: "active", calls: 47, latency: "320ms", lastUsed: "2 min ago",
    recent: [
      { id: "c1", timestamp: "10:24 AM", query: "CHEMBL4296 IC50 compounds", status: "success", duration: "280ms", output: "847 compounds found" },
      { id: "c2", timestamp: "10:20 AM", query: "BACE1 inhibitors selectivity", status: "success", duration: "350ms", output: "23 selective inhibitors" },
    ] },
  { id: "pubmed", name: "PubMed / NCBI", desc: "Biomedical literature search", status: "active", calls: 62, latency: "450ms", lastUsed: "1 min ago",
    recent: [
      { id: "p1", timestamp: "10:25 AM", query: "Alzheimer beta-amyloid trial 2024-2026", status: "success", duration: "420ms", output: "15 publications" },
    ] },
  { id: "pdb", name: "PDB / Docking", desc: "Protein structure & molecular docking", status: "active", calls: 18, latency: "1.2s", lastUsed: "5 min ago",
    recent: [
      { id: "d1", timestamp: "10:26 AM", query: "6SZF docking: lecanemab", status: "success", duration: "1.4s", output: "Score: -8.7 kcal/mol" },
    ] },
  { id: "rag", name: "RAG Pipeline", desc: "FAISS + ChromaDB retrieval", status: "active", calls: 89, latency: "180ms", lastUsed: "30s ago",
    recent: [
      { id: "r1", timestamp: "10:26 AM", query: "amyloid-beta aggregation inhibitors", status: "success", duration: "150ms", output: "12 chunks, top: 0.94" },
    ] },
  { id: "llm", name: "Gemini Pro LLM", desc: "Reasoning & synthesis engine", status: "active", calls: 34, latency: "2.1s", lastUsed: "1 min ago",
    recent: [
      { id: "l1", timestamp: "10:26 AM", query: "Synthesize Alzheimer's findings", status: "success", duration: "2.3s", output: "3 top candidates generated" },
    ] },
];

export default function ToolPanel() {
  const { query: globalQuery, results } = useGlobalQuery();
  const [expanded, setExpanded] = useState<string | null>("chembl");
  const [configTools, setConfigTools] = useState<any[]>([]);
  const [manualSearchType, setManualSearchType] = useState<'pubmed' | 'chembl' | 'pubchem' | 'pdb'>('pubmed');
  const [manualQuery, setManualQuery] = useState('');
  const [manualResults, setManualResults] = useState<any>(null);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualFilters, setManualFilters] = useState<any>({});

  const normalizeTool = (tool: any, index: number) => {
    if (tool.name && tool.recent) return tool;
    return {
      id: tool.id || tool.tool || `tool-${index}`,
      name: tool.name || tool.tool || "Tool",
      desc: tool.desc || tool.result || "Execution record",
      status: tool.status === "success" ? "active" : tool.status || "idle",
      calls: 1,
      latency: tool.time ? `${tool.time}s` : "n/a",
      lastUsed: "Current query",
      recent: [{
        id: `call-${index}`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        query: tool.input || "Current query",
        status: tool.status === "error" ? "error" : "success",
        duration: tool.time ? `${tool.time}s` : "n/a",
        output: tool.result || tool.status || "Completed",
      }],
    };
  };

  const handleManualSearch = async () => {
    if (!manualQuery.trim()) return;

    setManualLoading(true);
    try {
      const results = await manualSearch(manualSearchType, manualQuery, manualFilters);
      setManualResults(results);
    } catch (error) {
      console.error('Manual search failed:', error);
      setManualResults({ error: 'Search failed' });
    } finally {
      setManualLoading(false);
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

  const toolsUsed = ((results.tools?.length ? results.tools : results.toolsUsed) || configTools).map(normalizeTool);
  const manualResultItems = manualResults ? (
    Array.isArray(manualResults.data)
      ? manualResults.data
      : Array.isArray(manualResults.results)
      ? manualResults.results
      : manualResults.results
      ? [manualResults.results]
      : []
  ) : [];

  useEffect(() => {
    if (globalQuery) {
      setExpanded("chembl");
    }
  }, [globalQuery]);

  useEffect(() => {
    if (results.tools?.length || results.toolsUsed?.length) return;
    getBackendConfig()
      .then((config) => {
        const stats = Object.entries(config.tool_stats || {}).map(([id, stat]: [string, any]) => ({
          id,
          name: id,
          desc: `${stat.callCount || 0} recorded calls`,
          status: stat.status || "idle",
          calls: stat.callCount || 0,
          latency: stat.avgLatency || "n/a",
          lastUsed: stat.lastCalled || "Never",
          recent: [{
            id: `${id}-latest`,
            timestamp: stat.lastCalled || "Never",
            query: "Backend telemetry",
            status: "success",
            duration: stat.avgLatency || "n/a",
            output: `${id} ${stat.status || "ready"}`,
          }],
        }));
        setConfigTools(stats);
      })
      .catch(() => setConfigTools([]));
  }, [results.tools?.length, results.toolsUsed?.length]);

  const statusCfg = {
    active: { color: "text-emerald-300/70", bg: "bg-emerald-400/[0.08]", label: "Active", Icon: CheckCircle2 },
    idle: { color: "text-rose-300/40", bg: "bg-rose-400/[0.06]", label: "Idle", Icon: Clock },
    error: { color: "text-red-300/70", bg: "bg-red-400/[0.08]", label: "Error", Icon: AlertCircle },
    success: { color: "text-emerald-300/70", bg: "bg-emerald-400/[0.08]", label: "Success", Icon: CheckCircle2 },
  };

  const callIcon = { success: <CheckCircle2 className="w-3 h-3 text-emerald-300/60" />, error: <AlertCircle className="w-3 h-3 text-red-300/60" />, loading: <Loader2 className="w-3 h-3 text-rose-300/50 animate-spin" /> };

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-rose-500/[0.04]">
        <h2 className="text-[13px] font-semibold text-rose-100/90 mb-0.5">Tool Integration Panel</h2>
        <p className="text-[10px] text-rose-300/30 mb-1">Real-time API execution monitoring</p>
        {globalQuery && (
          <p className="text-[10px] text-rose-400/40">Current query: "{globalQuery}"</p>
        )}
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: "Total Calls", value: toolsUsed.reduce((sum: number, t: any) => sum + (t.calls || 1), 0).toString(), icon: Zap, color: "text-rose-300/70" },
            { label: "Active Tools", value: toolsUsed.filter((t: any) => t.status === "active").length.toString(), icon: Server, color: "text-emerald-300/70" },
            { label: "Avg Latency", value: "580ms", icon: Activity, color: "text-fuchsia-300/70" },
          ].map((s, i) => (
            <Card key={i} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-3 rounded-xl">
              <s.icon className={`w-3.5 h-3.5 ${s.color} mb-1`} />
              <p className="text-lg font-bold text-rose-100/85">{s.value}</p>
              <p className="text-[10px] text-rose-300/25">{s.label}</p>
            </Card>
          ))}
        </div>
      </div>

      {/* Manual Search Section */}
      <div className="p-4 border-b border-rose-500/[0.06]">
        <h3 className="text-sm font-semibold text-rose-100/80 mb-3 flex items-center gap-2">
          <Search className="w-4 h-4" />
          Manual Search
        </h3>
        <div className="space-y-3">
          <div className="flex gap-2">
            <Select value={manualSearchType} onValueChange={(value: any) => setManualSearchType(value)}>
              <SelectTrigger className="flex-1 bg-rose-500/[0.03] border-rose-500/[0.06] text-rose-100/80">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pubmed">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4" />
                    PubMed
                  </div>
                </SelectItem>
                <SelectItem value="chembl">
                  <div className="flex items-center gap-2">
                    <Atom className="w-4 h-4" />
                    ChEMBL
                  </div>
                </SelectItem>
                <SelectItem value="pubchem">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    PubChem
                  </div>
                </SelectItem>
                <SelectItem value="pdb">
                  <div className="flex items-center gap-2">
                    <Server className="w-4 h-4" />
                    PDB
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex gap-2">
            <Input
              placeholder={`Search ${manualSearchType}...`}
              value={manualQuery}
              onChange={(e) => setManualQuery(e.target.value)}
              className="flex-1 bg-rose-500/[0.03] border-rose-500/[0.06] text-rose-100/80 placeholder-rose-300/25"
              onKeyPress={(e) => e.key === 'Enter' && handleManualSearch()}
            />
            <Button
              onClick={handleManualSearch}
              disabled={manualLoading || !manualQuery.trim()}
              className="bg-rose-500/20 hover:bg-rose-500/30 border-rose-500/30"
            >
              {manualLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </Button>
          </div>
          {manualResults && (
            <Card className="bg-rose-500/[0.03] border-rose-500/[0.06] p-3">
              <div className="text-xs text-rose-300/60">
                {manualResults.error ? (
                  <div className="text-red-400">{manualResults.error}</div>
                ) : (
                  <div>
                    Found {manualResults.count || manualResults.length || manualResultItems.length || 0} results
                    {manualResultItems.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {manualResultItems.slice(0, 3).map((item: any, i: number) => (
                          <div key={i} className="text-rose-100/60 truncate">
                            {item.title || item.name || item.id || item.pmid || item.cid}
                          </div>
                        ))}
                        {manualResultItems.length > 3 && (
                          <div className="text-rose-300/40">...and {manualResultItems.length - 3} more</div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-2.5">
          {toolsUsed.map((tool: any, index: number) => {
            const st = statusCfg[tool.status] || statusCfg.active;
            const isExp = expanded === tool.id;
            return (
              <Card key={index} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] overflow-hidden rounded-xl hover:border-rose-400/10 transition-all duration-300">
                <button onClick={() => setExpanded(isExp ? null : tool.id)} className="w-full flex items-center gap-3 p-3.5 hover:bg-rose-500/[0.02] transition-colors">
                  <div className={`w-8 h-8 rounded-lg ${st.bg} flex items-center justify-center`}>
                    <Wrench className={`w-4 h-4 ${st.color}`} />
                  </div>
                  <div className="flex-1 text-left">
                    <div className="flex items-center gap-2">
                      <h3 className="text-[12px] font-semibold text-rose-100/80">{tool.name}</h3>
                      <Badge variant="outline" className={`${st.bg} ${st.color} border-transparent text-[9px]`}>
                        <st.Icon className="w-2.5 h-2.5 mr-0.5" />{st.label}
                      </Badge>
                    </div>
                    <p className="text-[10px] text-rose-300/25">{tool.desc}</p>
                  </div>
                  {isExp ? <ChevronDown className="w-3.5 h-3.5 text-rose-300/20 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-rose-300/20 shrink-0" />}
                </button>
                {isExp && (
                  <div className="px-3.5 pb-3.5 space-y-1.5">
                    {tool.recent.map((call: ToolCall) => (
                      <div key={call.id} className="flex items-center gap-2 rounded-lg bg-rose-500/[0.03] px-2.5 py-2">
                        {callIcon[call.status]}
                        <span className="text-[10px] text-rose-300/40 flex-1 truncate">{call.output}</span>
                        <span className="text-[10px] text-rose-300/25">{call.duration}</span>
                      </div>
                    ))}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
