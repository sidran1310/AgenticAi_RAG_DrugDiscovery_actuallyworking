import os
import nltk
from dotenv import load_dotenv
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from pubmed_api import get_pubmed
from pdb_api import search_pdb
from pubchem_api import get_pubchem
from ncbi_api import get_gene
from downloader import download_structures
from groq_api import initialize_groq, ask_groq
from rag_database import (
    fetch_pubmed_abstracts,
    create_vector_database,
    search_vector_database
)

# ============================
# Load environment variables
# ============================

load_dotenv()

# ============================
# Download NLTK data (first time only)
# ============================

nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)
nltk.download("stopwords", quiet=True)


# ============================
# NLP-based topic extraction using NLTK
# ============================

def extract_topic_nlp(question):
    tokens = word_tokenize(question)
    tagged = pos_tag(tokens)
    stop_words = set(stopwords.words("english"))
    generic = {"role", "effect", "use", "function", "discovery", "research", "study"}

    nouns = []
    for word, tag in tagged:
        if tag in ("NN", "NNP", "NNS", "NNPS"):
            if word.lower() not in stop_words and word.lower() not in generic:
                nouns.append(word)

    if nouns:
        return max(nouns, key=len)

    for word, tag in tagged:
        if word.lower() not in stop_words and word.isalpha():
            return word

    return question.split()[0]


# ============================
# Main Agent Loop
# ============================

def run_agent():

    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        print("ERROR: GROQ_API_KEY not found in .env file")
        return

    print("\nInitializing Groq AI...")
    groq_client = initialize_groq(api_key)
    print("Groq ready.")

    print("\n=== AgentDKI Drug Discovery Research Assistant ===")
    print("Powered by PubMed + PDB + PubChem + NCBI + RAG + NLTK + Groq AI\n")

    while True:

        question = input("\nAsk a biomedical question (type 'exit' to stop): ").strip()

        if question.lower() == "exit":
            print("Goodbye!")
            break

        if not question:
            print("Please enter a valid question.")
            continue

        # Step 1: Extract topic using NLTK
        topic = extract_topic_nlp(question)
        print(f"\n[NLTK] Extracted search topic: '{topic}'")

        # ============================
        # Step 2: PubMed Search
        # ============================
        print(f"\n[PubMed] Searching for papers on: {topic}")
        pubmed_ids = get_pubmed(topic)

        if pubmed_ids:
            print(f"[PubMed] Found {len(pubmed_ids)} paper IDs:")
            for pid in pubmed_ids[:5]:
                print(f"  - https://pubmed.ncbi.nlm.nih.gov/{pid}/")
        else:
            print("[PubMed] No papers found.")

        # ============================
        # Step 3: PDB Structure Search
        # ============================
        print(f"\n[PDB] Searching protein structures for: {topic}")
        pdb_ids = search_pdb(topic)

        if pdb_ids:
            print(f"[PDB] Found {len(pdb_ids)} structures:")
            for pdb in pdb_ids:
                print(f"  - https://www.rcsb.org/structure/{pdb}")

            print("\n[PDB] Downloading structure files...")
            downloaded = download_structures(pdb_ids)
            print(f"[PDB] Downloaded {len(downloaded)} files:")
            for f in downloaded:
                print(f"  - {f}")
        else:
            print("[PDB] No structures found.")
            pdb_ids = []

        # ============================
        # Step 4: PubChem Compound Info
        # ============================
        print(f"\n[PubChem] Fetching compound info for: {topic}")
        compound_data = get_pubchem(topic)

        if compound_data:
            print(f"[PubChem] Compound: {compound_data['compound']}")
            print(f"[PubChem] Formula:  {compound_data['formula']}")
            print(f"[PubChem] Weight:   {compound_data['weight']} g/mol")
        else:
            print("[PubChem] No compound data found.")

        # ============================
        # Step 5: NCBI Gene Info
        # ============================
        print(f"\n[NCBI] Searching gene info for: {topic}")
        gene_id = get_gene(topic)

        if gene_id:
            print(f"[NCBI] Gene ID: {gene_id}")
            print(f"[NCBI] Link: https://www.ncbi.nlm.nih.gov/gene/{gene_id}")
        else:
            print("[NCBI] No gene found.")

        # ============================
        # Step 6: RAG - Fetch Abstracts
        # ============================
        print(f"\n[RAG] Fetching abstracts for knowledge base...")
        abstracts = fetch_pubmed_abstracts(pubmed_ids)

        if not abstracts:
            print("[RAG] Could not retrieve abstracts.")
            continue

        print(f"[RAG] Retrieved {len(abstracts)} abstracts.")
        print("[RAG] Building knowledge base...")
        index, texts, metadata = create_vector_database(abstracts)
        print(f"[RAG] Knowledge base ready with {len(texts)} documents.")

        results = search_vector_database(question, index, texts, metadata, top_k=5)
        context = "\n\n".join([
            item.get("abstract") or item.get("content") or item.get("text", "")
            for item in results
        ])

        # ============================
        # Step 7: Groq AI Answer
        # ============================
        print("\n[Groq] Generating AI answer...\n")
        answer = ask_groq(
            groq_client,
            context,
            question,
            compound_data=compound_data,
            gene_id=gene_id,
            pdb_ids=pdb_ids
        )

        print("=" * 60)
        print("SCIENTIFIC ANSWER")
        print("=" * 60)
        print(answer)

        # ============================
        # Structured Data Summary
        # ============================
        print("\n--- Compound Data ---")
        if compound_data:
            print(f"{topic.capitalize()} — Formula: {compound_data['formula']}, "
                  f"Weight: {compound_data['weight']} g/mol")
        else:
            print("No compound data available.")

        print("\n--- Gene Association ---")
        if gene_id:
            print(f"NCBI Gene ID: {gene_id}")
            print(f"Link: https://www.ncbi.nlm.nih.gov/gene/{gene_id}")
        else:
            print("No gene data available.")

        print("\n--- Protein Structures ---")
        if pdb_ids:
            for pdb in pdb_ids:
                print(f"  - {pdb}: https://www.rcsb.org/structure/{pdb}")
        else:
            print("No protein structures found.")

        print("\n" + "=" * 60)


if __name__ == "__main__":
    run_agent()
import os
import sys
from dotenv import load_dotenv

# 1. Setup Environment and Pathing
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))

# Import the "Arms" (Tools) and the "Brain" (LLM)
from modules.tool_agent import decide_tools, generate_plan, synthesize_answer
from openai import OpenAI

class Sem8Agent:
    def __init__(self):
        # Using OpenAI client with Gemini API
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        ) if api_key else None
        
        self.system_prompt = """
        You are a Senior Bioinformatics AI Agent specialized in 2023-2026 Drug Discovery research.
        Your goal is to provide deep scientific insights and 3D visualizations.
        
        AVAILABLE TOOLS:
        - search_papers: Searches PubMed for 2023 literature.
        - get_chemical_info: Gets SMILES and molecular weight from PubChem.
        - visualize_docking: Launches UCSF Chimera for 3D docking.
        
        PROCESS:
        1. THOUGHT: What do I need to do?
        2. ACTION: Which tool should I call?
        3. OBSERVATION: What did the tool return?
        4. FINAL ANSWER: Summarize findings for the user.
        """

    def run(self, user_query):
        print(f"\n🚀 [MAIN AGENT] Starting Task: {user_query}")
        
        if not self.client:
            return "❌ GEMINI_API_KEY not found in .env file!"
        
        # Step 1: Initial Thought & Strategy
        print("🧠 [THOUGHT] Analyzing question and selecting tools...")
        selected_tools = decide_tools(user_query)
        
        plan = generate_plan(user_query, selected_tools, self.client)
        print(f"📋 [PLAN]\n{plan}")

        # Step 2: Synthesis Phase
        collected_data = {
            "pubmed_abstracts": [],
            "compound_data": None,
            "docking_results": []
        }
        
        final_answer = synthesize_answer(user_query, collected_data, self.client)
        return final_answer


# --- Main Execution Block ---
if __name__ == "__main__":
    agent = Sem8Agent()
    
    print("--- Welcome to the Agentic Drug Discovery Platform (2026) ---")
    query = input("Ask a drug discovery question (e.g., 'Research Ibuprofen and show docking'): ")
    
    if query:
        response = agent.run(query)
        print("\n" + "="*50)
        print("FINAL AGENT RESPONSE:")
        print(response)
        print("="*50)
    else:
        print("No query provided. Exiting.")
