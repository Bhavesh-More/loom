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

def get_ollama_executor_llm():
    """
    Ollama Cloud LLM used by the Executor node for actual code generation.

    Ollama Cloud exposes an OpenAI-compatible /v1 REST API, so we use
    langchain-openai's ChatOpenAI with a custom base_url.

    Configure via environment variables:
      OLLAMA_API_KEY, OLLAMA_API_KEY_1, OLLAMA_API_KEY_2, etc.
      OLLAMA_BASE_URL — endpoint (default: https://api.ollama.com/v1)
      OLLAMA_MODEL    — model name (default: devstral)
      
    If multiple OLLAMA_API_KEY_* variables are provided, they are chained together 
    using LangChain's fallback mechanism to gracefully handle rate limit errors.
    """
    api_keys = []
    
    # Check for the default OLLAMA_API_KEY
    default_key = os.environ.get("OLLAMA_API_KEY")
    if default_key:
        api_keys.append(default_key)
        
    # Check for OLLAMA_API_KEY_1, OLLAMA_API_KEY_2, etc.
    # Sort them to ensure deterministic order (e.g., _1, _2, _3)
    numbered_keys = [k for k in os.environ.keys() if k.startswith("OLLAMA_API_KEY_")]
    numbered_keys.sort()
    
    for k in numbered_keys:
        api_keys.append(os.environ[k])
        
    if not api_keys:
        raise EnvironmentError(
            "OLLAMA_API_KEY is not set. The Executor node requires Ollama Cloud. "
            "Add OLLAMA_API_KEY (or OLLAMA_API_KEY_1, etc.) to your .env file."
        )

    # Create ChatOpenAI instances for each key
    llms = [
        ChatOpenAI(
            model=_OLLAMA_MODEL,
            openai_api_key=key,
            openai_api_base=_OLLAMA_BASE_URL,
            temperature=0.2,
            max_tokens=8192,
        )
        for key in api_keys
    ]

    # The first LLM is the primary
    primary_llm = llms[0]
    
    # If there are fallbacks, chain them
    if len(llms) > 1:
        return primary_llm.with_fallbacks(llms[1:])
        
    return primary_llm
