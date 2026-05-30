import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import AgentChat from "@/components/AgentChat";
import ToolPanel from "@/components/ToolPanel";
import RAGExplorer from "@/components/RAGExplorer";
import MolecularViewer from "@/components/MolecularViewer";
import ResearchSummary from "@/components/ResearchSummary";
import AgentMemory from "@/components/AgentMemory";
import PaperGraph from "@/components/PaperGraph";
import {
  MessageSquare,
  Wrench,
  Database,
  Atom,
  FileText,
  Brain,
  FlaskConical,
  Sparkles,
  Github,
  ExternalLink,
} from "lucide-react";
import { SearchProvider } from "@/lib/SearchContext";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";

const NAV_ITEMS = [
  { id: "chat", label: "Agent Chat", icon: MessageSquare, description: "ReAct reasoning interface" },
  { id: "tools", label: "Tools", icon: Wrench, description: "API integrations" },
  { id: "rag", label: "RAG Explorer", icon: Database, description: "Knowledge base" },
  { id: "molecular", label: "Molecules", icon: Atom, description: "Compound viewer" },
  { id: "papers", label: "Paper Graph", icon: FlaskConical, description: "Research network" },
  { id: "research", label: "Research", icon: FileText, description: "Paper summaries" },
  { id: "memory", label: "Memory", icon: Brain, description: "Agent internals" },
];

export default function Index() {
  const [activePanel, setActivePanel] = useState("chat");


  return (
    <div className="premium-app h-screen flex bg-[#FFF9F5] text-stone-900 overflow-hidden">
      {/* Sidebar */}
      <div className="w-16 bg-[#0B1120] border-r border-slate-800 flex flex-col items-center py-4 shrink-0">
        {/* Logo */}
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center mb-6">
          <FlaskConical className="w-5 h-5 text-white" />
        </div>

        {/* Nav Items */}
        <nav className="flex-1 flex flex-col items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const isActive = activePanel === item.id;
            return (
              <Tooltip key={item.id} delayDuration={0}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => setActivePanel(item.id)}
                    className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all ${
                      isActive
                        ? "bg-pink-600/20 text-pink-400 ring-1 ring-pink-500/30"
                        : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/50"
                    }`}
                  >
                    <item.icon className="w-5 h-5" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right" className="bg-slate-800 border-slate-700 text-slate-200">
                  <p className="font-semibold text-xs">{item.label}</p>
                  <p className="text-xs text-slate-400">{item.description}</p>
                </TooltipContent>
              </Tooltip>
            );
          })}
        </nav>

        {/* Bottom */}
        <div className="flex flex-col items-center gap-2">
          <Tooltip delayDuration={0}>
            <TooltipTrigger asChild>
              <div className="w-8 h-8 rounded-full bg-emerald-500/20 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-emerald-400" />
              </div>
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-slate-800 border-slate-700 text-slate-200">
              <p className="text-xs">Agent Status: Active</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="h-12 bg-[#0B1120]/80 backdrop-blur-sm border-b border-slate-800 flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-3">
            <h1 className="text-sm font-bold text-slate-100">
              Drug Discovery ReAct Agent
            </h1>
            <Badge variant="outline" className="bg-cyan-500/10 text-cyan-400 border-cyan-500/30 text-xs">
              Compound AI
            </Badge>
            <Badge variant="outline" className="bg-violet-500/10 text-violet-400 border-violet-500/30 text-xs">
              RAG-Enhanced
            </Badge>
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-400 border-emerald-500/30 text-xs">
              Agentic
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="bg-slate-800/50 text-slate-400 border-slate-700 text-xs font-mono">
              LangChain + LCEL
            </Badge>
            <Badge variant="outline" className="bg-slate-800/50 text-slate-400 border-slate-700 text-xs font-mono">
              FAISS + ChromaDB
            </Badge>
            <Badge variant="outline" className="bg-pink-500/10 text-pink-400 border-pink-500/30 text-xs font-mono">
              ReAct Agent
            </Badge>
          </div>
        </header>

        {/* Panel Content - all mounted, CSS hidden to preserve state */}
        <main className="flex-1 overflow-hidden relative">
          <SearchProvider>
            <div className={activePanel === "chat" ? "h-full" : "hidden"}><AgentChat /></div>
            <div className={activePanel === "tools" ? "h-full" : "hidden"}><ToolPanel /></div>
            <div className={activePanel === "rag" ? "h-full" : "hidden"}><RAGExplorer /></div>
            <div className={activePanel === "molecular" ? "h-full" : "hidden"}><MolecularViewer /></div>
            <div className={activePanel === "papers" ? "h-full" : "hidden"}><PaperGraph /></div>
            <div className={activePanel === "research" ? "h-full" : "hidden"}><ResearchSummary /></div>
            <div className={activePanel === "memory" ? "h-full" : "hidden"}><AgentMemory /></div>
          </SearchProvider>
        </main>

        {/* Bottom Status Bar */}
        <footer className="h-8 bg-[#0B1120]/80 border-t border-slate-800 flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <div className="w-1.5 h-1.5 rounded-full bg-pink-400" />
              5 Tools Connected
            </span>
            <span>FAISS: 89,230 chunks</span>
            <span>ChromaDB: 64,100 chunks</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span>Gemini Pro • GPT-4 • Mistral</span>
            <span className="text-slate-600">|</span>
            <span>ReAct Framework v2.1</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
