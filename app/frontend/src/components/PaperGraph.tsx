import React, { useState, useRef, useCallback, useEffect } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { X, ExternalLink, Calendar, Users, Star, ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";

interface PaperNode {
  id: string;
  title: string;
  authors: string;
  year: number;
  journal: string;
  citations: number;
  cluster: string;
  doi?: string;
  abstract: string;
  x: number;
  y: number;
  radius: number;
  isCenter?: boolean;
}

interface PaperEdge {
  source: string;
  target: string;
  weight: number;
}

const CLUSTERS: Record<string, { fill: string; stroke: string; glow: string; label: string }> = {
  amyloid: { fill: "#FDA4AF", stroke: "#FB7185", glow: "#FB718540", label: "Amyloid-B" },
  tau: { fill: "#D8B4FE", stroke: "#C084FC", glow: "#C084FC40", label: "Tau Pathology" },
  bace: { fill: "#F0ABFC", stroke: "#E879F9", glow: "#E879F940", label: "BACE Inhibitors" },
  structural: { fill: "#86EFAC", stroke: "#4ADE80", glow: "#4ADE8040", label: "Structural Biology" },
  multiTarget: { fill: "#FDE68A", stroke: "#FBBF24", glow: "#FBBF2440", label: "Multi-Target" },
};

const NODES: PaperNode[] = [
  { id: "center", title: "Lecanemab in Early Alzheimer's Disease", authors: "van Dyck CH et al.", year: 2025, journal: "NEJM", citations: 1247, cluster: "amyloid", doi: "10.1056/NEJMoa2212948", abstract: "Phase 3 CLARITY AD trial showed lecanemab reduced amyloid markers and slowed cognitive decline by 27% vs placebo.", x: 400, y: 300, radius: 34, isCenter: true },
  { id: "p2", title: "Donanemab TRAILBLAZER-ALZ 2 Trial", authors: "Sims JR et al.", year: 2025, journal: "JAMA", citations: 892, cluster: "amyloid", abstract: "35% slowing of clinical decline with 80% amyloid clearance by 12 months.", x: 245, y: 175, radius: 27 },
  { id: "p3", title: "Aducanumab: Lessons from EMERGE", authors: "Knopman DS et al.", year: 2024, journal: "Nature Medicine", citations: 567, cluster: "amyloid", abstract: "Critical analysis of aducanumab trials and implications for anti-amyloid therapy.", x: 555, y: 165, radius: 23 },
  { id: "p4", title: "Next-Gen BACE1 Inhibitors", authors: "Vassar R et al.", year: 2025, journal: "Nat Rev Drug Discov", citations: 234, cluster: "bace", abstract: "Proposes partial BACE1 inhibition (30-50%) as optimal strategy.", x: 175, y: 385, radius: 20 },
  { id: "p5", title: "Cryo-EM Structure of AB42 Fibrils", authors: "Yang Y et al.", year: 2024, journal: "Science", citations: 567, cluster: "structural", abstract: "Resolved AB42 fibrils at 2.1A, identifying 3 novel druggable pockets.", x: 605, y: 345, radius: 25 },
  { id: "p6", title: "Multi-Target Drug Design for AD", authors: "Cummings J et al.", year: 2025, journal: "Alzheimer's & Dementia", citations: 89, cluster: "multiTarget", abstract: "Dual-target approach combining anti-amyloid and anti-tau mechanisms.", x: 315, y: 455, radius: 18 },
  { id: "p7", title: "Tau Propagation & Neurodegeneration", authors: "De Strooper B et al.", year: 2024, journal: "Cell", citations: 445, cluster: "tau", abstract: "Mechanisms of tau spreading across neural circuits.", x: 505, y: 465, radius: 23 },
  { id: "p8", title: "Anti-Tau Immunotherapy Phase II", authors: "Boxer AL et al.", year: 2025, journal: "Lancet Neurology", citations: 178, cluster: "tau", abstract: "Semorinemab showed reduction in tau PET signal.", x: 145, y: 245, radius: 18 },
  { id: "p9", title: "Blood Biomarkers for AD Diagnosis", authors: "Hansson O et al.", year: 2025, journal: "Nature Medicine", citations: 623, cluster: "amyloid", abstract: "Plasma p-tau217 achieves 96% accuracy for amyloid positivity.", x: 655, y: 225, radius: 25 },
  { id: "p10", title: "BACE2 Selectivity in Drug Design", authors: "Bhatt DK et al.", year: 2024, journal: "J Med Chem", citations: 112, cluster: "bace", abstract: "SAR study achieving >100-fold BACE1/BACE2 selectivity.", x: 95, y: 455, radius: 16 },
];

const EDGES: PaperEdge[] = [
  { source: "center", target: "p2", weight: 0.92 },
  { source: "center", target: "p3", weight: 0.88 },
  { source: "center", target: "p5", weight: 0.72 },
  { source: "center", target: "p9", weight: 0.78 },
  { source: "center", target: "p6", weight: 0.65 },
  { source: "center", target: "p4", weight: 0.58 },
  { source: "p2", target: "p3", weight: 0.85 },
  { source: "p2", target: "p9", weight: 0.7 },
  { source: "p3", target: "p9", weight: 0.68 },
  { source: "p4", target: "p10", weight: 0.9 },
  { source: "p4", target: "p6", weight: 0.55 },
  { source: "p5", target: "p7", weight: 0.6 },
  { source: "p6", target: "p7", weight: 0.75 },
  { source: "p6", target: "p8", weight: 0.62 },
  { source: "p7", target: "p8", weight: 0.82 },
  { source: "p8", target: "p2", weight: 0.5 },
  { source: "p10", target: "p5", weight: 0.48 },
];

export default function PaperGraph({ query }: { query?: string }) {
  const { query: globalQuery, results } = useGlobalQuery();
  const currentQuery = query || globalQuery;
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState<PaperNode | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const [yearFilter, setYearFilter] = useState(2023);
  const [dims, setDims] = useState({ w: 800, h: 600 });

  useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        const r = containerRef.current.getBoundingClientRect();
        setDims({ w: r.width, h: r.height });
      }
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const backendNodes = (results.papers_graph?.nodes || results.papersGraph?.nodes || []).map((node: any, index: number) => {
    const angle = (index / Math.max(1, (results.papers_graph?.nodes || results.papersGraph?.nodes || []).length)) * Math.PI * 2;
    const radius = index === 0 ? 0 : 190;
    return {
      id: node.id || `paper-${index}`,
      title: node.title || node.pubmedId || `Paper ${index + 1}`,
      authors: node.authors || "PubMed indexed authors",
      year: node.year || new Date().getFullYear(),
      journal: node.journal || "PubMed",
      citations: node.citations || 0,
      cluster: index % 3 === 0 ? "amyloid" : index % 3 === 1 ? "structural" : "multiTarget",
      doi: node.doi,
      abstract: node.abstract || `PubMed record ${node.pubmedId || node.id}`,
      x: 400 + Math.cos(angle) * radius,
      y: 300 + Math.sin(angle) * radius,
      radius: index === 0 ? 30 : 18,
      isCenter: index === 0,
    };
  });
  const backendEdges = (results.papers_graph?.edges || results.papersGraph?.edges || []).length
    ? (results.papers_graph?.edges || results.papersGraph?.edges || [])
    : backendNodes.slice(1).map((node: PaperNode) => ({ source: backendNodes[0]?.id, target: node.id, weight: 0.7 }));

  const sourceNodes = backendNodes.length ? backendNodes : NODES;
  const sourceEdges = backendNodes.length ? backendEdges : EDGES;
  const nodes = sourceNodes.filter((n) => n.year >= yearFilter);
  const nodeIds = new Set(nodes.map((n) => n.id));
  const edges = sourceEdges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
  const nodeMap = Object.fromEntries(nodes.map((n) => [n.id, n]));

  const connEdges = (id: string) => edges.filter((e) => e.source === id || e.target === id);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    const tag = (e.target as SVGElement).tagName;
    if (tag === "svg" || tag === "rect") {
      setIsPanning(true);
      setPanStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  }, [pan]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) setPan({ x: e.clientX - panStart.x, y: e.clientY - panStart.y });
  }, [isPanning, panStart]);

  const onMouseUp = useCallback(() => setIsPanning(false), []);

  return (
    <div className="flex flex-col h-full relative">
      {/* Controls */}
      <div className="absolute top-3 left-3 z-20 flex flex-col gap-2">
        <div className="flex gap-0.5 bg-rose-500/[0.04] backdrop-blur-2xl border border-rose-500/[0.08] rounded-xl p-0.5">
          <Button size="sm" variant="ghost" onClick={() => setZoom((z) => Math.min(z + 0.2, 3))} className="h-7 w-7 p-0 text-rose-300/50 hover:text-rose-200 hover:bg-rose-500/[0.08]">
            <ZoomIn className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))} className="h-7 w-7 p-0 text-rose-300/50 hover:text-rose-200 hover:bg-rose-500/[0.08]">
            <ZoomOut className="w-3.5 h-3.5" />
          </Button>
          <Button size="sm" variant="ghost" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }} className="h-7 w-7 p-0 text-rose-300/50 hover:text-rose-200 hover:bg-rose-500/[0.08]">
            <Maximize2 className="w-3.5 h-3.5" />
          </Button>
        </div>
        <span className="text-[10px] text-rose-300/30 bg-rose-500/[0.04] backdrop-blur-2xl border border-rose-500/[0.08] rounded-lg px-2 py-1 font-mono text-center">
          {Math.round(zoom * 100)}%
        </span>
      </div>

      {/* Legend */}
      <div className="absolute top-3 right-3 z-20 bg-rose-500/[0.04] backdrop-blur-2xl border border-rose-500/[0.08] rounded-xl p-3">
        <p className="text-[10px] font-semibold text-rose-200/60 mb-2 uppercase tracking-wider">Clusters</p>
        <div className="space-y-1.5">
          {Object.entries(CLUSTERS).map(([k, v]) => (
            <div key={k} className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: v.fill }} />
              <span className="text-[10px] text-rose-200/50">{v.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="absolute bottom-3 left-3 right-3 z-20 bg-rose-500/[0.04] backdrop-blur-2xl border border-rose-500/[0.08] rounded-xl px-4 py-2.5">
        <div className="flex items-center gap-3">
          <span className="text-[10px] text-rose-300/30 shrink-0 uppercase tracking-wider">Timeline</span>
          <input type="range" min={2022} max={2026} value={yearFilter} onChange={(e) => setYearFilter(Number(e.target.value))} className="flex-1 h-1 accent-rose-400 cursor-pointer" />
          <span className="text-[10px] font-mono text-rose-300/60 shrink-0 w-8">{yearFilter}+</span>
          <span className="text-[10px] text-rose-300/25">{nodes.length} papers</span>
        </div>
      </div>

      {/* SVG */}
      <div ref={containerRef} className="flex-1 overflow-hidden cursor-grab active:cursor-grabbing" onMouseDown={onMouseDown} onMouseMove={onMouseMove} onMouseUp={onMouseUp} onMouseLeave={onMouseUp}>
        <svg ref={svgRef} width="100%" height="100%" viewBox={`0 0 ${dims.w} ${dims.h}`} className="select-none">
          <defs>
            <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FDA4AF" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#FDA4AF" stopOpacity="0" />
            </radialGradient>
            <filter id="softGlow">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="transparent" />
          <g transform={`translate(${pan.x + dims.w / 2 * (1 - zoom)}, ${pan.y + dims.h / 2 * (1 - zoom)}) scale(${zoom})`}>
            {edges.map((edge, i) => {
              const s = nodeMap[edge.source];
              const t = nodeMap[edge.target];
              if (!s || !t) return null;
              const hi = hovered === edge.source || hovered === edge.target;
              return (
                <line key={i} x1={s.x} y1={s.y} x2={t.x} y2={t.y}
                  stroke={hi ? "#FDA4AF" : "rgba(253,164,175,0.06)"}
                  strokeWidth={hi ? edge.weight * 3 : edge.weight * 1.5}
                  strokeOpacity={hi ? 0.7 : 0.5}
                  className="transition-all duration-300"
                />
              );
            })}
            {nodes.map((node) => {
              const cl = CLUSTERS[node.cluster] || CLUSTERS.amyloid;
              const isH = hovered === node.id;
              const isS = selected?.id === node.id;
              const isConn = hovered ? connEdges(hovered).some((e) => e.source === node.id || e.target === node.id) : false;
              const op = !hovered || isH || isConn ? 1 : 0.25;
              return (
                <g key={node.id} className="cursor-pointer transition-all duration-300" opacity={op}
                  onClick={() => setSelected(node)} onMouseEnter={() => setHovered(node.id)} onMouseLeave={() => setHovered(null)}>
                  {node.isCenter && <circle cx={node.x} cy={node.y} r={node.radius * 2.2} fill="url(#centerGlow)" />}
                  <circle cx={node.x} cy={node.y} r={isH || isS ? node.radius + 5 : node.radius}
                    fill={cl.fill} fillOpacity={isH || isS ? 0.25 : 0.12}
                    stroke={cl.stroke} strokeWidth={isH || isS ? 2 : 1}
                    filter={isH ? "url(#softGlow)" : undefined}
                    className="transition-all duration-200"
                  />
                  <circle cx={node.x} cy={node.y} r={3.5} fill={cl.fill} fillOpacity={0.8} />
                  <text x={node.x} y={node.y + node.radius + 14} textAnchor="middle"
                    fill={isH ? "#FECDD3" : "#6B5B6E"} fontSize={isH ? 10 : 8.5} fontWeight={isH ? 600 : 400}
                    className="transition-all duration-200 pointer-events-none" fontFamily="Plus Jakarta Sans, sans-serif">
                    {node.title.length > 28 ? node.title.substring(0, 28) + "..." : node.title}
                  </text>
                  <text x={node.x} y={node.y + node.radius + 25} textAnchor="middle"
                    fill="#4A3F50" fontSize={7.5} className="pointer-events-none" fontFamily="Plus Jakarta Sans, sans-serif">
                    {node.year} · {node.citations} cit.
                  </text>
                </g>
              );
            })}
          </g>
        </svg>
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-30 w-[400px] max-w-[90%] animate-fade-in">
          <Card className="bg-[#1A1322]/95 backdrop-blur-2xl border-rose-500/[0.08] p-4 shadow-2xl shadow-rose-500/5 rounded-2xl">
            <div className="flex items-start justify-between mb-2.5">
              <Badge className="text-[10px]" style={{ backgroundColor: `${CLUSTERS[selected.cluster]?.fill}15`, color: CLUSTERS[selected.cluster]?.fill, borderColor: `${CLUSTERS[selected.cluster]?.fill}25` }}>
                {CLUSTERS[selected.cluster]?.label}
              </Badge>
              <button onClick={() => setSelected(null)} className="text-rose-300/25 hover:text-rose-200 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
            <h3 className="text-[13px] font-semibold text-rose-100/90 mb-1 leading-snug">{selected.title}</h3>
            <p className="text-[11px] text-rose-300/40 mb-2">{selected.authors}</p>
            <div className="flex items-center gap-3 text-[10px] text-rose-300/30 mb-2.5">
              <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{selected.year}</span>
              <span className="flex items-center gap-1"><Users className="w-3 h-3" />{selected.citations} cit.</span>
              <span className="flex items-center gap-1"><Star className="w-3 h-3 text-amber-400/60" />{selected.journal}</span>
            </div>
            <p className="text-[11px] text-rose-200/60 leading-relaxed mb-3">{selected.abstract}</p>
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-rose-300/20">{connEdges(selected.id).length} connections</span>
              {selected.doi && (
                <a href={`https://doi.org/${selected.doi}`} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-[10px] text-rose-300/50 hover:text-rose-200 ml-auto transition-colors">
                  View Paper <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </Card>
        </div>
      )}

      {currentQuery && (
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10">
          <Badge className="bg-rose-400/[0.08] text-rose-300/60 border-rose-400/15 text-[10px] backdrop-blur-sm">
            Graph: &quot;{currentQuery.substring(0, 35)}{currentQuery.length > 35 ? "..." : ""}&quot;
          </Badge>
        </div>
      )}
    </div>
  );
}
