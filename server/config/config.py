"""
config.py — Centralized Configuration & Model Settings for Loom.

This module holds model names and global configuration settings so that model choices
can be easily modified in a single place without changing code across multiple agent files.
"""

import os

# ── Model Configuration ───────────────────────────────────────────────────────

# Ollama / Executor Model (used for heavy code generation)
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "minimax-m3:cloud")

# Qwen / Planner / Task Decomposition Model
QWEN_MODEL: str = os.environ.get("QWEN_MODEL", "openai/gpt-oss-120b")
GROQ_PLANNER_MODEL: str = os.environ.get("GROQ_PLANNER_MODEL", QWEN_MODEL)

# Groq Fast Model (used for routing, classification, intent parsing, reflection, QA)
GROQ_FAST_MODEL: str = os.environ.get("GROQ_FAST_MODEL", "llama-3.3-70b-versatile")
LLAMA_FAST_MODEL: str = GROQ_FAST_MODEL
