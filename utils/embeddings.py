import logging
from pathlib import Path
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config import Config

logger = logging.getLogger(__name__)

_embedding_model: Optional[Embeddings] = None


def get_embedding_model() -> Embeddings:
    global _embedding_model
    if _embedding_model is None:
        if Config.EMBEDDING_BACKEND == "local":
            from langchain_huggingface import HuggingFaceEmbeddings
            _embedding_model = HuggingFaceEmbeddings(
                model_name=Config.LOCAL_EMBEDDING_MODEL,
            )
            logger.info(
                "Using local embedding model: %s", Config.LOCAL_EMBEDDING_MODEL
            )
        else:
            from langchain_openai import OpenAIEmbeddings
            if not Config.OPENAI_API_KEY:
                raise EnvironmentError("OPENAI_API_KEY is not set.")
            _embedding_model = OpenAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                api_key=Config.OPENAI_API_KEY,
            )
    return _embedding_model


def _index_path() -> Path:
    return Config.VECTOR_STORE_DIR / Config.FAISS_INDEX_NAME


def index_exists() -> bool:
    path = _index_path()
    return (path / "index.faiss").exists() and (path / "index.pkl").exists()


def build_vector_store(chunks: List[Document]) -> FAISS:
    if not chunks:
        raise ValueError("Cannot build a vector store from an empty list of chunks.")
    embeddings = get_embedding_model()
    logger.info("Embedding %d chunk(s)...", len(chunks))
    # Batch in groups to avoid API limits on very large sets
    BATCH = 500
    if len(chunks) <= BATCH:
        vector_store = FAISS.from_documents(chunks, embeddings)
    else:
        vector_store = FAISS.from_documents(chunks[:BATCH], embeddings)
        for i in range(BATCH, len(chunks), BATCH):
            batch = chunks[i:i + BATCH]
            logger.info("  Adding batch %d-%d...", i, i + len(batch))
            vector_store.add_documents(batch)
    save_vector_store(vector_store)
    return vector_store


def save_vector_store(vector_store: FAISS) -> None:
    path = _index_path()
    path.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(path))
    logger.info("FAISS index saved to %s", path)


def load_vector_store() -> Optional[FAISS]:
    if not index_exists():
        return None
    # Only require API key for OpenAI backend
    if Config.EMBEDDING_BACKEND == "openai" and not Config.OPENAI_API_KEY:
        return None
    try:
        embeddings = get_embedding_model()
        vs = FAISS.load_local(
            str(_index_path()), embeddings, allow_dangerous_deserialization=True
        )
        logger.info("FAISS index loaded.")
        return vs
    except Exception as exc:
        logger.error("Failed to load FAISS index: %s", exc)
        return None


def add_documents_to_store(vector_store: FAISS, new_chunks: List[Document]) -> FAISS:
    if not new_chunks:
        return vector_store
    logger.info("Adding %d new chunk(s) to existing index...", len(new_chunks))
    BATCH = 500
    for i in range(0, len(new_chunks), BATCH):
        vector_store.add_documents(new_chunks[i:i + BATCH])
    save_vector_store(vector_store)
    return vector_store


def reset_vector_store() -> None:
    import shutil
    path = _index_path()
    if path.exists():
        shutil.rmtree(path)
        logger.info("Vector store reset.")
    global _embedding_model
    _embedding_model = None

