import React, { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";
import {
  Brain,
  Clock,
  Database,
  Zap,
  ChevronDown,
  ChevronRight,
  Lightbulb,
  Target,
  GitBranch,
  Layers,
} from "lucide-react";
import { getAgentMemory } from "@/lib/api";

interface MemoryEntry {
  id: string;
  type: "short-term" | "long-term" | "episodic";
  content: string;
  timestamp: string;
  relevance: number;
}

const DEMO_MEMORY: MemoryEntry[] = [
  { id: "m1", type: "short-term", content: "User queried about beta-amyloid targeting drug candidates for Alzheimer's disease", timestamp: "10:23 AM", relevance: 0.98 },
  { id: "m2", type: "short-term", content: "ChEMBL returned 847 compounds with IC50 values against beta-amyloid (1-42)", timestamp: "10:24 AM", relevance: 0.95 },
  { id: "m3", type: "short-term", content: "Top candidates identified: Lecanemab, Donanemab, Aducanumab", timestamp: "10:25 AM", relevance: 0.97 },
  { id: "m4", type: "long-term", content: "Amyloid hypothesis: Beta-amyloid accumulation is a primary driver of Alzheimer's pathology. Anti-amyloid antibodies have shown clinical benefit in Phase III trials.", timestamp: "Persistent", relevance: 0.92 },
  { id: "m5", type: "long-term", content: "BACE1 inhibitors: First-generation compounds failed due to excessive target inhibition. Partial inhibition (30-50%) is the current recommended approach.", timestamp: "Persistent", relevance: 0.88 },
  { id: "m6", type: "episodic", content: "Previous session: User explored EGFR inhibitors for NSCLC. Identified gefitinib, erlotinib, and osimertinib as top candidates.", timestamp: "Yesterday", relevance: 0.45 },
  { id: "m7", type: "episodic", content: "Previous session: Analyzed tau propagation mechanisms and identified semorinemab as a potential anti-tau therapeutic.", timestamp: "Mar 10", relevance: 0.62 },
];

const PLANNING_STEPS = [
  { id: "s1", label: "Parse Query", description: "Extract disease, target, and drug type from user input", status: "complete" },
  { id: "s2", label: "Database Search", description: "Query ChEMBL, PubMed, and NCBI for relevant data", status: "complete" },
  { id: "s3", label: "RAG Retrieval", description: "Search FAISS and ChromaDB for indexed literature", status: "complete" },
  { id: "s4", label: "Molecular Analysis", description: "Run docking simulations and ADMET predictions", status: "complete" },
  { id: "s5", label: "Synthesis", description: "Combine findings into a coherent recommendation", status: "complete" },
  { id: "s6", label: "Validation", description: "Cross-reference results with known clinical data", status: "active" },
];

const FEW_SHOT_EXAMPLES = [
  {
    query: "Find kinase inhibitors for CML",
    thought: "User wants kinase inhibitors for chronic myeloid leukemia. BCR-ABL is the primary target.",
    action: "Search ChEMBL for BCR-ABL inhibitors with IC50 data",
    result: "Identified imatinib, dasatinib, nilotinib as top candidates",
  },
  {
    query: "Analyze PD-L1 antibodies for melanoma",
    thought: "PD-L1/PD-1 checkpoint inhibitors are key immunotherapy agents for melanoma.",
    action: "Query PubMed for PD-L1 antibody clinical trials in melanoma",
    result: "Pembrolizumab and nivolumab show highest response rates",
  },
];

export default function AgentMemory() {
  const { query: globalQuery } = useGlobalQuery();
  const [expandedSection, setExpandedSection] = useState<string>("memory");
  const [memoryEntries, setMemoryEntries] = useState<any[]>([]);
  const [planSteps, setPlanSteps] = useState<any[]>([]);
  const [fewShotExamples, setFewShotExamples] = useState<any[]>([]);

  useEffect(() => {
    getAgentMemory()
      .then((data) => {
        setMemoryEntries(data.memory_entries || []);
        setPlanSteps(data.plan_steps || []);
        setFewShotExamples(data.few_shot_examples || []);
      })
      .catch(() => {
        setMemoryEntries([]);
        setPlanSteps([]);
        setFewShotExamples([]);
      });
  }, [globalQuery]);

  const memoryTypeConfig = {
    "short-term": { color: "text-pink-400", bg: "bg-pink-500/15", icon: Zap, label: "Short-term" },
    "long-term": { color: "text-violet-400", bg: "bg-violet-500/15", icon: Database, label: "Long-term" },
    episodic: { color: "text-amber-400", bg: "bg-amber-500/15", icon: Clock, label: "Episodic" },
  };

  const sections = [
    { id: "memory", label: "Memory State", icon: Brain, count: memoryEntries.length },
    { id: "planning", label: "Planning Strategy", icon: Target, count: planSteps.length },
    { id: "fewshot", label: "Few-Shot Examples", icon: Lightbulb, count: fewShotExamples.length },
    { id: "architecture", label: "Agent Architecture", icon: GitBranch, count: null },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-white/5">
        <h2 className="text-sm font-semibold text-slate-100 mb-1">
          Agent Memory and Planning
        </h2>
        <p className="text-xs text-slate-400 mb-1">
          Internal state, reasoning strategy, and architecture
        </p>
        {globalQuery && (
          <p className="text-[10px] text-slate-500 mb-3">Active query: "{globalQuery}"</p>
        )}

        <div className="grid grid-cols-4 gap-3">
          {[
            { label: "Short-term", value: memoryEntries.filter((m) => m.type === "short_term" || m.type === "short-term").length.toString(), color: "text-pink-400" },
            { label: "Long-term", value: memoryEntries.filter((m) => m.type === "long_term" || m.type === "long-term").length.toString(), color: "text-violet-400" },
            { label: "Episodic", value: memoryEntries.filter((m) => m.type === "episodic").length.toString(), color: "text-amber-400" },
            { label: "Plan Steps", value: planSteps.length.toString(), color: "text-emerald-400" },
          ].map((stat, idx) => (
            <Card key={idx} className="bg-white/5 backdrop-blur-xl border-white/10 p-3 rounded-xl">
              <p className={`text-lg font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-slate-500">{stat.label}</p>
            </Card>
          ))}
        </div>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-3">
          {sections.map((section) => {
            const isExpanded = expandedSection === section.id;
            const SectionIcon = section.icon;

            return (
              <Card key={section.id} className="bg-white/5 backdrop-blur-xl border-white/10 overflow-hidden rounded-xl">
                <button
                  onClick={() => setExpandedSection(isExpanded ? "" : section.id)}
                  className="w-full flex items-center gap-3 p-4 hover:bg-white/5 transition-colors"
                >
                  <SectionIcon className="w-5 h-5 text-pink-400" />
                  <span className="text-sm font-semibold text-slate-100 flex-1 text-left">
                    {section.label}
                  </span>
                  {section.count !== null && (
                    <Badge variant="outline" className="bg-pink-500/10 text-pink-300 border-pink-500/25 text-xs">
                      {section.count}
                    </Badge>
                  )}
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-slate-500" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-slate-500" />
                  )}
                </button>

                {isExpanded && (
                  <div className="px-4 pb-4 space-y-2">
                    {section.id === "memory" &&
                      memoryEntries.map((entry) => {
                        const normalizedType = entry.type === "short_term" ? "short-term" : entry.type === "long_term" ? "long-term" : entry.type;
                        const config = memoryTypeConfig[normalizedType] || memoryTypeConfig.episodic;
                        const MemIcon = config.icon;
                        return (
                          <div key={entry.id} className="p-3 bg-black/20 rounded-lg border border-white/5">
                            <div className="flex items-center gap-2 mb-1">
                              <MemIcon className={`w-3 h-3 ${config.color}`} />
                              <Badge variant="outline" className={`${config.bg} ${config.color} border-transparent text-xs`}>
                                {config.label}
                              </Badge>
                              <span className="text-xs text-slate-500 ml-auto">
                                {entry.timestamp}
                              </span>
                              <span className="text-xs font-mono text-pink-300">
                                {entry.relevance.toFixed(2)}
                              </span>
                            </div>
                            <p className="text-xs text-slate-300 leading-relaxed">
                              {entry.content}
                            </p>
                          </div>
                        );
                      })}

                    {section.id === "planning" && (
                      <div className="space-y-2">
                        {planSteps.map((step, idx) => (
                          <div key={step.id} className="flex items-start gap-3">
                            <div className="flex flex-col items-center">
                              <div
                                className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                  step.status === "complete"
                                    ? "bg-emerald-500/20 text-emerald-400"
                                    : "bg-pink-500/20 text-pink-400 ring-2 ring-pink-500/30"
                                }`}
                              >
                                {idx + 1}
                              </div>
                              {idx < PLANNING_STEPS.length - 1 && (
                                <div className="w-0.5 h-6 bg-white/10 mt-1" />
                              )}
                            </div>
                            <div className="flex-1 pb-2">
                              <p className="text-sm font-medium text-slate-100">
                                {step.label || step.description}
                              </p>
                              <p className="text-xs text-slate-400">
                                {step.description}
                              </p>
                            </div>
                            <Badge
                              variant="outline"
                              className={`text-xs shrink-0 ${
                                step.status === "complete" || step.status === "completed"
                                  ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/25"
                                  : "bg-pink-500/10 text-pink-400 border-pink-500/25"
                              }`}
                            >
                              {step.status === "complete" || step.status === "completed" ? "Done" : "Active"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    )}

                    {section.id === "fewshot" &&
                      fewShotExamples.map((ex, idx) => (
                        <div key={idx} className="p-3 bg-black/20 rounded-lg border border-white/5 space-y-2">
                          <div className="flex items-center gap-2">
                            <Lightbulb className="w-3 h-3 text-amber-400" />
                            <span className="text-xs font-semibold text-slate-200">
                              Example {idx + 1}
                            </span>
                          </div>
                          <p className="text-xs text-pink-300 font-mono">
                            Q: {ex.query}
                          </p>
                          <p className="text-xs text-fuchsia-300">
                            Thought: {ex.thought || ex.reasoning}
                          </p>
                          <p className="text-xs text-violet-300">
                            Action: {ex.action || ex.tools?.join(", ")}
                          </p>
                          <p className="text-xs text-emerald-300">
                            Result: {ex.result || ex.outcome}
                          </p>
                        </div>
                      ))}

                    {section.id === "architecture" && (
                      <div className="p-4 bg-black/20 rounded-lg border border-white/5">
                        <div className="space-y-3">
                          {[
                            { label: "Framework", value: "LangChain LCEL + ReAct", icon: Layers },
                            { label: "LLM", value: "Gemini Pro (primary) + GPT-4 (fallback)", icon: Brain },
                            { label: "Vector Stores", value: "FAISS (89K chunks) + ChromaDB (64K chunks)", icon: Database },
                            { label: "Embeddings", value: "text-embedding-3-large (3072 dim)", icon: Zap },
                            { label: "Tools", value: "ChEMBL, PubMed, NCBI, Docking Engine, Whisper", icon: Target },
                            { label: "Memory", value: "ConversationBufferWindowMemory (k=10)", icon: Clock },
                          ].map((item, idx) => {
                            const ItemIcon = item.icon;
                            return (
                              <div key={idx} className="flex items-center gap-3">
                                <ItemIcon className="w-4 h-4 text-pink-400 shrink-0" />
                                <span className="text-xs text-slate-500 w-24 shrink-0">
                                  {item.label}
                                </span>
                                <span className="text-xs text-slate-200">
                                  {item.value}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
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
