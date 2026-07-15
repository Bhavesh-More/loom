import json
import logging
import os

from graph.llm_clients import get_ollama_executor_llm
from graph.llm_utils import compact_text
from graph.state import LoomState
from observability.execution_logger import log_execution_event
from prompts.prompts import AGENT_PROMPT_MAP
from services.knowledge_service import knowledge_service
from tools.file_tools import validate_agent_output

logger = logging.getLogger(__name__)


def _build_theme_block(theme: dict | None) -> str:
    """
    Format the theme dict into a clear prompt block for the executor agent.
    Returns an empty string when no theme is provided.
    """
    if not theme:
        return ""
    return (
        "\n\n## UI Theme Tokens (apply these to all visual/UI code)\n"
        "The user has selected a custom theme. Use these design tokens exactly:\n"
        + json.dumps(theme, indent=2)
        + "\n\nApply: colors for backgrounds/buttons/text, font-family for all text elements, "
          "button_radius/button_size for interactive controls.\n"
    )


def _build_planner_rules_block(step: dict) -> str:
    """
    Format the planner's per-step architecture guidance into a prompt block.
    Empty sections are omitted gracefully.
    """
    parts = []

    arch = step.get("architecture_notes", "")
    if arch:
        parts.append(f"## Architecture Notes\n{arch}")

    rules = step.get("coding_rules", [])
    if rules:
        parts.append("## Coding Rules (MUST follow)\n" + "\n".join(f"- {r}" for r in rules))

    avoid = step.get("avoid", [])
    if avoid:
        parts.append("## Anti-patterns to Avoid\n" + "\n".join(f"- {a}" for a in avoid))

    expected = step.get("expected_output", "")
    if expected:
        parts.append(f"## Expected Output\n{expected}")

    if not parts:
        return ""
    return "\n\n" + "\n\n".join(parts)


async def executor_node(state: LoomState) -> LoomState:
    """
    Executes the current step in the execution plan using Ollama Cloud.

    Per-step behaviour:
      1. Retrieves the current plan step (agent, task, context_keys, planner rules).
      2. Builds a rich user message that includes:
           - Project goal
           - Specific task
           - Repository context
           - Prior agent outputs (context_keys)
           - Planner architecture notes, coding rules, avoid list, expected output
           - UI theme tokens (if the user selected a theme)
           - Knowledge/memory context
      3. Calls Ollama Cloud (via OpenAI-compatible API) to generate code.
      4. Validates output; retries up to max_attempts on validation failure.
      5. Raises if validation still fails — NO hardcoded fallback.
      6. Stores output in state['agent_outputs'][agent_name].
      7. Records execution details in the knowledge/memory system.
    """
    plan       = state["execution_plan"]
    step_index = state["current_step"]

    if step_index >= len(plan):
        print(f"\n[Executor] No more steps to execute.")
        return state

    current_step = plan[step_index]
    agent_name   = current_step["agent"]
    task         = current_step["task"]
    context_keys = current_step.get("context_keys", [])

    print(f"\n[Executor] Step {step_index + 1}/{len(plan)}: Running agent '{agent_name}'")
    print(f"[Executor] Task: {task}")

    system_prompt = AGENT_PROMPT_MAP.get(agent_name)
    if not system_prompt:
        error_msg = f"No system prompt found for agent: {agent_name}"
        logger.error("[Executor] ERROR: %s", error_msg)
        state["errors"].append(error_msg)
        state["current_step"] = step_index + 1
        return state

    # ── Build context block from prior agent outputs ─────────────────────────
    context_block = ""
    if context_keys:
        context_parts = []
        for key in context_keys:
            prior_output = state["agent_outputs"].get(key)
            if prior_output:
                context_parts.append(
                    f"=== Output from {key} agent ===\n{compact_text(prior_output, 5000)}\n"
                )
        if context_parts:
            context_block = "\n\n## Context from prior agents:\n" + "\n".join(context_parts)

    # ── Prepare knowledge/memory context ─────────────────────────────────────
    chat_session_id = state.get("chat_session_id")
    knowledge_block = ""
    if chat_session_id:
        try:
            knowledge_block = await knowledge_service.prepare_agent_context(
                agent_name=agent_name,
                chat_session_id=chat_session_id,
                task=task,
            )
        except Exception as exc:
            logger.warning("[Executor] Failed to prepare knowledge context: %s", exc)

    context_payload_text = compact_text(state.get('context_payload_text', ''), 10000)
    knowledge_block      = compact_text(knowledge_block, 5000)

    # ── Build planner rules block for this step ───────────────────────────────
    planner_rules_block = _build_planner_rules_block(current_step)

    # ── Build theme block if theme was selected ───────────────────────────────
    theme_block = _build_theme_block(state.get("theme"))

    user_message = f"""
Project Goal: {state['goal']}

Your specific task: {task}

Precomputed repository context:
{context_payload_text}

Use the relevant files, relationships, and change_surface above as your primary
repo map. Do not repeat broad repo scanning in your answer; write code against
this context and only infer missing details when the context has an explicit gap.
{context_block}
{knowledge_block}
{planner_rules_block}
{theme_block}
Generate ALL required files now. Do not omit any file. Do not truncate any file.
"""

    llm = get_ollama_executor_llm()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]

    log_execution_event(
        "agent.input",
        {
            "project_id":      state.get("project_id"),
            "chat_session_id": state.get("chat_session_id"),
            "agent":           agent_name,
            "step_index":      step_index,
            "task":            task,
            "context_keys":    context_keys,
            "has_theme":       bool(state.get("theme")),
            "messages":        messages,
        },
    )

    try:
        output            = ""
        validation_errors: list[str] = []
        # Allow more attempts for complex UI agents like streamlit
        max_attempts = 3 if agent_name in {"streamlit", "fastapi"} else 2

        for attempt in range(max_attempts):
            repair_block = ""
            if validation_errors:
                repair_block = (
                    "\n\nThe previous output failed validation. Regenerate ALL files from "
                    "scratch and fix these errors:\n"
                    + "\n".join(f"- {error}" for error in validation_errors)
                    + "\nDo not explain the fix. Return only # FILE-prefixed files. "
                      "Do not omit any file."
                )

            attempt_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message + repair_block},
            ]

            print(
                f"[Executor] Calling Ollama Cloud for agent '{agent_name}' (attempt {attempt + 1}/{max_attempts})..."
            )

            response = await llm.ainvoke(attempt_messages)
            output   = response.content

            validation_errors = validate_agent_output(
                agent_name,
                output,
                goal_or_task=f"{state['goal']}\n{task}",
            )

            if not validation_errors:
                messages = attempt_messages
                break

            print(
                f"[Executor] Agent '{agent_name}' output failed validation on attempt {attempt + 1}: {validation_errors}"
            )
            log_execution_event(
                "agent.validation_failed",
                {
                    "project_id":      state.get("project_id"),
                    "chat_session_id": state.get("chat_session_id"),
                    "agent":           agent_name,
                    "step_index":      step_index,
                    "attempt":         attempt + 1,
                    "errors":          validation_errors,
                },
            )

        # No hardcoded fallback — if Ollama cannot produce valid output, raise.
        if validation_errors:
            raise ValueError(
                f"Agent '{agent_name}' failed to generate valid output after "
                f"{max_attempts} attempt(s). Validation errors: "
                + "; ".join(validation_errors)
            )

        state["agent_outputs"][agent_name] = output
        print(
            f"[Executor] Agent '{agent_name}' completed successfully. Output: {len(output)} chars"
        )

        # ── Record successful execution in knowledge/memory system ───────────
        if chat_session_id:
            try:
                await knowledge_service.after_agent_execution(
                    agent_name=agent_name,
                    chat_session_id=chat_session_id,
                    task=task,
                    output=output,
                )
            except Exception as db_exc:
                logger.warning("[Executor] Failed to record execution details: %s", db_exc)

        try:
            from knowledge.memory_service import memory_service
            from knowledge.memory_models import AgentExecutionEntry, AgentDecisionEntry, AgentMemoryEntry
            from knowledge.reflection import MemoryReflectionEngine

            resolved_aid = await memory_service.resolve_agent_id(agent_name)
            if resolved_aid:
                exec_entry = AgentExecutionEntry(
                    agent_id=resolved_aid,
                    task_id=task,
                    input_data=user_message,
                    output_data=output,
                    status="success",
                    metadata={"chat_session_id": chat_session_id or "local-run"}
                )
                saved_exec = await memory_service.save_execution(exec_entry)

                reflections = await MemoryReflectionEngine.extract_reflections(task, output)

                decision_entry = AgentDecisionEntry(
                    execution_id=saved_exec.id,
                    agent_id=resolved_aid,
                    decision=reflections["decision"],
                    reasoning=reflections["reasoning"],
                    outcome=reflections["outcome"]
                )
                await memory_service.save_decision(decision_entry)

                memory_entry = AgentMemoryEntry(
                    agent_id=resolved_aid,
                    context=task,
                    summary=f"Completed task '{task}'",
                    learned_info=reflections["learned_info"],
                    tags=["execution_learning", agent_name]
                )
                await memory_service.save_memory(memory_entry)

                try:
                    from knowledge.sync_manager import sync_manager
                    from datetime import datetime, timezone
                    import uuid

                    shared_entry = {
                        "id":           f"shared-{saved_exec.id or uuid.uuid4()}",
                        "content":      f"Agent '{agent_name}' learned from task '{task}': {reflections['learned_info']}",
                        "version":      1,
                        "timestamp":    datetime.now(timezone.utc).isoformat(),
                        "source_agent": agent_name,
                        "priority":     "medium",
                        "tags":         ["agent_sharing", agent_name]
                    }
                    await sync_manager.add_knowledge(shared_entry)
                except Exception as se:
                    logger.warning("[Executor] Failed to share knowledge dynamically: %s", se)
        except Exception as pe:
            logger.warning("[Executor] Failed to write Phase 2 execution/decision/memory logs: %s", pe)

        log_execution_event(
            "agent.output",
            {
                "project_id":      state.get("project_id"),
                "chat_session_id": state.get("chat_session_id"),
                "agent":           agent_name,
                "step_index":      step_index,
                "task":            task,
                "raw_output":      output,
                "errors":          state.get("errors", []),
            },
        )

    except Exception as e:
        error_msg = f"Agent '{agent_name}' failed: {str(e)}"
        logger.error("[Executor] ERROR: %s", error_msg)
        state["errors"].append(error_msg)
        state["agent_outputs"][agent_name] = ""

        # ── Record failed execution ──────────────────────────────────────────
        try:
            from knowledge.memory_service import memory_service
            from knowledge.memory_models import AgentExecutionEntry, AgentDecisionEntry, AgentMemoryEntry
            from knowledge.reflection import MemoryReflectionEngine

            resolved_aid = await memory_service.resolve_agent_id(agent_name)
            if resolved_aid:
                exec_entry = AgentExecutionEntry(
                    agent_id=resolved_aid,
                    task_id=task,
                    input_data=user_message,
                    output_data=f"ERROR: {error_msg}",
                    status="failure",
                    metadata={"chat_session_id": chat_session_id or "local-run"}
                )
                saved_exec = await memory_service.save_execution(exec_entry)

                reflections = await MemoryReflectionEngine.extract_reflections(
                    task, f"ERROR: {error_msg}", error_logs=error_msg
                )

                decision_entry = AgentDecisionEntry(
                    execution_id=saved_exec.id,
                    agent_id=resolved_aid,
                    decision=reflections["decision"],
                    reasoning=reflections["reasoning"],
                    outcome=reflections["outcome"]
                )
                await memory_service.save_decision(decision_entry)

                memory_entry = AgentMemoryEntry(
                    agent_id=resolved_aid,
                    context=task,
                    summary=f"Failed task '{task}'",
                    learned_info=reflections["learned_info"],
                    tags=["execution_failure", agent_name]
                )
                await memory_service.save_memory(memory_entry)
        except Exception as db_err:
            logger.warning("[Executor] Failed to write Phase 2 failure logs: %s", db_err)

        log_execution_event(
            "agent.error",
            {
                "project_id":      state.get("project_id"),
                "chat_session_id": state.get("chat_session_id"),
                "agent":           agent_name,
                "step_index":      step_index,
                "task":            task,
                "error":           str(e),
            },
        )

    state["current_step"] = step_index + 1
    return state
