"""
config.py
---------
Central configuration for the RAG Assistant.
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    BASE_DIR: Path = Path(__file__).resolve().parent
    DOCS_DIR: Path = BASE_DIR / "docs"
    DATA_DIR: Path = BASE_DIR / "data"
    VECTOR_STORE_DIR: Path = BASE_DIR / "vector_store"
    ASSETS_DIR: Path = BASE_DIR / "assets"

    FAISS_INDEX_NAME: str = "faiss_index"

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Chunking
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 600))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 120))

    # Embeddings
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_BACKEND: str = os.getenv("EMBEDDING_BACKEND", "openai")
    LOCAL_EMBEDDING_MODEL: str = os.getenv(
        "LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2"
    )

    # Retrieval — fetch more candidates, re-rank, return top TOP_K
    TOP_K: int = int(os.getenv("TOP_K", 5))
    RETRIEVAL_FETCH_K: int = int(os.getenv("RETRIEVAL_FETCH_K", 20))
    RETRIEVAL_SCORE_THRESHOLD: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", 2.5))

    # LLM
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", 0))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", 1500))
    LLM_REQUEST_TIMEOUT: int = int(os.getenv("LLM_REQUEST_TIMEOUT", 60))

    # Max file size 500 MB
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 500))

    # Authentication
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme")
    USER_USERNAME: str = os.getenv("USER_USERNAME", "user")
    USER_PASSWORD: str = os.getenv("USER_PASSWORD", "changeme")

    NO_ANSWER_MESSAGE: str = (
        "Your query couldn't be found in the uploaded documents. "
        "Please ensure the relevant document has been uploaded, or rephrase your question."
    )

    @classmethod
    def ensure_directories(cls) -> None:
        for directory in (cls.DOCS_DIR, cls.DATA_DIR, cls.VECTOR_STORE_DIR, cls.ASSETS_DIR):
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls) -> list:
        problems = []
        if cls.EMBEDDING_BACKEND == "openai" and not cls.OPENAI_API_KEY:
            problems.append(
                "OPENAI_API_KEY is missing. Create a .env file and set OPENAI_API_KEY=<your key>."
            )
        if cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            problems.append("CHUNK_OVERLAP must be smaller than CHUNK_SIZE.")
        # Warn if embedding backend changed while an index exists
        if cls.EMBEDDING_BACKEND == "local":
            index_path = cls.VECTOR_STORE_DIR / cls.FAISS_INDEX_NAME / "index.faiss"
            if index_path.exists():
                logger.warning(
                    "EMBEDDING_BACKEND is set to 'local' but an existing FAISS index "
                    "was built with a different embedding model. Vector dimensions may "
                    "differ. Reset the knowledge base to rebuild with the new backend."
                )
        return problems


Config.ensure_directories()
