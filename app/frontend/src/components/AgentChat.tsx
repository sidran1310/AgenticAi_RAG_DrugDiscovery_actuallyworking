import React, { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Brain,
  Wrench,
  Eye,
  CheckCircle2,
  Send,
  Loader2,
  Sparkles,
  Bot,
  User,
  ChevronDown,
  ChevronRight,
  Plus,
  Copy,
  RefreshCw,
  Pencil,
  Trash2,
  Check,
  MessageSquare,
} from "lucide-react";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";
import { sendChatMessage, searchStructures } from "@/lib/api";

interface ReActStep {
  type: "thought" | "action" | "observation" | "answer";
  content: string;
  tool?: string;
  args?: Record<string, string>;
  timestamp: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "agent";
  content: string;
  steps?: ReActStep[];
  timestamp: string;
  error?: string;
}

interface ChatSession {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: string;
}

const DEFAULT_SESSION: ChatSession = {
  id: "s1",
  name: "New Research Chat",
  messages: [],
  createdAt: "Today",
};

const stepConfig = {
  thought: {
    icon: Brain,
    color: "text-fuchsia-300",
    bg: "bg-fuchsia-400/[0.06]",
    border: "border-fuchsia-400/[0.1]",
    label: "Thought",
    badgeCls: "bg-fuchsia-400/10 text-fuchsia-300/80 border-fuchsia-400/15",
  },
  action: {
    icon: Wrench,
    color: "text-rose-300",
    bg: "bg-rose-400/[0.06]",
    border: "border-rose-400/[0.1]",
    label: "Action",
    badgeCls: "bg-rose-400/10 text-rose-300/80 border-rose-400/15",
  },
  observation: {
    icon: Eye,
    color: "text-amber-300",
    bg: "bg-amber-400/[0.06]",
    border: "border-amber-400/[0.1]",
    label: "Observation",
    badgeCls: "bg-amber-400/10 text-amber-300/80 border-amber-400/15",
  },
  answer: {
    icon: CheckCircle2,
    color: "text-emerald-300",
    bg: "bg-emerald-400/[0.06]",
    border: "border-emerald-400/[0.1]",
    label: "Answer",
    badgeCls: "bg-emerald-400/10 text-emerald-300/80 border-emerald-400/15",
  },
};

function StepCard({ step }: { step: ReActStep }) {
  const [open, setOpen] = useState(step.type === "answer");
  const cfg = stepConfig[step.type];
  const Icon = cfg.icon;

  return (
    <div className={`border ${cfg.border} ${cfg.bg} rounded-xl overflow-hidden backdrop-blur-sm transition-all duration-300 animate-fade-in`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-white/[0.02] transition-colors"
      >
        <Icon className={`w-3.5 h-3.5 ${cfg.color} shrink-0`} />
        <Badge variant="outline" className={`${cfg.badgeCls} text-[10px] font-mono shrink-0`}>
          {cfg.label}
        </Badge>
        {step.tool && (
          <Badge variant="outline" className="bg-rose-500/[0.04] text-rose-300/50 border-rose-500/[0.06] text-[10px] font-mono shrink-0">
            {step.tool}
          </Badge>
        )}
        <span className="text-rose-300/30 text-[11px] truncate flex-1 text-left">
          {step.content.substring(0, 70)}...
        </span>
        {open ? <ChevronDown className="w-3.5 h-3.5 text-rose-300/20 shrink-0" /> : <ChevronRight className="w-3.5 h-3.5 text-rose-300/20 shrink-0" />}
      </button>
      {open && (
        <div className="px-3.5 pb-3.5 pt-1">
          {step.args && (
            <div className="mb-2.5 p-2 bg-black/20 rounded-lg border border-rose-500/[0.04]">
              <p className="text-[10px] font-mono text-rose-300/25 mb-1">Arguments:</p>
              {Object.entries(step.args).map(([k, v]) => (
                <div key={k} className="flex gap-2 text-[11px] font-mono">
                  <span className="text-rose-300/60">{k}:</span>
                  <span className="text-rose-100/70">{v}</span>
                </div>
              ))}
            </div>
          )}
          <p className="text-[13px] text-rose-100/80 leading-relaxed whitespace-pre-wrap">
            {step.content}
          </p>
        </div>
      )}
    </div>
  );
}

interface AgentChatProps {
  globalQuery?: string;
}

export default function AgentChat({ globalQuery }: AgentChatProps) {
  const { query, setQuery, isProcessing: globalProcessing, setIsProcessing, results, setResults, setAutoDock } = useGlobalQuery();
  const [sessions, setSessions] = useState<ChatSession[]>(() => {
    try {
      const saved = localStorage.getItem("bioagent.chat.sessions");
      return saved ? JSON.parse(saved) : [DEFAULT_SESSION];
    } catch {
      return [DEFAULT_SESSION];
    }
  });
  const [activeSessionId, setActiveSessionId] = useState("s1");
  const [input, setInput] = useState("");
  const [isLocalProcessing, setIsLocalProcessing] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((s) => s.id === activeSessionId);
  const messages = activeSession?.messages || [];

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages]);

  useEffect(() => {
    localStorage.setItem("bioagent.chat.sessions", JSON.stringify(sessions));
  }, [sessions]);

  useEffect(() => {
    if (globalQuery?.trim()) setInput(globalQuery);
  }, [globalQuery]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLocalProcessing) return;
    setIsLocalProcessing(true);
    setQuery(input.trim());
    setIsProcessing(true);
    const submittedInput = input.trim();
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
    setSessions((p) => p.map((s) => s.id === activeSessionId ? { ...s, messages: [...s.messages, userMsg] } : s));
    setInput("");

    try {
      const data = await sendChatMessage(submittedInput, "default");
      const chatText = data.chat || data.response || "No answer was returned.";
      const thoughtProcess = Array.isArray(data.thought_process) ? data.thought_process : [];
      const actions = Array.isArray(data.actions) ? data.actions : [];
      const observations = Array.isArray(data.observations) ? data.observations : [];

      const agentMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "agent",
        content: chatText,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        steps: [
          ...thoughtProcess.map((step: any) => ({
            type: "thought" as const,
            content: step.content,
            timestamp: step.timestamp,
          })),
          ...actions.map((action: any) => ({
            type: "action" as const,
            content: action.result,
            tool: action.tool,
            timestamp: new Date().toISOString(),
          })),
          ...observations.map((obs: any) => ({
            type: "observation" as const,
            content: typeof obs === "string" ? obs : obs.content,
            timestamp: new Date().toISOString(),
          })),
          {
            type: "answer" as const,
            content: chatText,
            timestamp: new Date().toISOString(),
          },
        ],
      };

      setSessions((p) => p.map((s) => s.id === activeSessionId ? { ...s, messages: [...s.messages, agentMsg] } : s));

      // Set global results
      setResults({
        chat: data.chat || data.response,
        molecules: (data as any).molecules || [],
        papers_graph: (data as any).papers_graph || { nodes: [], edges: [] },
        papersGraph: (data as any).papers_graph || { nodes: [], edges: [] },
        rag_results: (data as any).rag_results || [],
        ragResults: (data as any).rag_results || [],
        tools: (data as any).tools || (data as any).tools_used || [],
        toolsUsed: (data as any).tools || (data as any).tools_used || [],
        metadata: data.metadata,
      });

      // Auto-trigger docking — use pdb_ids from response or search for structures
      const compoundName =
        data.metadata?.compound?.name ||
        data.metadata?.topic ||
        submittedInput.split(' ').slice(0, 3).join(' ');
      let pdbId = data.metadata?.pdb_ids?.[0];
      if (!pdbId && compoundName) {
        try {
          const structRes = await searchStructures(data.metadata?.topic || submittedInput);
          pdbId = structRes.structures?.[0]?.pdb_id;
        } catch { /* silent */ }
      }
      if (pdbId && compoundName) {
        setAutoDock({ compound: compoundName, pdbId });
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "agent",
        content: "Sorry, I encountered an error while processing your request. Please check if the backend server is running.",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        error: error instanceof Error ? error.message : "Unknown error",
      };
      setSessions((p) => p.map((s) => s.id === activeSessionId ? { ...s, messages: [...s.messages, errorMsg] } : s));
    } finally {
      setIsLocalProcessing(false);
      setIsProcessing(false);
    }
  }, [input, isLocalProcessing, activeSessionId, setQuery, setIsProcessing, setResults]);

  const handleNewChat = () => {
    const ns: ChatSession = { id: `s${Date.now()}`, name: "New Research Chat", messages: [], createdAt: "Now" };
    setSessions((p) => [ns, ...p]);
    setActiveSessionId(ns.id);
  };

  const handleRename = (id: string) => {
    if (editName.trim()) setSessions((p) => p.map((s) => s.id === id ? { ...s, name: editName.trim() } : s));
    setEditingId(null);
  };

  const handleDelete = (id: string) => {
    const remaining = sessions.filter((s) => s.id !== id);
    setSessions(remaining);
    if (activeSessionId === id && remaining.length > 0) setActiveSessionId(remaining[0].id);
  };

  const handleCopy = (text: string, msgId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(msgId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRegenerate = () => {
    if (messages.length < 2) return;
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    if (lastUser) {
      setSessions((p) => p.map((s) => s.id === activeSessionId ? { ...s, messages: s.messages.slice(0, -1) } : s));
      setInput(lastUser.content);
    }
  };

  const suggestions = [
    "Find EGFR inhibitors for NSCLC",
    "Analyze BACE1 inhibitors for Alzheimer's",
    "Search JAK2 inhibitors in myelofibrosis",
    "CDK4/6 inhibitors with low toxicity",
  ];

  return (
    <div className="flex h-full">
      {/* Chat Sidebar */}
      <div className="w-52 bg-[#0D0912] border-r border-rose-500/[0.04] flex flex-col shrink-0">
        <div className="p-3">
          <Button
            onClick={handleNewChat}
            className="w-full h-8 bg-gradient-to-r from-rose-400/90 to-pink-400/90 hover:from-rose-300 hover:to-pink-300 text-white text-[11px] rounded-xl border-0 shadow-lg shadow-rose-500/15 font-medium"
          >
            <Plus className="w-3.5 h-3.5 mr-1" />
            New Chat
          </Button>
        </div>
        <ScrollArea className="flex-1 px-2">
          <div className="space-y-0.5 pb-2">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center gap-2 px-2.5 py-2 rounded-lg cursor-pointer transition-all duration-200 ${
                  activeSessionId === session.id
                    ? "bg-rose-400/[0.08] text-rose-200"
                    : "text-rose-300/30 hover:bg-rose-500/[0.04] hover:text-rose-300/50"
                }`}
                onClick={() => setActiveSessionId(session.id)}
              >
                <MessageSquare className="w-3 h-3 shrink-0" />
                {editingId === session.id ? (
                  <input
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleRename(session.id)}
                    onBlur={() => handleRename(session.id)}
                    className="flex-1 bg-transparent text-[11px] outline-none border-b border-rose-400/30 text-rose-100"
                    autoFocus
                    onClick={(e) => e.stopPropagation()}
                  />
                ) : (
                  <span className="flex-1 text-[11px] truncate">{session.name}</span>
                )}
                <div className="hidden group-hover:flex items-center gap-0.5">
                  <button onClick={(e) => { e.stopPropagation(); setEditingId(session.id); setEditName(session.name); }} className="p-0.5 hover:text-rose-200 transition-colors">
                    <Pencil className="w-2.5 h-2.5" />
                  </button>
                  <button onClick={(e) => { e.stopPropagation(); handleDelete(session.id); }} className="p-0.5 hover:text-red-300 transition-colors">
                    <Trash2 className="w-2.5 h-2.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Chat Main */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center gap-3 px-5 py-3 border-b border-rose-500/[0.04]">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-400 via-pink-400 to-fuchsia-400 flex items-center justify-center shadow-lg shadow-pink-500/20">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 className="text-[13px] font-semibold text-rose-100">ReAct Research Agent</h2>
            <p className="text-[10px] text-rose-300/30">Drug Discovery · RAG-Enhanced</p>
          </div>
          <div className="ml-auto flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400/80 animate-pulse" />
            <span className="text-[10px] text-emerald-400/60 font-medium">Online</span>
          </div>
        </div>

        <ScrollArea className="flex-1 px-5 py-4" ref={scrollRef}>
          <div className="space-y-5 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <div key={msg.id} className="animate-fade-in">
                {msg.role === "user" ? (
                  <div className="flex gap-3 justify-end">
                    <div className="max-w-[80%]">
                      <div className="bg-gradient-to-r from-rose-400/[0.08] to-pink-400/[0.08] border border-rose-400/[0.1] rounded-2xl rounded-tr-md px-4 py-3 backdrop-blur-sm">
                        <p className="text-[13px] text-rose-100/90">{msg.content}</p>
                      </div>
                      <p className="text-[10px] text-rose-300/20 mt-1 text-right">{msg.timestamp}</p>
                    </div>
                    <div className="w-7 h-7 rounded-lg bg-rose-500/[0.06] border border-rose-500/[0.08] flex items-center justify-center shrink-0">
                      <User className="w-3.5 h-3.5 text-rose-300/40" />
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-3">
                    <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-rose-400 to-pink-400 flex items-center justify-center shrink-0 shadow-lg shadow-rose-500/15">
                      <Sparkles className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div className="flex-1 space-y-2">
                      {msg.steps?.map((step, idx) => <StepCard key={idx} step={step} />)}
                      <div className="flex items-center gap-3 pt-1">
                        <button
                          onClick={() => { const t = msg.steps?.map((s) => `[${s.type}] ${s.content}`).join("\n\n") || msg.content; handleCopy(t, msg.id); }}
                          className="flex items-center gap-1 text-[10px] text-rose-300/25 hover:text-rose-300/60 transition-colors"
                        >
                          {copiedId === msg.id ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                          {copiedId === msg.id ? "Copied" : "Copy"}
                        </button>
                        <button onClick={handleRegenerate} className="flex items-center gap-1 text-[10px] text-rose-300/25 hover:text-rose-300/60 transition-colors">
                          <RefreshCw className="w-3 h-3" />
                          Regenerate
                        </button>
                        <span className="text-[10px] text-rose-300/15 ml-auto">{msg.timestamp}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isLocalProcessing && (
              <div className="flex gap-3 animate-fade-in">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-rose-400 to-pink-400 flex items-center justify-center shrink-0 shadow-lg shadow-rose-500/15">
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                </div>
                <div className="flex items-center gap-2 px-4 py-2.5 bg-rose-500/[0.04] border border-rose-500/[0.06] rounded-2xl rounded-tl-md backdrop-blur-sm">
                  <Loader2 className="w-3.5 h-3.5 text-rose-300/50 animate-spin" />
                  <span className="text-[12px] text-rose-300/40">Reasoning...</span>
                  <span className="flex gap-0.5">
                    {[0, 150, 300].map((d) => (
                      <span key={d} className="w-1 h-1 rounded-full bg-rose-300/40 animate-bounce" style={{ animationDelay: `${d}ms` }} />
                    ))}
                  </span>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {messages.length <= 2 && (
          <div className="px-5 pb-2">
            <p className="text-[10px] text-rose-300/20 mb-2 font-medium uppercase tracking-widest">Suggestions</p>
            <div className="flex flex-wrap gap-1.5">
              {suggestions.map((q, i) => (
                <button key={i} onClick={() => setInput(q)} className="text-[11px] px-3 py-1.5 rounded-full border border-rose-500/[0.08] text-rose-300/35 hover:text-rose-300/60 hover:border-rose-400/20 hover:bg-rose-500/[0.04] transition-all">
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="px-5 py-3 border-t border-rose-500/[0.04]">
          <div className="flex gap-2 max-w-3xl mx-auto">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about drug targets, compounds, trials..."
              className="bg-rose-500/[0.04] border-rose-500/[0.08] text-rose-100 placeholder:text-rose-300/20 focus-visible:ring-rose-400/20 rounded-xl text-[13px]"
              disabled={isLocalProcessing}
            />
            <Button
              onClick={handleSend}
              disabled={!input.trim() || isLocalProcessing}
              className="bg-gradient-to-r from-rose-400 to-pink-400 hover:from-rose-300 hover:to-pink-300 text-white shrink-0 rounded-xl shadow-lg shadow-rose-500/20 border-0"
            >
              {isLocalProcessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
