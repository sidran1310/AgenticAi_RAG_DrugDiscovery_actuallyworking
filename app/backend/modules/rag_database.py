import html
import math
import os
import re
import xml.etree.ElementTree as ET
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from pubmed_api import get_pubmed


EUTILS_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
_DOCUMENTS: List[Dict[str, Any]] = []
_VECTORS: List[Counter] = []


def _tokens(text: str) -> List[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z][a-zA-Z0-9\-]{2,}", (text or "").lower())
        if token not in {"the", "and", "for", "with", "from", "that", "this", "into", "were", "are"}
    ]


def _vector(text: str) -> Counter:
    return Counter(_tokens(text))


def _cosine(left: Counter, right: Counter) -> float:
    if not left or not right:
        return 0.0
    shared = set(left) & set(right)
    numerator = sum(left[key] * right[key] for key in shared)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def _text_at(element: Optional[ET.Element], path: str) -> str:
    found = element.find(path) if element is not None else None
    if found is None:
        return ""
    return "".join(found.itertext()).strip()


def _parse_article(article: ET.Element, pmid_hint: str) -> Optional[Dict[str, Any]]:
    medline = article.find("MedlineCitation")
    article_node = medline.find("Article") if medline is not None else None
    if article_node is None:
        return None

    pmid = _text_at(medline, "PMID") or pmid_hint
    title = html.unescape(_text_at(article_node, "ArticleTitle"))
    abstract_parts = [
        html.unescape("".join(node.itertext()).strip())
        for node in article_node.findall("Abstract/AbstractText")
    ]
    abstract = " ".join(part for part in abstract_parts if part)
    if not abstract:
        return None

    journal = _text_at(article_node, "Journal/Title") or _text_at(article_node, "Journal/ISOAbbreviation")
    year = (
        _text_at(article_node, "Journal/JournalIssue/PubDate/Year")
        or _text_at(article_node, "Journal/JournalIssue/PubDate/MedlineDate")[:4]
    )
    authors = []
    for author in article_node.findall("AuthorList/Author")[:6]:
        last = _text_at(author, "LastName")
        initials = _text_at(author, "Initials")
        if last:
            authors.append(f"{last} {initials}".strip())

    doi = ""
    for article_id in article.findall("PubmedData/ArticleIdList/ArticleId"):
        if article_id.attrib.get("IdType") == "doi":
            doi = (article_id.text or "").strip()
            break

    return {
        "id": pmid,
        "pubmed_id": pmid,
        "title": title or f"PubMed {pmid}",
        "abstract": abstract,
        "content": abstract,
        "year": year or "",
        "publication_date": f"{year}-01-01" if year else "",
        "journal": journal or "Unknown journal",
        "authors": ", ".join(authors) if authors else "Unknown authors",
        "doi": doi or None,
        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "source": "PubMed",
    }


def fetch_pubmed_abstracts(pubmed_ids: Iterable[str]) -> List[Dict[str, Any]]:
    """Fetch PubMed abstracts in one XML request and return normalized documents."""
    ids = [str(pid).strip() for pid in pubmed_ids if str(pid).strip()]
    if not ids:
        return []

    params = {
        "db": "pubmed",
        "id": ",".join(ids[:100]),
        "retmode": "xml",
        "rettype": "abstract",
    }
    api_key = os.getenv("NCBI_API_KEY") or os.getenv("PUBMED_API_KEY")
    if api_key:
        params["api_key"] = api_key

    try:
        response = requests.get(EUTILS_FETCH_URL, params=params, timeout=20)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        docs = []
        for article in root.findall(".//PubmedArticle"):
            parsed = _parse_article(article, "")
            if parsed:
                docs.append(parsed)
        return docs
    except Exception as exc:
        print(f"[RAG] PubMed abstract fetch failed: {exc}")
        return []


def create_vector_database(documents_or_ids: Iterable[Any]) -> Tuple[List[Dict[str, Any]], List[Counter], List[Dict[str, Any]]]:
    """Create an in-memory lexical vector index.

    The public contract intentionally mirrors the old FAISS helper while avoiding
    runtime model downloads. Callers can pass PubMed IDs or already fetched docs.
    """
    global _DOCUMENTS, _VECTORS

    items = list(documents_or_ids or [])
    if not items:
        _DOCUMENTS, _VECTORS = [], []
        return _DOCUMENTS, _VECTORS, []

    if isinstance(items[0], dict):
        docs = [item for item in items if item.get("abstract") or item.get("content")]
    else:
        docs = fetch_pubmed_abstracts(items)

    _DOCUMENTS = docs
    _VECTORS = [_vector(f"{doc.get('title', '')} {doc.get('abstract') or doc.get('content', '')}") for doc in docs]
    metadata = [
        {
            "id": doc.get("pubmed_id") or doc.get("id"),
            "title": doc.get("title"),
            "year": doc.get("year"),
            "journal": doc.get("journal"),
            "authors": doc.get("authors"),
        }
        for doc in docs
    ]
    return _DOCUMENTS, _VECTORS, metadata


def search_vector_database(
    query: str,
    index: Optional[Any] = None,
    texts: Optional[Any] = None,
    metadata: Optional[Any] = None,
    top_k: Optional[int] = None,
    n_results: Optional[int] = None,
    year_filter: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Search the local RAG index, lazily building one from PubMed if needed."""
    limit = max(1, min(int(n_results or top_k or 5), 25))
    query = (query or "").strip()
    if not query:
        return []

    if not _DOCUMENTS:
        ids = get_pubmed(query, max_results=min(limit * 3, 30))
        create_vector_database(ids)

    query_vec = _vector(query)
    ranked = []
    for doc, vector in zip(_DOCUMENTS, _VECTORS):
        if year_filter and doc.get("year"):
            try:
                if int(str(doc["year"])[:4]) < year_filter:
                    continue
            except ValueError:
                pass
        score = _cosine(query_vec, vector)
        if score > 0:
            enriched = dict(doc)
            enriched["similarity_score"] = round(score, 4)
            enriched["score"] = round(score, 4)
            ranked.append(enriched)

    ranked.sort(key=lambda item: item.get("similarity_score", 0), reverse=True)
    return ranked[:limit]
