# Drug Discovery ReAct Agent Dashboard - Development Plan

## Design Guidelines

### Design References
- **IBM Watson Drug Discovery**: Clean data-driven interface
- **BenchSci**: Scientific search with structured results
- **Style**: Dark Scientific Dashboard + Neon Accents + Data-Dense Layouts

### Color Palette
- Primary Background: #0F172A (Slate 900 - deep navy)
- Secondary Background: #1E293B (Slate 800 - cards)
- Tertiary: #334155 (Slate 700 - borders/dividers)
- Accent Primary: #06B6D4 (Cyan 500 - actions/highlights)
- Accent Secondary: #8B5CF6 (Violet 500 - agent reasoning)
- Accent Success: #10B981 (Emerald 500 - success states)
- Accent Warning: #F59E0B (Amber 500 - observations)
- Accent Error: #EF4444 (Red 500 - errors)
- Text Primary: #F1F5F9 (Slate 100)
- Text Secondary: #94A3B8 (Slate 400)

### Typography
- Headings: Inter font-weight 700
- Body: Inter font-weight 400
- Code/Data: JetBrains Mono font-weight 400
- Labels: Inter font-weight 600 uppercase tracking-wider

### Key Component Styles
- Cards: Slate 800 bg, 1px border slate-700, 12px rounded, subtle glow on hover
- Buttons: Cyan 500 bg, white text, 8px rounded, hover: brighten
- Badges: Semi-transparent backgrounds with colored text
- Chat bubbles: Distinct colors for Thought (violet), Action (cyan), Observation (amber), Answer (emerald)

### Images to Generate
1. **hero-drug-discovery-molecules.jpg** - Abstract molecular structures floating in dark space with cyan/violet glowing connections, scientific visualization (Style: 3d, dark background)
2. **bg-neural-network-pattern.jpg** - Abstract neural network pattern with glowing nodes and connections on dark background, AI/science theme (Style: 3d, dark)
3. **icon-molecular-docking.jpg** - 3D molecular docking visualization showing protein-ligand interaction with glowing highlights (Style: 3d, scientific)
4. **bg-research-data-flow.jpg** - Abstract data flow visualization with streams of light representing information processing, dark scientific theme (Style: 3d, futuristic)

---

## Development Tasks

### Files to Create (8 files max)

1. **src/pages/Index.tsx** - Main dashboard layout with sidebar navigation and content area
2. **src/components/AgentChat.tsx** - ReAct agent chat interface with reasoning chain display (Thought/Action/Observation/Answer)
3. **src/components/ToolPanel.tsx** - Tool integration panel showing ChEMBL, PubMed, NCBI, Gemini, Docking tools
4. **src/components/RAGExplorer.tsx** - RAG knowledge base explorer with document search and retrieval results
5. **src/components/MolecularViewer.tsx** - Compound search and molecular property display
6. **src/components/ResearchSummary.tsx** - Research findings dashboard with filterable results
7. **src/components/AgentMemory.tsx** - Agent memory state and planning visualization
8. **public/ARCHITECTURE_GUIDE.md** - Python backend architecture guide with full code structure

### Implementation Notes
- All components use mock/demo data to showcase the UI
- Dark theme throughout using Tailwind dark classes
- Responsive design for desktop-first with tablet support
- Sidebar navigation to switch between panels
- The chat interface is the primary view