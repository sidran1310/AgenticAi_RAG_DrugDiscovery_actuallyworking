import React, { useState, useEffect, useRef } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Atom, Search, CheckCircle2, XCircle, Activity, Beaker, Shield, Target, Box, Download, Play, Loader2, Database } from "lucide-react";
import { useGlobalQuery } from "@/contexts/GlobalQueryContext";
import { downloadStructure, runDocking, searchCompounds, searchStructures, manualSearch } from "@/lib/api";

interface Compound {
  id: string; name: string; chemblId: string; drugClass: string; relevance: number;
  props: { mw: number; logP: number; hbd: number; hba: number; tpsa: number; rotBonds: number };
  dock: { target: string; score: number; pose: string; rmsd: number };
  admet: { solubility: string; permeability: string; cyp3a4: string; herg: string; hepatotox: string; bbb: string };
  lipinski: { passes: boolean; violations: number };
}

const COMPOUNDS: Compound[] = [
  { id: "1", name: "Lecanemab", chemblId: "CHEMBL4523167", drugClass: "Monoclonal Antibody", relevance: 97, props: { mw: 146000, logP: -2.1, hbd: 180, hba: 420, tpsa: 8500, rotBonds: 45 }, dock: { target: "AB Protofibrils (6SZF)", score: -8.7, pose: "Interface binding", rmsd: 1.2 }, admet: { solubility: "High (IV)", permeability: "N/A (biologic)", cyp3a4: "No interaction", herg: "Safe", hepatotox: "Low risk", bbb: "Limited" }, lipinski: { passes: false, violations: 2 } },
  { id: "2", name: "Donanemab", chemblId: "CHEMBL4651234", drugClass: "Monoclonal Antibody", relevance: 94, props: { mw: 148000, logP: -1.8, hbd: 185, hba: 430, tpsa: 8700, rotBonds: 48 }, dock: { target: "N3pGlu-AB (7Q4B)", score: -8.1, pose: "Epitope binding", rmsd: 1.5 }, admet: { solubility: "High (IV)", permeability: "N/A (biologic)", cyp3a4: "No interaction", herg: "Safe", hepatotox: "Low risk", bbb: "Limited" }, lipinski: { passes: false, violations: 2 } },
  { id: "3", name: "Aducanumab", chemblId: "CHEMBL4297891", drugClass: "Monoclonal Antibody", relevance: 82, props: { mw: 145500, logP: -2.3, hbd: 175, hba: 415, tpsa: 8400, rotBonds: 42 }, dock: { target: "AB Aggregates (6SZF)", score: -9.2, pose: "Fibril surface", rmsd: 0.9 }, admet: { solubility: "High (IV)", permeability: "N/A (biologic)", cyp3a4: "No interaction", herg: "Safe", hepatotox: "Moderate risk", bbb: "Limited" }, lipinski: { passes: false, violations: 2 } },
  { id: "4", name: "NVD-001", chemblId: "CHEMBL5001234", drugClass: "BACE1 Partial Inhibitor", relevance: 78, props: { mw: 423.5, logP: 2.8, hbd: 2, hba: 5, tpsa: 78.2, rotBonds: 6 }, dock: { target: "BACE1 (6EJ2)", score: -7.8, pose: "Active site", rmsd: 0.8 }, admet: { solubility: "Moderate", permeability: "High", cyp3a4: "Weak inhibitor", herg: "Safe", hepatotox: "Low risk", bbb: "High penetration" }, lipinski: { passes: true, violations: 0 } },
  { id: "5", name: "BMS-986405", chemblId: "CHEMBL5002345", drugClass: "BACE1 Partial Inhibitor", relevance: 75, props: { mw: 456.2, logP: 3.1, hbd: 1, hba: 6, tpsa: 82.5, rotBonds: 7 }, dock: { target: "BACE1 (6EJ2)", score: -8.3, pose: "Allosteric site", rmsd: 1.1 }, admet: { solubility: "Moderate", permeability: "High", cyp3a4: "No interaction", herg: "Borderline", hepatotox: "Low risk", bbb: "High penetration" }, lipinski: { passes: true, violations: 0 } },
  { id: "6", name: "AZD-3839", chemblId: "CHEMBL5003456", drugClass: "BACE1 Selective", relevance: 72, props: { mw: 389.8, logP: 2.4, hbd: 2, hba: 4, tpsa: 65.3, rotBonds: 5 }, dock: { target: "BACE1 (6EJ2)", score: -7.5, pose: "Active site", rmsd: 1.3 }, admet: { solubility: "High", permeability: "High", cyp3a4: "No interaction", herg: "Safe", hepatotox: "Low risk", bbb: "High penetration" }, lipinski: { passes: true, violations: 0 } },
];

function admetColor(v: string) {
  const l = v.toLowerCase();
  if (l.includes("high") || l.includes("safe") || l.includes("low risk") || l.includes("no interaction")) return "text-emerald-300/70";
  if (l.includes("moderate") || l.includes("weak") || l.includes("borderline") || l.includes("limited")) return "text-amber-300/70";
  return "text-red-300/70";
}

function MoleculeScene({ receptorPdb, ligandPdb }: { receptorPdb: string; ligandPdb: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    let viewer: any;
    const init = async () => {
      try {
        const $3Dmol = (await import("3dmol")).default ?? (await import("3dmol"));
        if (!containerRef.current) return;

        if (viewerRef.current) {
          try { viewerRef.current.clear(); } catch {}
        }

        viewer = $3Dmol.createViewer(containerRef.current, {
          backgroundColor: "0x0f0a14",
          antialias: true,
        });
        viewerRef.current = viewer;

        if (receptorPdb) {
          viewer.addModel(receptorPdb, "pdb");
          viewer.setStyle({ model: 0 }, { cartoon: { color: "spectrum", opacity: 0.85 } });
        }

        if (ligandPdb) {
          viewer.addModel(ligandPdb, "pdb");
          viewer.setStyle({ model: 1 }, { stick: { radius: 0.2, colorscheme: "greenCarbon" } });
          viewer.setStyle({ model: 1, elem: "N" }, { stick: { radius: 0.2, color: "#60a5fa" } });
          viewer.setStyle({ model: 1, elem: "O" }, { stick: { radius: 0.2, color: "#f87171" } });
          viewer.addSurface($3Dmol.SurfaceType.VDW, {
            opacity: 0.15,
            color: "#fb7185",
          }, { model: 1 });
          viewer.zoomTo({ model: 1 });
        } else if (receptorPdb) {
          viewer.zoomTo();
        }

        viewer.render();
      } catch (e) {
        console.error("3Dmol init error:", e);
      }
    };

    init();

    return () => {
      if (viewerRef.current) {
        try { viewerRef.current.clear(); } catch {}
      }
    };
  }, [receptorPdb, ligandPdb]);

  if (!receptorPdb && !ligandPdb) {
    return (
      <div className="flex h-full items-center justify-center text-center">
        <div>
          <Box className="mx-auto mb-2 h-8 w-8 text-rose-300/25" />
          <p className="text-[12px] text-rose-300/40">Load a PDB structure to render</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />
      <div className="absolute left-3 top-3 z-10 flex gap-2 pointer-events-none">
        {receptorPdb && <Badge className="bg-black/50 text-rose-200 border-rose-400/20 text-[10px]">Protein</Badge>}
        {ligandPdb && <Badge className="bg-black/50 text-emerald-200 border-emerald-400/20 text-[10px]">Ligand</Badge>}
      </div>
    </div>
  );
}

export default function MolecularViewer() {
  const { query: globalQuery, results, autoDock, setAutoDock } = useGlobalQuery();
  const [search, setSearch] = useState("");
  const [sel, setSel] = useState<any>(null);
  const [apiMolecules, setApiMolecules] = useState<any[]>([]);
  const [structureId, setStructureId] = useState<string>("");
  const [receptorPdb, setReceptorPdb] = useState<string>("");
  const [ligandPdb, setLigandPdb] = useState<string>("");
  const [viewerStatus, setViewerStatus] = useState("Search a target or ask the agent to load a structure.");
  const [isDocking, setIsDocking] = useState(false);
  const [manualSearchType, setManualSearchType] = useState<'chembl' | 'pubchem'>('chembl');
  const [manualResults, setManualResults] = useState<any>(null);
  const [manualLoading, setManualLoading] = useState(false);

  const handleManualSearch = async () => {
    if (!search.trim()) return;
    setManualLoading(true);
    setViewerStatus("Searching database...");
    try {
      const res = await manualSearch(manualSearchType, search);
      setManualResults(res);
      setViewerStatus(`Found ${res.count || res.length || 0} ${manualSearchType.toUpperCase()} results`);
    } catch {
      setManualResults({ error: 'Search failed' });
      setViewerStatus("Search failed");
    } finally {
      setManualLoading(false);
    }
  };

  const normalizeMolecule = (m: any, index: number) => ({
    id: m.id || `compound-${index}`,
    name: m.name || m.compound || "Unknown compound",
    chemblId: m.chemblId || m.chembl_id || "Not assigned",
    drugClass: m.drugClass || m.drug_class || m.phase || "Candidate compound",
    relevance: m.relevance || Math.round((m.relevance_score || 0.75) * 100),
    props: m.props || { mw: m.molecularWeight || 0, logP: m.logP ?? 0, hbd: m.hbd ?? 0, hba: m.hba ?? 0, tpsa: m.tpsa ?? 0, rotBonds: m.rotBonds ?? 0 },
    dock: m.dock || { target: m.target || "Target structure pending", score: m.dockingScore ?? null, pose: "Not docked", rmsd: null },
    admet: m.admet || { solubility: "Needs assay", permeability: "Needs assay", cyp3a4: "Unknown", herg: "Unknown", hepatotox: "Unknown", bbb: "Unknown" },
    lipinski: m.lipinski || { passes: Boolean(m.lipinskiPass), violations: m.lipinskiPass ? 0 : 1 },
  });

  const sourceMolecules = results.molecules?.length ? results.molecules : apiMolecules.length ? apiMolecules : COMPOUNDS;
  const molecules = sourceMolecules.map(normalizeMolecule);

  useEffect(() => { if (globalQuery) setSearch(""); }, [globalQuery]);

  useEffect(() => {
    const pdbId = results.metadata?.pdb_ids?.[0];
    if (pdbId) setStructureId(pdbId);
  }, [results.metadata]);

  useEffect(() => {
    if (!globalQuery || results.molecules?.length) return;
    let cancelled = false;
    searchCompounds(globalQuery, 5).then((data) => { if (!cancelled) setApiMolecules(data.compounds || []); }).catch(() => { if (!cancelled) setApiMolecules([]); });
    searchStructures(globalQuery).then((data) => { if (!cancelled && data.structures?.[0]?.pdb_id) setStructureId(data.structures[0].pdb_id); }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [globalQuery, results.molecules?.length]);

  const filtered = molecules.filter((c: any) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return c.name?.toLowerCase().includes(q) || c.drugClass?.toLowerCase().includes(q) || c.chemblId?.toLowerCase().includes(q);
  });

  useEffect(() => {
    if (filtered.length > 0 && (!sel || !filtered.some((c: any) => c.id === sel.id))) setSel(filtered[0]);
    if (filtered.length === 0) setSel(null);
  }, [filtered, sel]);

  const fmtMW = (mw: number) => mw > 1000 ? `${(mw / 1000).toFixed(1)}k Da` : `${mw} Da`;

  const loadStructure = async (pdbId = structureId) => {
    if (!pdbId) return;
    setViewerStatus(`Downloading ${pdbId}...`);
    setLigandPdb("");
    const data = await downloadStructure(pdbId);
    const response = await fetch(data.viewer_url);
    if (!response.ok) throw new Error(`Failed to fetch structure file: ${response.status}`);
    const text = await response.text();
    setReceptorPdb(text);
    setStructureId(data.pdb_id || pdbId);
    setViewerStatus(`Loaded ${data.file_name} — ${pdbId}`);
  };

  useEffect(() => {
    if (structureId) loadStructure(structureId).catch((err) => setViewerStatus(err instanceof Error ? err.message : "Structure load failed"));
  }, [structureId]);

  const dockSelected = async () => {
    if (!sel || !structureId) return;
    setIsDocking(true);
    setViewerStatus(`Docking ${sel.name} into ${structureId}...`);
    try {
      const data = await runDocking(sel.name, structureId);
      if (data.pose_viewer_url) {
        const response = await fetch(data.pose_viewer_url);
        if (!response.ok) throw new Error(`Failed to fetch pose file: ${response.status}`);
        setLigandPdb(await response.text());
      }
      const score = data.best_score ?? data.binding_affinity;
      setViewerStatus(score ? `Docking complete — ${score} kcal/mol` : (data.results?.[0] || "Docking complete."));
      if (score) setSel((c: any) => c ? { ...c, dock: { ...c.dock, target: structureId, score, pose: "Ranked pose", rmsd: c.dock?.rmsd ?? null } } : c);
    } catch (err) {
      setViewerStatus(err instanceof Error ? err.message : "Docking failed");
    } finally {
      setIsDocking(false);
    }
  };

  useEffect(() => {
    if (!autoDock) return;
    const { compound, pdbId } = autoDock;
    setAutoDock(null);
    setStructureId(pdbId);
    setViewerStatus(`Loading ${pdbId}...`);
    setIsDocking(true);
    setLigandPdb("");

    const run = async () => {
      // Load receptor first, then dock
      try {
        const structData = await downloadStructure(pdbId);
        const recResp = await fetch(structData.viewer_url);
        if (!recResp.ok) throw new Error(`Structure fetch failed: ${recResp.status}`);
        const recText = await recResp.text();
        setReceptorPdb(recText);
      } catch (err) {
        setViewerStatus(`Structure load failed: ${err instanceof Error ? err.message : err}`);
        setIsDocking(false);
        return;
      }

      setViewerStatus(`Docking ${compound} into ${pdbId}...`);
      try {
        const data = await runDocking(compound, pdbId);
        if (data.pose_viewer_url) {
          const resp = await fetch(data.pose_viewer_url);
          if (!resp.ok) throw new Error(`Pose fetch failed: ${resp.status}`);
          setLigandPdb(await resp.text());
        }
        const score = data.best_score ?? data.binding_affinity;
        setViewerStatus(score ? `Docking complete — ${score} kcal/mol` : (data.results?.[0] || "Docking complete."));
        if (score) setSel((c: any) => c ? { ...c, dock: { ...c.dock, target: pdbId, score, pose: "Ranked pose", rmsd: c.dock?.rmsd ?? null } } : c);
      } catch (err) {
        setViewerStatus(err instanceof Error ? err.message : "Docking failed");
      } finally {
        setIsDocking(false);
      }
    };

    run();
  }, [autoDock]);

  return (
    <div className="flex h-full">
      {/* List */}
      <div className="w-64 border-r border-rose-500/[0.04] flex flex-col shrink-0">
        <div className="p-3 border-b border-rose-500/[0.04]">
          {globalQuery && results.molecules?.length > 0 && <p className="text-[10px] text-rose-300/40 mb-2">{results.molecules.length} compounds from query</p>}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-rose-300/25" />
            <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search compounds..."
              className="pl-9 h-8 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-100 placeholder:text-rose-300/20 focus-visible:ring-rose-400/20 rounded-lg text-[11px]" />
          </div>
          <div className="mt-3 space-y-2">
            <div className="flex gap-2">
              <Select value={manualSearchType} onValueChange={(value: any) => setManualSearchType(value)}>
                <SelectTrigger className="flex-1 h-7 bg-rose-500/[0.04] border-rose-500/[0.06] text-rose-100/80 text-[10px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="chembl"><div className="flex items-center gap-2"><Atom className="w-3 h-3" />ChEMBL</div></SelectItem>
                  <SelectItem value="pubchem"><div className="flex items-center gap-2"><Database className="w-3 h-3" />PubChem</div></SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={handleManualSearch} disabled={manualLoading || !search.trim()} className="h-7 bg-rose-500/20 hover:bg-rose-500/30 border-rose-500/30 px-2">
                {manualLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
              </Button>
            </div>
            {manualResults && (
              <div className="text-[10px] text-rose-300/60">
                {manualResults.error ? <span className="text-red-400">{manualResults.error}</span> : <span>Found {manualResults.count || manualResults.length || 0} results</span>}
              </div>
            )}
          </div>
        </div>
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {filtered.map((c) => (
              <button key={c.id} onClick={() => setSel(c)}
                className={`w-full text-left p-3 rounded-xl transition-all duration-200 ${sel?.id === c.id ? "bg-rose-400/[0.08] border border-rose-400/[0.12]" : "hover:bg-rose-500/[0.04] border border-transparent"}`}>
                <div className="flex items-center gap-2 mb-1">
                  <Atom className={`w-3.5 h-3.5 ${sel?.id === c.id ? "text-rose-300/70" : "text-rose-300/20"}`} />
                  <span className="text-[12px] font-semibold text-rose-100/80">{c.name}</span>
                </div>
                <p className="text-[10px] text-rose-300/25 ml-5.5">{c.drugClass}</p>
                <div className="flex items-center gap-2 ml-5.5 mt-1">
                  <div className="flex-1 h-1 bg-rose-500/[0.06] rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-rose-400/60 to-pink-400/60 rounded-full transition-all" style={{ width: `${c.relevance}%` }} />
                  </div>
                  <span className="text-[10px] font-mono text-rose-300/50">{c.relevance}%</span>
                </div>
              </button>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Detail */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!sel ? (
          <div className="flex flex-1 items-center justify-center text-center">
            <div>
              <Atom className="w-10 h-10 text-rose-300/25 mx-auto mb-3" />
              <p className="text-[13px] text-rose-300/50">No molecules match this query</p>
              <p className="text-[11px] text-rose-300/30">Try a compound, drug target, or disease indication.</p>
            </div>
          </div>
        ) : (
        <>
        <div className="p-4 border-b border-rose-500/[0.04]">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-rose-400/15 to-pink-400/15 border border-rose-400/10 flex items-center justify-center">
              <Atom className="w-5 h-5 text-rose-300/60" />
            </div>
            <div>
              <h2 className="text-base font-bold text-rose-100/90">{sel.name}</h2>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="bg-rose-400/[0.06] text-rose-300/60 border-rose-400/10 text-[10px]">{sel.drugClass}</Badge>
                <span className="text-[10px] text-rose-300/25 font-mono">{sel.chemblId}</span>
              </div>
            </div>
            <div className="ml-auto text-right">
              <p className="text-[10px] text-rose-300/25">Relevance</p>
              <p className="text-2xl font-bold bg-gradient-to-r from-rose-300 to-pink-300 bg-clip-text text-transparent">{sel.relevance}%</p>
            </div>
          </div>
        </div>

        <div className="mx-4 mt-4 overflow-hidden rounded-xl border border-rose-500/[0.06] bg-rose-500/[0.03]">
          <div className="flex items-center gap-2 border-b border-rose-500/[0.06] bg-white/5 px-3 py-2">
            <Input value={structureId} onChange={(e) => setStructureId(e.target.value.toUpperCase())} placeholder="PDB ID"
              className="h-8 w-28 bg-white/10 border-rose-400/20 text-rose-100 text-[11px]" />
            <Button size="sm" variant="ghost" onClick={() => loadStructure()} disabled={!structureId} className="h-8 text-[11px] text-rose-300 hover:bg-rose-500/10">
              <Download className="w-3 h-3 mr-1" />Load
            </Button>
            <Button size="sm" onClick={dockSelected} disabled={!sel || !structureId || isDocking} className="h-8 text-[11px] bg-rose-500 hover:bg-rose-400">
              {isDocking ? <Loader2 className="w-3 h-3 mr-1 animate-spin" /> : <Play className="w-3 h-3 mr-1" />}
              {isDocking ? "Docking..." : "Dock"}
            </Button>
            <span className="ml-auto truncate text-[10px] text-rose-300/50">{viewerStatus}</span>
          </div>
          <div className="h-[300px]">
            <MoleculeScene receptorPdb={receptorPdb} ligandPdb={ligandPdb} />
          </div>
        </div>

        <Tabs defaultValue="properties" className="flex-1 flex flex-col overflow-hidden">
          <TabsList className="mx-4 mt-3 bg-rose-500/[0.04] border border-rose-500/[0.06] rounded-xl p-0.5 shrink-0">
            <TabsTrigger value="properties" className="text-[10px] rounded-lg data-[state=active]:bg-rose-400/10 data-[state=active]:text-rose-300/80"><Beaker className="w-3 h-3 mr-1" />Properties</TabsTrigger>
            <TabsTrigger value="docking" className="text-[10px] rounded-lg data-[state=active]:bg-rose-400/10 data-[state=active]:text-rose-300/80"><Target className="w-3 h-3 mr-1" />Docking</TabsTrigger>
            <TabsTrigger value="admet" className="text-[10px] rounded-lg data-[state=active]:bg-rose-400/10 data-[state=active]:text-rose-300/80"><Shield className="w-3 h-3 mr-1" />ADMET</TabsTrigger>
          </TabsList>

          <ScrollArea className="flex-1 p-4">
            <TabsContent value="properties" className="mt-0">
              <div className="grid grid-cols-3 gap-2.5 mb-4">
                {[
                  { label: "Molecular Weight", value: fmtMW(sel.props.mw || 0) },
                  { label: "LogP", value: sel.props.logP.toString() },
                  { label: "TPSA", value: `${sel.props.tpsa} A2` },
                  { label: "H-Bond Donors", value: sel.props.hbd.toString() },
                  { label: "H-Bond Acceptors", value: sel.props.hba.toString() },
                  { label: "Rotatable Bonds", value: sel.props.rotBonds.toString() },
                ].map((p, i) => (
                  <Card key={i} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-3 rounded-xl">
                    <p className="text-[10px] text-rose-300/25 mb-0.5">{p.label}</p>
                    <p className="text-base font-bold text-rose-100/80">{p.value}</p>
                  </Card>
                ))}
              </div>
              <Card className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-4 rounded-xl">
                <div className="flex items-center gap-2 mb-1.5">
                  {sel.lipinski.passes ? <CheckCircle2 className="w-4 h-4 text-emerald-300/70" /> : <XCircle className="w-4 h-4 text-amber-300/70" />}
                  <h3 className="text-[12px] font-semibold text-rose-100/80">Lipinski Rule of Five</h3>
                </div>
                <p className="text-[11px] text-rose-300/40">{sel.lipinski.passes ? "Passes — good oral bioavailability" : `${sel.lipinski.violations} violation(s)`}</p>
              </Card>
            </TabsContent>

            <TabsContent value="docking" className="mt-0 space-y-3">
              <Card className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-4 rounded-xl">
                <h3 className="text-[12px] font-semibold text-rose-100/80 mb-3">Docking Results</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div><p className="text-[10px] text-rose-300/25 mb-0.5">Target</p><p className="text-[12px] font-semibold text-rose-100/80">{sel.dock.target}</p></div>
                  <div><p className="text-[10px] text-rose-300/25 mb-0.5">Score</p><p className="text-xl font-bold text-rose-300/80">{sel.dock.score ?? "Pending"} <span className="text-[10px] text-rose-300/25">{sel.dock.score == null ? "" : "kcal/mol"}</span></p></div>
                  <div><p className="text-[10px] text-rose-300/25 mb-0.5">Pose</p><p className="text-[12px] text-rose-100/70">{sel.dock.pose}</p></div>
                  <div><p className="text-[10px] text-rose-300/25 mb-0.5">RMSD</p><p className="text-[12px] text-rose-100/70">{sel.dock.rmsd ?? "Pending"}</p></div>
                </div>
              </Card>
              <Card className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-4 rounded-xl">
                <h3 className="text-[12px] font-semibold text-rose-100/80 mb-2">Binding Affinity</h3>
                <div className="relative h-6 bg-gradient-to-r from-red-400/10 via-amber-400/10 to-emerald-400/10 rounded-lg overflow-hidden">
                  <div className="absolute top-0 bottom-0 w-1 bg-rose-300/80 rounded" style={{ left: `${Math.min(100, (Math.abs(sel.dock.score || 0) / 12) * 100)}%` }} />
                </div>
                <div className="flex justify-between mt-1 text-[9px] text-rose-300/20">
                  <span>Weak (0)</span><span>Moderate (-6)</span><span>Strong (-12)</span>
                </div>
              </Card>
            </TabsContent>

            <TabsContent value="admet" className="mt-0 space-y-2">
              {[
                { label: "Solubility", value: sel.admet.solubility, icon: Beaker },
                { label: "Permeability", value: sel.admet.permeability, icon: Activity },
                { label: "CYP3A4", value: sel.admet.cyp3a4, icon: Shield },
                { label: "hERG Liability", value: sel.admet.herg, icon: Activity },
                { label: "Hepatotoxicity", value: sel.admet.hepatotox, icon: Shield },
                { label: "BBB Penetration", value: sel.admet.bbb, icon: Target },
              ].map((item, i) => (
                <Card key={i} className="bg-rose-500/[0.03] backdrop-blur-xl border-rose-500/[0.06] p-3.5 rounded-xl">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg bg-rose-400/[0.06] flex items-center justify-center">
                        <item.icon className="w-3.5 h-3.5 text-rose-300/40" />
                      </div>
                      <span className="text-[12px] font-medium text-rose-100/70">{item.label}</span>
                    </div>
                    <span className={`text-[12px] font-semibold ${admetColor(item.value)}`}>{item.value}</span>
                  </div>
                </Card>
              ))}
            </TabsContent>
          </ScrollArea>
        </Tabs>
        </>
        )}
      </div>
    </div>
  );
}
