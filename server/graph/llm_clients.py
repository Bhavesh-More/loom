"""
llm_clients.py — Centralized LLM factory functions for Loom.

Split of responsibilities:
  - Groq  → Router, Planner, QA  (fast classification + architecture reasoning)
  - Ollama Cloud (OpenAI-compatible) → Executor  (heavyweight code generation)

All configuration is read from environment variables — nothing hardcoded.
  GROQ_API_KEY       : Groq API key
  OLLAMA_API_KEY     : Ollama Cloud API key
  OLLAMA_BASE_URL    : Ollama Cloud endpoint  (default: https://api.ollama.com/v1)
  OLLAMA_MODEL       : Model name             (default: devstral)
"""

import os

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI


# ─── Model constants (read from env with sensible defaults) ─────────────────

_GROQ_PLANNER_MODEL   = os.environ.get("GROQ_PLANNER_MODEL", "qwen/qwen3-32b")
_GROQ_FAST_MODEL      = os.environ.get("GROQ_FAST_MODEL",    "llama-3.3-70b-versatile")
_OLLAMA_BASE_URL      = os.environ.get("OLLAMA_BASE_URL",    "https://api.ollama.com/v1")
_OLLAMA_MODEL         = os.environ.get("OLLAMA_MODEL",       "devstral")


# ─── Groq LLM factories ─────────────────────────────────────────────────────

def get_groq_planner_llm() -> ChatGroq:
    """
    Groq LLM used by the Planner node.
    Uses a larger, thinking-capable model for deep architecture reasoning.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. The Planner node requires Groq. "
            "Add it to your .env file."
        )
    return ChatGroq(
        model=_GROQ_PLANNER_MODEL,
        api_key=api_key,
        temperature=0.6,
        max_tokens=3500,
    )


def get_groq_router_llm() -> ChatGroq:
    """
    Groq LLM used by the Router node.
    Uses the fast model — classification only, low token budget.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. The Router node requires Groq. "
            "Add it to your .env file."
        )
    return ChatGroq(
        model=_GROQ_FAST_MODEL,
        api_key=api_key,
        temperature=0.0,
        max_tokens=512,
    )


def get_groq_qa_llm() -> ChatGroq:
    """
    Groq LLM used by the QA node.
    Uses the fast model for conversational responses.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. The QA node requires Groq. "
            "Add it to your .env file."
        )
    return ChatGroq(
        model=_GROQ_FAST_MODEL,
        api_key=api_key,
        temperature=0.5,
        max_tokens=2048,
    )


# ─── Ollama Cloud LLM factory ────────────────────────────────────────────────

def get_ollama_executor_llm() -> ChatOpenAI:
    """
    Ollama Cloud LLM used by the Executor node for actual code generation.

    Ollama Cloud exposes an OpenAI-compatible /v1 REST API, so we use
    langchain-openai's ChatOpenAI with a custom base_url.

    Configure via environment variables:
      OLLAMA_API_KEY  — your Ollama Cloud API key
      OLLAMA_BASE_URL — endpoint (default: https://api.ollama.com/v1)
      OLLAMA_MODEL    — model name (default: devstral)
    """
    api_key = os.environ.get("OLLAMA_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OLLAMA_API_KEY is not set. The Executor node requires Ollama Cloud. "
            "Add OLLAMA_API_KEY to your .env file."
        )
    return ChatOpenAI(
        model=_OLLAMA_MODEL,
        openai_api_key=api_key,
        openai_api_base=_OLLAMA_BASE_URL,
        temperature=0.2,
        max_tokens=8192,
    )
