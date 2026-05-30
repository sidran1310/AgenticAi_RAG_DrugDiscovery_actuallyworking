import os
from dotenv import load_dotenv
import httpx

load_dotenv()

BASE_URL = "https://generativelanguage.googleapis.com/v1beta2"
DEFAULT_MODEL = "gemini-3.5-pro"


def initialize_gemini(api_key: str, model: str = None):
    if not api_key:
        raise ValueError("GEMINI_API_KEY is required to initialize Gemini.")
    return {
        "api_key": api_key,
        "model": model or DEFAULT_MODEL,
    }


def ask_gemini(client, context, question, compound_data=None, gene_id=None, pdb_ids=None):
    extra = ""

    if compound_data:
        extra += f"\nCompound: {compound_data.get('compound', 'unknown')}, Formula: {compound_data.get('formula', 'unknown')}, Weight: {compound_data.get('weight', 'unknown')} g/mol"

    if gene_id:
        extra += f"\nAssociated Gene ID (NCBI): {gene_id}"

    if pdb_ids:
        extra += f"\nRelated PDB Structures: {', '.join(pdb_ids)}"

    prompt = f"""
You are a biomedical research assistant specializing in drug discovery.

Context from recent scientific literature:
{context}

Additional structured data:
{extra}

Question:
{question}

Instructions:
- Answer in a clear, expert scientific style.
- Use the context and structured data above to support your response.
- Mention the compound formula, molecular weight, gene ID, and protein structures when relevant.
- Keep the answer between 5 and 8 sentences.
- Prefer fluent paragraphs; avoid bullet-point lists unless required.
"""

    url = f"{BASE_URL}/models/{client['model']}:generateText"
    headers = {
        "Authorization": f"Bearer {client['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "prompt": {
            "text": prompt,
        },
        "temperature": 0.4,
        "maxOutputTokens": 1024,
    }

    try:
        with httpx.Client(timeout=30.0) as http:
            response = http.post(url, json=body, headers=headers)
            response.raise_for_status()
            payload = response.json()

        candidate = None
        if isinstance(payload, dict):
            candidates = payload.get("candidates") or payload.get("results")
            if isinstance(candidates, list) and candidates:
                first = candidates[0]
                candidate = first.get("output") or first.get("content") or first.get("text")

            if not candidate:
                candidate = payload.get("output") or payload.get("text")

        return candidate or "Gemini API returned an empty response."

    except Exception as e:
        return f"Gemini API Error: {str(e)}"
