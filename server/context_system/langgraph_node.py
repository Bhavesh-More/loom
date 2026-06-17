from __future__ import annotations

import asyncio

from context_system.service import context_system
from observability.execution_logger import log_execution_event


class ContextUnderstandingNode:
    """Stateless LangGraph node; durable state lives in Postgres and graph state."""

    async def __call__(self, state: dict) -> dict:
        prompt = state.get("goal") or state.get("prompt") or ""
        repo_path = state.get("workspace_path") or state.get("repo_path") or ""
        task_id = state.get("task_id") or state.get("project_id") or "langgraph-task"
        state.setdefault("errors", [])

        try:
            payload = await context_system.analyze(repo_path, prompt, task_id)
            state["context_payload"] = payload.model_dump(by_alias=True)
            state["context_payload_text"] = context_system.payload_to_prose(payload)
            log_execution_event(
                "context.payload",
                {
                    "project_id": state.get("project_id"),
                    "chat_session_id": state.get("chat_session_id"),
                    "repo_path": repo_path,
                    "task_id": task_id,
                    "prompt": prompt,
                    "context_json": state["context_payload"],
                    "context_text": state["context_payload_text"],
                },
            )
        except Exception as exc:
            state["context_payload"] = {
                "task": prompt,
                "files": [],
                "relationships": [],
                "change_surface": [],
                "gaps": [
                    {
                        "description": f"Context analysis failed: {exc}",
                        "severity": "medium",
                    }
                ],
            }
            state["context_payload_text"] = (
                "Repository context could not be generated for this run. "
                "Proceed using the project goal and prior agent context."
            )
            state["errors"].append(f"Context understanding failed: {exc}")
            log_execution_event(
                "context.error",
                {
                    "project_id": state.get("project_id"),
                    "chat_session_id": state.get("chat_session_id"),
                    "repo_path": repo_path,
                    "task_id": task_id,
                    "prompt": prompt,
                    "error": str(exc),
                },
            )
        return state


async def context_understanding_node_async(state: dict) -> dict:
    return await ContextUnderstandingNode()(state)


def context_understanding_node(state: dict) -> dict:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(context_understanding_node_async(state))
    raise RuntimeError("Use context_understanding_node_async inside an active event loop")
