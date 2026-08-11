"""
rag_pipeline.py — Hybrid retrieval (vector + BM25) for career knowledge base.

Architecture:
- fastembed (BAAI/bge-small-en-v1.5): ONNX-based, ~130MB, no torch needed
- ChromaDB EphemeralClient: in-memory, rebuilt at every app start from career_data.json
- BM25Okapi (rank_bm25): keyword-based retrieval to complement semantic search
- Hybrid merge: 0.6 * vector_score + 0.4 * bm25_score for reranking

The dataset is ~17 records / ~20KB so startup embedding takes < 5 seconds.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Module-level singletons — initialized once at app startup
_chroma_collection = None
_bm25_index = None
_bm25_documents: list[str] = []
_bm25_metadata: list[dict] = []
_embedder = None
_career_data: list[dict] = []

CAREER_DATA_PATH = Path(__file__).parent.parent / "data" / "career_data.json"


def _get_embedder():
    global _embedder
    if _embedder is None:
        logger.info("Loading fastembed model BAAI/bge-small-en-v1.5...")
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        logger.info("fastembed model loaded.")
    return _embedder


def _build_document_text(record: dict) -> str:
    """Compose a single text document from all career record fields."""
    skills = ", ".join(record.get("skills", []))
    tools = ", ".join(record.get("tools", []))
    responsibilities = " ".join(record.get("responsibilities", []))
    return (
        f"Title: {record.get('title', '')}\n"
        f"Description: {record.get('description', '')}\n"
        f"Skills: {skills}\n"
        f"Tools: {tools}\n"
        f"Responsibilities: {responsibilities}\n"
        f"Salary: {record.get('salary_range', '')}\n"
        f"Future Scope: {record.get('future_scope', '')}"
    )


def initialize_rag() -> None:
    """
    Build the in-memory vector store and BM25 index from career_data.json.
    Called once at app startup. Safe to call multiple times (idempotent).
    """
    global _chroma_collection, _bm25_index, _bm25_documents, _bm25_metadata, _career_data

    if _chroma_collection is not None:
        logger.info("RAG already initialized, skipping.")
        return

    logger.info("Initializing RAG pipeline from career_data.json...")

    # Load career data
    with open(CAREER_DATA_PATH, "r", encoding="utf-8") as f:
        _career_data = json.load(f)

    # Build document texts
    all_texts = []
    all_ids = []
    all_meta = []

    for record in _career_data:
        text = _build_document_text(record)
        all_texts.append(text)
        all_ids.append(record.get("id", str(len(all_texts))))
        all_meta.append({
            "id": record.get("id", ""),
            "title": record.get("title", ""),
            "salary_range": record.get("salary_range", ""),
        })

    # ── ChromaDB EphemeralClient (in-memory) ──────────────────────────────────
    import chromadb
    client = chromadb.EphemeralClient()
    collection = client.create_collection(
        name="careers",
        metadata={"hnsw:space": "cosine"},
    )

    # Batch embed all documents with fastembed
    embedder = _get_embedder()
    logger.info(f"Embedding {len(all_texts)} career documents...")
    embeddings = list(embedder.embed(all_texts))
    embedding_lists = [e.tolist() for e in embeddings]

    collection.add(
        ids=all_ids,
        documents=all_texts,
        embeddings=embedding_lists,
        metadatas=all_meta,
    )
    _chroma_collection = collection
    logger.info(f"ChromaDB collection built: {len(all_texts)} documents.")

    # ── BM25 index ────────────────────────────────────────────────────────────
    from rank_bm25 import BM25Okapi
    tokenized = [text.lower().split() for text in all_texts]
    _bm25_index = BM25Okapi(tokenized)
    _bm25_documents = all_texts
    _bm25_metadata = all_meta
    logger.info("BM25 index built.")


def retrieve_relevant_careers(query: str, n_results: int = 5) -> list[str]:
    """
    Hybrid retrieval: semantic vector search + BM25 keyword search.
    Returns top-N merged and reranked document texts.
    """
    if _chroma_collection is None or _bm25_index is None:
        logger.warning("RAG not initialized. Call initialize_rag() first.")
        return []

    n_candidates = n_results + 3  # fetch extra for reranking

    # ── Vector search ─────────────────────────────────────────────────────────
    embedder = _get_embedder()
    query_embedding = list(embedder.embed([query]))[0].tolist()

    vector_results = _chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_candidates, len(_bm25_documents)),
        include=["documents", "distances", "metadatas"],
    )

    vector_docs = vector_results["documents"][0]
    vector_distances = vector_results["distances"][0]  # cosine distance (lower = better)

    # Convert to similarity scores (0–1, higher = better)
    vector_scores = {doc: max(0.0, 1.0 - dist) for doc, dist in zip(vector_docs, vector_distances)}

    # ── BM25 search ───────────────────────────────────────────────────────────
    tokenized_query = query.lower().split()
    bm25_scores_raw = _bm25_index.get_scores(tokenized_query)

    # Normalize BM25 scores to 0–1
    max_bm25 = max(bm25_scores_raw) if max(bm25_scores_raw) > 0 else 1
    normalized_bm25 = {
        _bm25_documents[i]: bm25_scores_raw[i] / max_bm25
        for i in range(len(_bm25_documents))
    }

    # ── Hybrid merge ──────────────────────────────────────────────────────────
    all_doc_set = set(vector_scores.keys()) | set(
        doc for doc, s in normalized_bm25.items() if s > 0.05
    )

    scored = []
    for doc in all_doc_set:
        v_score = vector_scores.get(doc, 0.0)
        b_score = normalized_bm25.get(doc, 0.0)
        combined = 0.6 * v_score + 0.4 * b_score
        scored.append((combined, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:n_results]]


def get_career_by_id(career_id: str) -> Optional[dict]:
    """Return raw career record by ID."""
    for career in _career_data:
        if career.get("id") == career_id:
            return career
    return None


def get_all_careers() -> list[dict]:
    """Return all career records."""
    return _career_data


def find_matching_careers(skills: list[str], top_n: int = 5) -> list[dict]:
    """
    Match careers against a user's skill set.
    Returns careers sorted by match percentage (highest first).
    """
    if not skills or not _career_data:
        return _career_data[:top_n]

    skills_lower = {s.lower() for s in skills}
    results = []

    for career in _career_data:
        required = [s.lower() for s in career.get("skills", [])]
        if not required:
            continue
        matched = sum(1 for s in required if s in skills_lower)
        # Also check partial matches (e.g. "machine learning" in "machine learning engineer")
        partial = sum(
            1 for s in required
            if any(word in s for word in skills_lower if len(word) > 3)
        )
        match_pct = round((matched / len(required)) * 100)
        # Boost with partial matches (up to 20% bonus)
        boosted = min(100, match_pct + min(20, int((partial / len(required)) * 20)))

        results.append({
            **career,
            "match_percentage": boosted,
            "matched_skills": [s for s in career.get("skills", []) if s.lower() in skills_lower],
            "missing_skills": [s for s in career.get("skills", []) if s.lower() not in skills_lower],
        })

    results.sort(key=lambda x: x["match_percentage"], reverse=True)
    return results[:top_n]
