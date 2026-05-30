import os
from typing import List, Dict, Any, Optional
import requests
from datetime import datetime

EUTILS_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EUTILS_SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
EUTILS_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

def get_pubmed(query: str, max_results: int = 20) -> List[str]:
    """Search PubMed and return a stable list of PMID strings."""
    query = (query or "").strip()
    if not query:
        return []

    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max(1, min(int(max_results or 20), 100)),
        "sort": "relevance",
    }
    api_key = os.getenv("NCBI_API_KEY") or os.getenv("PUBMED_API_KEY")
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(EUTILS_SEARCH_URL, params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
        return payload.get("esearchresult", {}).get("idlist", [])
    except Exception as exc:
        print(f"[PubMed] Search failed for {query!r}: {exc}")
        return []

def get_pubmed_details(pmids: List[str]) -> List[Dict[str, Any]]:
    """Get detailed information for PubMed IDs including abstracts."""
    if not pmids:
        return []

    # Split into batches of 100 (NCBI limit)
    batches = [pmids[i:i + 100] for i in range(0, len(pmids), 100)]
    all_details = []

    api_key = os.getenv("NCBI_API_KEY") or os.getenv("PUBMED_API_KEY")

    for batch in batches:
        try:
            # Get summaries first
            summary_params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "json",
                "rettype": "abstract"
            }
            if api_key:
                summary_params["api_key"] = api_key

            summary_response = requests.get(EUTILS_SUMMARY_URL, params=summary_params, timeout=15)
            summary_response.raise_for_status()
            summary_data = summary_response.json()

            # Get full abstracts
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(batch),
                "retmode": "xml",
                "rettype": "abstract"
            }
            if api_key:
                fetch_params["api_key"] = api_key

            fetch_response = requests.get(EUTILS_FETCH_URL, params=fetch_params, timeout=15)
            fetch_response.raise_for_status()

            # Parse the results
            for pmid in batch:
                detail = {
                    "pmid": pmid,
                    "title": "",
                    "abstract": "",
                    "authors": [],
                    "journal": "",
                    "year": "",
                    "doi": "",
                    "keywords": []
                }

                # Extract from summary
                if "result" in summary_data and pmid in summary_data["result"]:
                    result = summary_data["result"][pmid]
                    detail["title"] = result.get("title", "")
                    detail["journal"] = result.get("source", "")
                    detail["year"] = result.get("pubdate", "")[:4] if result.get("pubdate") else ""

                    # Extract authors
                    authors = result.get("authors", [])
                    if authors:
                        detail["authors"] = [author.get("name", "") for author in authors if author.get("name")]

                    # Extract DOI
                    article_ids = result.get("articleids", [])
                    for aid in article_ids:
                        if aid.get("idtype") == "doi":
                            detail["doi"] = aid.get("value", "")
                            break

                # Extract abstract from fetch (simplified parsing)
                if fetch_response.text:
                    # Basic XML parsing for abstract
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(fetch_response.text)
                        for article in root.findall(".//PubmedArticle"):
                            medline = article.find(".//MedlineCitation")
                            if medline is not None:
                                article_el = medline.find(".//Article")
                                if article_el is not None:
                                    abstract_el = article_el.find(".//Abstract")
                                    if abstract_el is not None:
                                        abstract_text = article_el.find(".//AbstractText")
                                        if abstract_text is not None and abstract_text.text:
                                            detail["abstract"] = abstract_text.text.strip()
                    except:
                        pass  # XML parsing can fail, we'll work with what we have

                all_details.append(detail)

        except Exception as e:
            print(f"[PubMed] Failed to get details for batch: {e}")
            continue

    return all_details

def search_pubmed_advanced(query: str, filters: Dict[str, Any] = None, max_results: int = 20) -> Dict[str, Any]:
    """Advanced PubMed search with filters and detailed results."""
    filters = filters or {}

    # Build advanced query
    advanced_query = query

    # Add date filters
    if "date_from" in filters:
        advanced_query += f" AND ({filters['date_from']}[Date - Publication] : {filters.get('date_to', '3000')}[Date - Publication])"

    # Add journal filters
    if "journal" in filters:
        advanced_query += f" AND {filters['journal']}[Journal]"

    # Add author filters
    if "author" in filters:
        advanced_query += f" AND {filters['author']}[Author]"

    # Add MeSH terms
    if "mesh_terms" in filters:
        mesh_terms = filters["mesh_terms"]
        if isinstance(mesh_terms, list):
            mesh_query = " OR ".join([f'"{term}"[MeSH Terms]' for term in mesh_terms])
            advanced_query += f" AND ({mesh_query})"
        else:
            advanced_query += f' AND "{mesh_terms}"[MeSH Terms]'

    # Add species filter
    if "species" in filters:
        advanced_query += f" AND {filters['species']}[Organism]"

    # Get PMIDs
    pmids = get_pubmed(advanced_query, max_results)

    # Get detailed information
    details = get_pubmed_details(pmids)

    return {
        "query": advanced_query,
        "total_results": len(pmids),
        "results": details,
        "filters_applied": filters
    }
