"""
chatbot/llm.py
--------------
LLM wrapper — cached singleton to avoid re-initializing on every query.
"""

import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from config import Config

logger = logging.getLogger(__name__)

_llm: Optional[ChatOpenAI] = None


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        if not Config.OPENAI_API_KEY:
            raise EnvironmentError("OPENAI_API_KEY is not set.")
        _llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.LLM_TEMPERATURE,
            max_tokens=Config.LLM_MAX_TOKENS,
            api_key=Config.OPENAI_API_KEY,
            timeout=Config.LLM_REQUEST_TIMEOUT,
        )
        logger.debug("ChatOpenAI initialized: model=%s", Config.LLM_MODEL)
    return _llm


def reset_llm() -> None:
    global _llm
    _llm = None
