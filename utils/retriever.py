import logging
from dataclasses import dataclass, field
from typing import List, Optional

from langchain_community.vectorstores import FAISS

from config import Config

logger = logging.getLogger(__name__)

@dataclass
class RetrievedChunk:
    content: str
    source: str
    page: int
    chunk_index: int
    score: float = field(default=0.0)

    @property
    def citation(self) -> str:
        return f"{self.source}, page {self.page}"


def _docs_to_chunks(results_with_scores) -> List[RetrievedChunk]:
    chunks = []
    for doc, score in results_with_scores:
        chunks.append(RetrievedChunk(
            content=doc.page_content,
            source=doc.metadata.get("source", "unknown"),
            page=doc.metadata.get("page_display", doc.metadata.get("page", 0)),
            chunk_index=doc.metadata.get("chunk_index", 0),
            score=float(score),
        ))
    return chunks


def _expand_query(query: str) -> str:
    import re
    eq = query.strip()
    # Match "exp 7" or "exp7" and expand to "experiment 7"
    eq = re.sub(r'\bexp\s*(\d+)\b', r'experiment \1', eq, flags=re.IGNORECASE)
    eq = re.sub(r'\bexps\s*(\d+)\b', r'experiments \1', eq, flags=re.IGNORECASE)
    
    # Standalone common abbreviations
    eq = re.sub(r'\bexp\b', 'experiment', eq, flags=re.IGNORECASE)
    eq = re.sub(r'\bexps\b', 'experiments', eq, flags=re.IGNORECASE)
    eq = re.sub(r'\bfig\b', 'figure', eq, flags=re.IGNORECASE)
    eq = re.sub(r'\bfigs\b', 'figures', eq, flags=re.IGNORECASE)
    eq = re.sub(r'\beq\b', 'equation', eq, flags=re.IGNORECASE)
    eq = re.sub(r'\beqs\b', 'equations', eq, flags=re.IGNORECASE)
    return eq


def rewrite_query_with_llm(query: str) -> str:
    """
    Uses a fast LLM call to rewrite informal, abbreviated, or incomplete user
    queries into clean, descriptive, formal search phrases optimized for RAG.
    """
    try:
        from chatbot.llm import get_llm
        from langchain_core.prompts import ChatPromptTemplate
        
        rewrite_prompt = ChatPromptTemplate.from_template(
            "You are a search query optimizer for technical manuals and documents.\n"
            "Translate the following informal, abbreviated, or incomplete user query into a clean, "
            "search-friendly, formal English query optimized for vector search. "
            "Correct spelling errors, expand abbreviations (e.g. pinout -> pinout configuration diagram), "
            "and make it descriptive. Respond ONLY with the optimized search phrase, nothing else.\n\n"
            "User query: {query}\n"
            "Optimized search query:"
        )
        llm = get_llm()
        messages = rewrite_prompt.format_messages(query=query)
        response = llm.invoke(messages)
        optimized = response.content.strip().strip('"').strip("'").strip()
        if optimized:
            return optimized
    except Exception as exc:
        logger.warning("Query rewriting via LLM failed: %s", exc)
    return query


def retrieve_relevant_chunks(
    vector_store: FAISS,
    query: str,
    top_k: int = Config.TOP_K,
) -> List[RetrievedChunk]:
    """
    Multi-pass retrieval:
      Pass 1 — Pure similarity search on optimized query.
      Pass 2 — Similarity search on a slightly reworded query (add 'explain' prefix).
      Pass 3 — MMR search for diversity (fetch_k candidates, return top_k).
    Merge, deduplicate by content hash, re-rank by score, return top_k.
    """
    if not query or not query.strip():
        return []

    # First expand obvious local abbreviations (instant regex)
    expanded_query = _expand_query(query)
    # Rewrite dynamically using LLM
    optimized_query = rewrite_query_with_llm(expanded_query)
    if optimized_query != query:
        logger.info("Optimized user query %r to search phrase %r", query, optimized_query)

    fetch_k = max(Config.RETRIEVAL_FETCH_K, top_k * 4)
    all_chunks: List[RetrievedChunk] = []

    # Pass 1: Similarity search (primary)
    try:
        results = vector_store.similarity_search_with_score(optimized_query, k=fetch_k)
        all_chunks.extend(_docs_to_chunks(results))
    except Exception as exc:
        logger.warning("Similarity pass failed: %s", exc)

    # Pass 2: Reworded query
    try:
        alt_query = f"explain {optimized_query}"
        results = vector_store.similarity_search_with_score(alt_query, k=top_k)
        all_chunks.extend(_docs_to_chunks(results))
    except Exception as exc:
        logger.warning("Similarity pass 2 failed: %s", exc)

    # Pass 3: MMR for diversity (complementary)
    try:
        mmr_docs = vector_store.max_marginal_relevance_search(
            optimized_query, k=top_k, fetch_k=fetch_k
        )
        # Assign a neutral distance score of 1.3 for MMR-only chunks to prevent
        # them from overriding high-quality similarity matches.
        for doc in mmr_docs:
            all_chunks.append(RetrievedChunk(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                page=doc.metadata.get("page_display", doc.metadata.get("page", 0)),
                chunk_index=doc.metadata.get("chunk_index", 0),
                score=1.3,
            ))
    except Exception as exc:
        logger.warning("MMR pass failed: %s", exc)

    if not all_chunks:
        return []

    # Deduplicate by first 200 chars of content.
    # Since similarity matches are added first, deduplication will preserve
    # their actual correct L2 distance scores instead of the dummy 1.3 score.
    seen = set()
    unique: List[RetrievedChunk] = []
    for c in all_chunks:
        key = c.content[:200].strip()
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # Filter by score threshold (lower L2 distance = better)
    threshold = Config.RETRIEVAL_SCORE_THRESHOLD
    filtered = [c for c in unique if c.score <= threshold]
    # If nothing passes threshold, keep best chunk anyway
    if not filtered:
        filtered = sorted(unique, key=lambda c: c.score)[:1]

    # Sort by score ascending (lower = more similar) and return top_k
    filtered.sort(key=lambda c: c.score)
    result = filtered[:top_k]

    logger.info("Retrieved %d chunk(s) for query: %r", len(result), query[:80])
    return result


def format_context(chunks: List[RetrievedChunk]) -> str:
    if not chunks:
        return ""
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(
            f"[Chunk {i} | Source: {chunk.source} | Page: {chunk.page}]\n{chunk.content}"
        )
    return "\n\n---\n\n".join(blocks)
