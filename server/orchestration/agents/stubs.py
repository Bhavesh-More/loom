from __future__ import annotations

from typing import Any


STUB = True


async def db_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {
        "table_name": "calculator_history",
        "columns": [
            {"name": "id", "type": "uuid", "nullable": False, "primary_key": True},
            {"name": "expression", "type": "text", "nullable": False},
            {"name": "result", "type": "numeric", "nullable": False},
        ],
        "pk_field": "id",
        "create_sql": """
        CREATE TABLE IF NOT EXISTS calculator_history (
          id uuid PRIMARY KEY,
          expression text NOT NULL,
          result numeric NOT NULL
        );
        """,
    }


async def sqlite_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {
        "table_name": "calculator_history",
        "columns": [
            {"name": "id", "type": "integer", "nullable": False, "primary_key": True},
            {"name": "expression", "type": "text", "nullable": False},
            {"name": "result", "type": "real", "nullable": False},
        ],
        "pk_field": "id",
        "create_sql": """
        CREATE TABLE IF NOT EXISTS calculator_history (
          id integer PRIMARY KEY,
          expression text NOT NULL,
          result real NOT NULL
        );
        """,
    }


async def python_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {
        "module_path": "calculator.py",
        "functions": ["add", "subtract", "multiply", "divide"],
        "imports": ["math"],
    }


async def backend_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {
        "routes": ["/history", "/calculate"],
        "app_file": "main.py",
        "imports": ["json"],
    }


async def streamlit_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {
        "app_file": "app.py",
        "widgets": ["number_input", "selectbox", "button"],
        "imports": ["math"],
    }


async def readme_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    return {"content": "# Calculator App\n\nRun the backend and Streamlit frontend."}


async def generic_available_agent(inputs: dict[str, Any], retry_hint: str | None = None) -> dict[str, Any]:
    task = str(inputs.get("task") or "Complete the requested work.")
    dependencies = inputs.get("dependencies") or {}
    dependency_names = ", ".join(dependencies.keys()) or "none"
    hint = f"\nRetry hint: {retry_hint}" if retry_hint else ""
    return {
        "content": (
            f"# FILE: output.txt\n"
            f"Task: {task}\n"
            f"Dependencies: {dependency_names}\n"
            f"This is a validated placeholder output from an available Loom agent.{hint}\n"
        )
    }


AGENT_STUBS = {
    "db_agent": db_agent,
    "sqlite_agent": sqlite_agent,
    "python_agent": python_agent,
    "backend_agent": backend_agent,
    "streamlit_agent": streamlit_agent,
    "readme_agent": readme_agent,
    "postgresql": generic_available_agent,
    "mongodb": generic_available_agent,
    "supabase": generic_available_agent,
    "redis": generic_available_agent,
    "fastapi": generic_available_agent,
    "auth": generic_available_agent,
    "rag": generic_available_agent,
    "openai": generic_available_agent,
    "web_scraping": generic_available_agent,
    "docker": generic_available_agent,
    "github_actions": generic_available_agent,
    "langgraph": generic_available_agent,
    "langchain": generic_available_agent,
    "pytest": generic_available_agent,
    "streamlit": generic_available_agent,
    "all_rounder": generic_available_agent,
}
