import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def initialize_groq(api_key):
    client = Groq(api_key=api_key)
    return client


def ask_groq(client, context, question, compound_data=None, gene_id=None, pdb_ids=None):

    # Build extra structured info
    extra = ""

    if compound_data:
        compound_name = compound_data.get("compound") or compound_data.get("name", "Unknown compound")
        formula = compound_data.get("formula", "unknown formula")
        weight = compound_data.get("weight") or compound_data.get("molecular_weight", "unknown weight")
        extra += f"\nCompound: {compound_name}, Formula: {formula}, Weight: {weight} g/mol"

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
    - Write a clear, fluent scientific paragraph answering the question.
    - Use only the context and structured data above to support your answer.
    - Mention compound formula, molecular weight, gene, or protein structures only when those fields are explicitly present in the structured data.
    - If a molecular property, gene, or structure is missing, say that it requires confirmation instead of inventing a value.
    - Do NOT use bullet points. Write in flowing paragraph form only.
    - Keep it between 5 to 8 sentences.
    - Sound like a scientific expert explaining to a researcher.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a biomedical research assistant specializing in drug discovery."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1024,
            temperature=0.7
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"Groq API Error: {str(e)}"
