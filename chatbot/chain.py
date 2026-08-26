"""
chatbot/chain.py
----------------
RAGChain — orchestrates retrieval → prompt → generation with full error handling.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

import openai
from langchain_community.vectorstores import FAISS

from chatbot.llm import get_llm
from config import Config
from utils.prompt import get_qa_prompt
from utils.retriever import RetrievedChunk, format_context, retrieve_relevant_chunks

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    answer: str
    sources: List[RetrievedChunk] = field(default_factory=list)
    response_time_seconds: float = 0.0
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    error: Optional[str] = None


class RAGChain:
    def __init__(self, vector_store: Optional[FAISS]):
        self.vector_store = vector_store
        self.prompt = get_qa_prompt()

    def ask(self, question: str, top_k: int = Config.TOP_K) -> RAGResponse:
        start = time.perf_counter()

        if not question or not question.strip():
            return RAGResponse(answer="Please enter a question.", error="empty_question")

        if self.vector_store is None:
            return RAGResponse(
                answer="No documents have been loaded yet. Please upload a file first.",
                error="empty_vector_store",
            )

        # Retrieval
        try:
            chunks = retrieve_relevant_chunks(self.vector_store, question, top_k=top_k)
        except Exception as exc:
            logger.exception("Retrieval failed.")
            return RAGResponse(
                answer="Something went wrong while searching the documents. Please try again.",
                error=f"retrieval_error: {exc}",
                response_time_seconds=time.perf_counter() - start,
            )

        if not chunks:
            return RAGResponse(
                answer=Config.NO_ANSWER_MESSAGE,
                sources=[],
                response_time_seconds=time.perf_counter() - start,
            )

        context = format_context(chunks)

        # Generation
        try:
            llm = get_llm()
            messages = self.prompt.format_messages(context=context, question=question)
            result = llm.invoke(messages)
        except openai.APITimeoutError:
            logger.exception("OpenAI timeout.")
            return RAGResponse(
                answer="The request timed out. Please check your connection and try again.",
                sources=chunks, error="api_timeout",
                response_time_seconds=time.perf_counter() - start,
            )
        except openai.APIConnectionError:
            return RAGResponse(
                answer="Could not reach the AI service. Please check your network connection.",
                sources=chunks, error="network_error",
                response_time_seconds=time.perf_counter() - start,
            )
        except openai.AuthenticationError:
            return RAGResponse(
                answer="Authentication failed. Please check your OPENAI_API_KEY.",
                sources=chunks, error="auth_error",
                response_time_seconds=time.perf_counter() - start,
            )
        except openai.RateLimitError:
            return RAGResponse(
                answer="Rate limit reached. Please wait a moment and try again.",
                sources=chunks, error="rate_limit",
                response_time_seconds=time.perf_counter() - start,
            )
        except Exception as exc:
            logger.exception("Unexpected error during generation.")
            return RAGResponse(
                answer="An unexpected error occurred. Please try again.",
                sources=chunks, error=f"unexpected: {exc}",
                response_time_seconds=time.perf_counter() - start,
            )

        elapsed = time.perf_counter() - start
        usage = getattr(result, "response_metadata", {}).get("token_usage", {}) or {}

        return RAGResponse(
            answer=result.content,
            sources=chunks,
            response_time_seconds=elapsed,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens"),
        )
