"""
ingest.py
---------
Standalone ingestion script.

Runs the full pipeline:

    PDFs in docs/  ->  Load  ->  Chunk  ->  Embed  ->  Save to FAISS

Can be run directly from the command line:

    python ingest.py                # build (or load) the index, skip if it
                                     # already exists
    python ingest.py --rebuild      # force a full rebuild from scratch

The Streamlit app (app.py) calls the same underlying functions when the user
clicks "Build Knowledge Base", so this script is also useful for batch /
headless ingestion (e.g. in a CI pipeline or cron job).
"""

import argparse
import logging
import sys

from config import Config
from utils.embeddings import build_vector_store, index_exists
from utils.loader import load_pdfs_from_directory
from utils.splitter import split_documents

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_ingestion(rebuild: bool = False) -> bool:
    """
    Execute the load -> split -> embed -> store pipeline against the
    configured `docs/` directory.

    Args:
        rebuild: If True, rebuild the FAISS index even if one already exists.

    Returns:
        True if the pipeline completed successfully, False otherwise.
    """
    problems = Config.validate()
    if problems:
        for problem in problems:
            logger.error(problem)
        return False

    if index_exists() and not rebuild:
        logger.info(
            "A FAISS index already exists at %s. Use --rebuild to force a "
            "fresh build. Skipping ingestion.",
            Config.VECTOR_STORE_DIR / Config.FAISS_INDEX_NAME,
        )
        return True

    logger.info("Loading PDFs from %s ...", Config.DOCS_DIR)
    documents = load_pdfs_from_directory(Config.DOCS_DIR)
    if not documents:
        logger.warning(
            "No usable documents found in %s. Add some PDFs and re-run.",
            Config.DOCS_DIR,
        )
        return False

    logger.info("Splitting %d page-document(s) into chunks ...", len(documents))
    chunks = split_documents(documents)

    logger.info("Building FAISS index from %d chunk(s) ...", len(chunks))
    build_vector_store(chunks)

    logger.info("Ingestion complete. Index saved to %s", Config.VECTOR_STORE_DIR)
    return True


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Ingest PDFs into the FAISS knowledge base.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force a full rebuild of the FAISS index, even if one already exists.",
    )
    args = parser.parse_args()

    success = run_ingestion(rebuild=args.rebuild)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
