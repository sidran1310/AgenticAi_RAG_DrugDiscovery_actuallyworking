# Project Summary
The Drug Discovery ReAct Agent is a comprehensive web application designed to assist researchers in drug discovery through the integration of advanced AI capabilities, including ReAct reasoning and various biomedical tools. This system facilitates the identification, filtering, and summarization of credible sources, enabling efficient research processes in drug development.

# Project Module Description
The project consists of several functional modules, each serving distinct purposes:
- **Agent Chat**: An interactive interface for users to engage with the ReAct agent, input queries, and receive synthesized responses.
- **Tool Panel**: Displays connected biomedical tools and their operational status, allowing users to understand available resources.
- **RAG Explorer**: A knowledge base viewer for searching and retrieving indexed documents from the RAG pipeline.
- **Molecular Viewer**: Allows users to browse and analyze compounds, including their properties and docking results.
- **Research Summary**: Aggregates findings from literature, providing AI-curated summaries and credibility scores.
- **Agent Memory**: Visualizes the agent's memory state, planning strategies, and reasoning paths.

# Directory Tree
```
app/frontend/
├── README.md                    # Project overview and setup instructions
├── components.json              # Component metadata
├── eslint.config.js             # ESLint configuration
├── index.html                   # Main HTML file for the frontend
├── package.json                 # Project dependencies and scripts
├── postcss.config.js            # PostCSS configuration
├── public/
│   ├── ARCHITECTURE_GUIDE.md    # Architecture guide for the Python backend
│   ├── favicon.svg               # Favicon for the application
│   └── robots.txt               # Robots.txt for web crawlers
├── seo-scripts/
│   ├── build.js                  # Build script for SEO
│   ├── convert-blog-to-html.js   # Script to convert blog posts to HTML
│   ├── generate-sitemap.js       # Sitemap generation script
│   └── marked.esm.js            # Marked library for markdown parsing
├── site.config.json             # Configuration for the site
├── src/
│   ├── App.css                  # Global CSS styles
│   ├── App.tsx                  # Main application component
│   ├── components/              # React components
│   ├── hooks/                   # Custom React hooks
│   ├── lib/                     # Utility functions and API calls
│   ├── main.tsx                 # Application entry point
│   ├── pages/                   # Page components
│   ├── vite-env.d.ts            # TypeScript environment definitions
│   └── ...                      # Other source files
├── tailwind.config.ts           # Tailwind CSS configuration
├── template_config.json         # Template configuration
├── todo.md                      # Development tasks and notes
├── tsconfig.app.json            # TypeScript configuration for the app
└── vite.config.ts               # Vite configuration for the project
```

# File Description Inventory
- **README.md**: Provides an overview and instructions for setting up the project.
- **ARCHITECTURE_GUIDE.md**: Details the architecture and code structure for the backend.
- **index.html**: The HTML entry point for the application.
- **package.json**: Lists project dependencies and scripts for building and running the application.
- **src/**: Contains all source code files, including React components and utility functions.

# Technology Stack
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, LangChain, FAISS, ChromaDB, Gemini API, Whisper
- **Deployment**: Docker (for containerization)

# Usage
To set up and run the project:
1. **Install dependencies**:
   ```bash
   cd app/frontend
   pnpm install
   ```
2. **Build the project**:
   ```bash
   pnpm run build
   ```
3. **Run the application**:
   ```bash
   pnpm run dev
   ```
