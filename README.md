# Drug Discovery ReAct Agent

An agentic AI system for drug discovery research. Combines a LangChain ReAct agent with RAG (FAISS + ChromaDB), real molecular docking (AutoDock Vina), and live biomedical APIs (ChEMBL, PubMed, PDB) — all surfaced through a React frontend with 3D molecular visualization.

```
app/
├── backend/   Flask API — agent, RAG, docking pipeline, biomedical tools
└── frontend/  React + Vite — chat UI, molecular viewer, RAG explorer, paper graph
```

---

## Windows Quick Start

1. Install prerequisites: [Python 3.11](https://www.python.org/downloads/release/python-3110/), [Node.js 18+](https://nodejs.org), AutoDock Vina + Open Babel (see below)
2. Double-click **`start.bat`** in the project root
3. On first run it will ask for your `GROQ_API_KEY` and `GEMINI_API_KEY` — paste them in and press Enter
4. Browser opens automatically at `http://localhost:5173`

Keys are saved to `app/backend/.env` — subsequent runs skip the prompt.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11 |
| Node.js | 18+ |
| npm | any |
| AutoDock Vina | 1.2+ |
| Open Babel | 3.x |

### Install AutoDock Vina + Open Babel

**macOS**
```bash
brew install open-babel
# Download Vina binary from https://github.com/ccsb-scripps/AutoDock-Vina/releases
# Copy to /opt/homebrew/bin/vina and make executable:
chmod +x /opt/homebrew/bin/vina
```

**Linux (Ubuntu/Debian)**
```bash
sudo apt install openbabel
# Download Vina binary from https://github.com/ccsb-scripps/AutoDock-Vina/releases
chmod +x vina_1.2.x_linux_x86_64
sudo mv vina_1.2.x_linux_x86_64 /usr/local/bin/vina
```

**Windows**
```powershell
# Install Open Babel from https://github.com/openbabel/openbabel/releases
# Download the Windows installer (.exe) and run it
# Then download vina_1.2.x_win.exe from https://github.com/ccsb-scripps/AutoDock-Vina/releases
# Rename to vina.exe and place in C:\tools\ (or any folder in your PATH)
# Add that folder to PATH: System Properties > Environment Variables > Path > New
```

---

## 1. Clone

```bash
git clone https://github.com/sidran1310/AgenticAi_RAG_DrugDiscovery_actuallyworking.git
cd AgenticAi_RAG_DrugDiscovery_actuallyworking
```

---

## 2. Backend Setup

**macOS / Linux**
```bash
cd app/backend

python3.11 -m venv venv
source venv/bin/activate

pip install -r requirements-no-gpu.txt

cp .env.example .env
# Edit .env and add your API keys
```

**Windows (Command Prompt or PowerShell)**
```powershell
cd app\backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements-no-gpu.txt

copy .env.example .env
# Open .env in Notepad and add your API keys
```

### API Keys

| Key | Required | Where to get |
|-----|----------|--------------|
| `GEMINI_API_KEY` | Compulsory | aistudio.google.com |
| `GROQ_API_KEY` | Compulsory | console.groq.com |
| `PUBMED_API_KEY` | Optional | ncbi.nlm.nih.gov/account |
| `NCBI_API_KEY` | Optional | ncbi.nlm.nih.gov/account |

ChEMBL and PDB are public APIs — no key needed.

### Run backend

**macOS / Linux**
```bash
source venv/bin/activate
python app.py
```

**Windows**
```powershell
venv\Scripts\activate
python app.py
```

---

## 3. Frontend Setup

**macOS / Linux**
```bash
cd app/frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

**Windows**
```powershell
cd app\frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser. The frontend proxies `/api` requests to the backend at `localhost:5001` automatically.

---

## Project Structure

```
app/backend/
├── app.py               # Flask entry point
├── api/                 # Route handlers
├── modules/             # Core logic (docking, RAG, APIs, agent)
│   ├── docking.py       # AutoDock Vina pipeline
│   ├── rag_database.py  # FAISS + ChromaDB
│   ├── chembl_api.py    # ChEMBL compound search
│   ├── pubmed_api.py    # PubMed literature search
│   ├── pdb_api.py       # RCSB PDB structure search
│   └── langchain_agents.py  # LangChain ReAct agent
├── services/            # Business logic layer
├── models/              # Pydantic request/response models
├── middleware/          # Rate limiting, CORS, logging
└── database/            # SQLite session/chat history (auto-created)

app/frontend/
├── src/
│   ├── components/      # AgentChat, MolecularViewer, RAGExplorer, etc.
│   ├── contexts/        # GlobalQueryContext (cross-panel state)
│   ├── lib/             # API client, config
│   └── pages/           # Index (main layout)
└── vite.config.ts       # Proxy config for /api → localhost:5001
```

---

## Troubleshooting

**Backend won't start — import errors**
Make sure the venv is active: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)

**Docking returns no results**
Check `vina` and `obabel` are in PATH:
```bash
which vina && which obabel      # Mac/Linux
where vina & where obabel       # Windows
```