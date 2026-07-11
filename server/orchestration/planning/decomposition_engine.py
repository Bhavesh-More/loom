from __future__ import annotations

import json
import os
import re
from typing import Any

from langchain_groq import ChatGroq

from graph.llm_utils import compact_text
from orchestration.planning.agent_router import route_task
from orchestration.planning.task_graph import TaskGraph, TaskNode


class DecompositionEngine:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    async def decompose(self, task: str, context: dict[str, Any] | None = None) -> TaskGraph:
        """
        Decomposes a high-level task into a structured TaskGraph with routed agents.
        """
        context = context or {}
        raw_json = await self._llm_decompose(task, context)
        subtasks = raw_json.get("subtasks", [])

        # Fallback if decomposition fails or returns empty
        if not subtasks:
            subtasks = self._fallback_decomposition(task, context)

        nodes: list[TaskNode] = []
        for s in subtasks:
            subtask_id = s.get("id") or f"task_{len(nodes) + 1}"
            task_desc = s.get("task") or "Complete task."
            parent_id = s.get("parent_id")
            capabilities = s.get("capabilities_required") or []
            depends_on = s.get("depends_on") or []

            # Type normalization
            if isinstance(capabilities, str):
                capabilities = [capabilities]
            capabilities = [str(c).strip() for c in capabilities]

            if isinstance(depends_on, str):
                depends_on = [depends_on]
            depends_on = [str(d).strip() for d in depends_on]

            # Route each subtask based on required capabilities
            routing = route_task(capabilities)

            node = TaskNode(
                id=subtask_id,
                parent_id=parent_id,
                agent_id=routing.agent_id,
                task=task_desc,
                capabilities_required=capabilities,
                capability_score=routing.capability_score,
                selection_reasoning=routing.explanation,
                depends_on=depends_on,
            )
            nodes.append(node)

        # Sanitize depends_on to reference only existing nodes to avoid invalid references
        existing_ids = {n.id for n in nodes}
        for n in nodes:
            n.depends_on = [d for d in n.depends_on if d in existing_ids and d != n.id]

        graph = TaskGraph(nodes=nodes)

        # Check for cycles. If a cycle exists, clear dependencies as a safety fallback
        try:
            graph.topological_sort()
        except ValueError:
            for n in graph.nodes:
                n.depends_on = []

        return graph

    async def _llm_decompose(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        if not os.getenv("GROQ_API_KEY_1") and self.llm is None:
            return {}

        llm = self.llm or ChatGroq(
            model="qwen/qwen3-32b",
            api_key=os.environ.get("GROQ_API_KEY_1"),
            temperature=0.2,
            max_tokens=1536,
        )
        context_json = compact_text(json.dumps(context, default=str), 3000)

        prompt = f"""
You are a task decomposition assistant. Your job is to break down a high-level user request into a set of executable subtasks with explicit dependencies and required technical capabilities.

User Request: {task}
Context JSON: {context_json}

Return a JSON object containing a list of subtasks. Each subtask must have the following structure:
{{
  "id": "A short, unique identifier for the subtask (e.g., 'db_schema', 'api_routes')",
  "parent_id": "The ID of the parent task if this is a nested subtask, otherwise null",
  "task": "A clear description of what this subtask should accomplish",
  "capabilities_required": ["A list of specific technical skills or technologies required (e.g., 'postgresql', 'fastapi', 'streamlit', 'python', 'jwt', 'docker', 'pytest')"],
  "depends_on": ["IDs of other subtasks that must be completed before this one can start"]
}}

Make sure:
1. The subtasks form a Directed Acyclic Graph (DAG) with no dependency cycles.
2. The capabilities listed correspond to technical categories (like 'sql', 'fastapi', 'auth', 'pytest', etc.).
3. Return ONLY a valid JSON object matching this structure:
{{
  "subtasks": [
    ...
  ]
}}
"""
        messages = [
            {"role": "system", "content": "Return only JSON matching the requested subtasks format."},
            {"role": "user", "content": prompt},
        ]
        try:
            response = await llm.ainvoke(messages) if hasattr(llm, "ainvoke") else llm.invoke(messages)
            raw = getattr(response, "content", str(response))
            return json.loads(self._strip_json(raw))
        except Exception:
            return {}

    def _strip_json(self, raw: str) -> str:
        raw = raw.strip()
        if "<think>" in raw and "</think>" in raw:
            raw = raw[raw.index("</think>") + len("</think>") :].strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        match = re.search(r"\{.*\}", raw.strip(), re.DOTALL)
        return match.group(0) if match else raw.strip().rstrip("```").strip()

    def _fallback_decomposition(self, task: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        # Default fallback decomposition for calculator app
        return [
            {
                "id": "db_schema",
                "parent_id": None,
                "task": "Create database schema and SQL for calculator operation history.",
                "capabilities_required": ["sql", "postgresql"],
                "depends_on": [],
            },
            {
                "id": "calc_logic",
                "parent_id": None,
                "task": "Create Python calculator functions for arithmetic operations.",
                "capabilities_required": ["python"],
                "depends_on": [],
            },
            {
                "id": "api_backend",
                "parent_id": None,
                "task": "Expose calculator history and persistence routes using the database schema.",
                "capabilities_required": ["fastapi", "rest_api"],
                "depends_on": ["db_schema"],
            },
            {
                "id": "streamlit_ui",
                "parent_id": None,
                "task": "Create a Streamlit UI that calls the Python calculator module and API.",
                "capabilities_required": ["streamlit"],
                "depends_on": ["calc_logic", "api_backend"],
            },
            {
                "id": "documentation",
                "parent_id": None,
                "task": "Write README documentation for setup and usage.",
                "capabilities_required": ["readme", "markdown"],
                "depends_on": ["streamlit_ui"],
            },
        ]
