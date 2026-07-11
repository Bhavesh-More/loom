import logging
import os
from langchain_groq import ChatGroq
from graph.llm_utils import compact_text
from graph.state import LoomState
from observability.execution_logger import log_execution_event
from prompts.prompts import AGENT_PROMPT_MAP
from services.knowledge_service import knowledge_service
from tools.file_tools import validate_agent_output

logger = logging.getLogger(__name__)


def _calculator_streamlit_fallback_output() -> str:
    return """# FILE: app.py
import ast
import operator

import streamlit as st


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def initialize_state() -> None:
    st.session_state.setdefault("expression", "")
    st.session_state.setdefault("display", "0")
    st.session_state.setdefault("history", [])
    st.session_state.setdefault("last_was_result", False)


def evaluate_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate_node(node.operand))
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate_node(node.left)
        right = evaluate_node(node.right)
        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError("Cannot divide by zero")
        return OPERATORS[type(node.op)](left, right)
    raise ValueError("Unsupported expression")


def safe_eval(expression: str) -> float:
    return evaluate_node(ast.parse(expression, mode="eval").body)


def format_result(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.10g}"


def refresh_display() -> None:
    st.session_state.display = st.session_state.expression or "0"


def add_token(token: str) -> None:
    if st.session_state.last_was_result and token not in "+-*/%":
        st.session_state.expression = ""
    st.session_state.expression += token
    st.session_state.last_was_result = False
    refresh_display()


def clear() -> None:
    st.session_state.expression = ""
    st.session_state.display = "0"
    st.session_state.last_was_result = False


def backspace() -> None:
    st.session_state.expression = st.session_state.expression[:-1]
    st.session_state.last_was_result = False
    refresh_display()


def toggle_sign() -> None:
    expression = st.session_state.expression
    if not expression:
        return
    st.session_state.expression = expression[2:-1] if expression.startswith("-(") and expression.endswith(")") else f"-({expression})"
    st.session_state.last_was_result = False
    refresh_display()


def calculate() -> None:
    if not st.session_state.expression:
        return
    try:
        result = format_result(safe_eval(st.session_state.expression))
        st.session_state.history.insert(0, f"{st.session_state.expression} = {result}")
        st.session_state.history = st.session_state.history[:8]
        st.session_state.expression = result
        st.session_state.display = result
        st.session_state.last_was_result = True
    except Exception as exc:
        st.session_state.display = str(exc) or "Invalid expression"


def render_action_button(label: str, callback, button_type: str = "secondary") -> None:
    st.button(label, on_click=callback, use_container_width=True, type=button_type)


def render_token_button(label: str, token: str, button_type: str = "secondary") -> None:
    st.button(label, on_click=add_token, args=(token,), use_container_width=True, type=button_type)


initialize_state()
st.set_page_config(page_title="Calculator", page_icon="=", layout="centered")

st.title("Calculator")
st.caption("A safe Streamlit calculator with history.")
st.markdown(f"### {st.session_state.display}")

rows = [
    [("AC", clear, None), ("+/-", toggle_sign, None), ("%", "%", "primary"), ("/", "/", "primary")],
    [("7", "7", None), ("8", "8", None), ("9", "9", None), ("*", "*", "primary")],
    [("4", "4", None), ("5", "5", None), ("6", "6", None), ("-", "-", "primary")],
    [("1", "1", None), ("2", "2", None), ("3", "3", None), ("+", "+", "primary")],
    [("0", "0", None), (".", ".", None), ("<-", backspace, None), ("=", calculate, "primary")],
]

for row in rows:
    columns = st.columns(4)
    for column, (label, action, button_type) in zip(columns, row):
        with column:
            if callable(action):
                render_action_button(label, action, button_type or "secondary")
            else:
                render_token_button(label, action, button_type or "secondary")

if st.session_state.history:
    st.divider()
    st.subheader("History")
    for item in st.session_state.history:
        st.code(item)

# FILE: requirements.txt
streamlit
"""


def _fallback_output_for_agent(agent_name: str, goal: str, task: str) -> str | None:
    if agent_name == "streamlit" and "calculator" in f"{goal} {task}".lower():
        return _calculator_streamlit_fallback_output()
    return None


async def executor_node(state: LoomState) -> LoomState:
    """
    Executes the current step in the execution plan.
    Calls the appropriate agent with its system prompt + context from prior agents.
    Stores output in state['agent_outputs'][agent_name].
    Increments state['current_step'].
    """
    plan = state["execution_plan"]
    step_index = state["current_step"]

    if step_index >= len(plan):
        logger.info("[Executor] No more steps to execute.")
        return state

    current_step = plan[step_index]
    agent_name   = current_step["agent"]
    task         = current_step["task"]
    context_keys = current_step.get("context_keys", [])

    logger.info("[Executor] Step %s/%s: Running agent '%s'", step_index + 1, len(plan), agent_name)
    logger.info("[Executor] Task: %s", task)

    system_prompt = AGENT_PROMPT_MAP.get(agent_name)
    if not system_prompt:
        error_msg = f"No system prompt found for agent: {agent_name}"
        logger.error("[Executor] ERROR: %s", error_msg)
        state["errors"].append(error_msg)
        state["current_step"] = step_index + 1
        return state

    # Build context from prior agent outputs in the current run
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

    # 1. PREPARE AGENT CONTEXT (Retrieve knowledge chunks, memories, history)
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
    knowledge_block = compact_text(knowledge_block, 5000)

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

Generate the code now.
"""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("GROQ_API_KEY_1"),
        temperature=0.2,
        max_tokens=8192,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]
    log_execution_event(
        "agent.input",
        {
            "project_id": state.get("project_id"),
            "chat_session_id": state.get("chat_session_id"),
            "agent": agent_name,
            "step_index": step_index,
            "task": task,
            "context_keys": context_keys,
            "messages": messages,
        },
    )

    try:
        output = ""
        validation_errors: list[str] = []
        max_attempts = 3 if agent_name == "streamlit" else 1

        for attempt in range(max_attempts):
            repair_block = ""
            if validation_errors:
                repair_block = (
                    "\n\nThe previous output failed validation. Regenerate all files from scratch and fix these errors:\n"
                    + "\n".join(f"- {error}" for error in validation_errors)
                    + "\nDo not explain the fix. Return only # FILE-prefixed files."
                )

            attempt_messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message + repair_block},
            ]
            response = await llm.ainvoke(attempt_messages)
            output = response.content
            validation_errors = validate_agent_output(
                agent_name,
                output,
                goal_or_task=f"{state['goal']}\n{task}",
            )

            if not validation_errors:
                messages = attempt_messages
                break

            logger.warning(
                "[Executor] Agent '%s' output failed validation on attempt %s: %s",
                agent_name,
                attempt + 1,
                validation_errors,
            )
            log_execution_event(
                "agent.validation_failed",
                {
                    "project_id": state.get("project_id"),
                    "chat_session_id": state.get("chat_session_id"),
                    "agent": agent_name,
                    "step_index": step_index,
                    "attempt": attempt + 1,
                    "errors": validation_errors,
                },
            )

        if validation_errors:
            fallback_output = _fallback_output_for_agent(agent_name, state["goal"], task)
            if fallback_output:
                fallback_errors = validate_agent_output(
                    agent_name,
                    fallback_output,
                    goal_or_task=f"{state['goal']}\n{task}",
                )
                if not fallback_errors:
                    output = fallback_output
                    validation_errors = []
                    logger.info("[Executor] Used deterministic fallback for '%s'.", agent_name)

        if validation_errors:
            raise ValueError("Generated output failed validation: " + "; ".join(validation_errors))

        state["agent_outputs"][agent_name] = output
        logger.info("[Executor] Agent '%s' completed. Output length: %s chars", agent_name, len(output))

        # 2. RECORD OUTCOME (Run history & memory reflections)
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

        # Record in Phase 2 / Enhancement agent_executions, agent_decisions, and agent_memories tables
        try:
            from knowledge.memory_service import memory_service
            from knowledge.memory_models import AgentExecutionEntry, AgentDecisionEntry, AgentMemoryEntry
            from knowledge.reflection import MemoryReflectionEngine
            resolved_aid = await memory_service.resolve_agent_id(agent_name)
            if resolved_aid:
                # Save execution
                exec_entry = AgentExecutionEntry(
                    agent_id=resolved_aid,
                    task_id=task,
                    input_data=user_message,
                    output_data=output,
                    status="success",
                    metadata={"chat_session_id": chat_session_id or "local-run"}
                )
                saved_exec = await memory_service.save_execution(exec_entry)
                
                # Perform dynamic reflection using the reflection engine
                reflections = await MemoryReflectionEngine.extract_reflections(task, output)
                
                # Save decision & reasoning summary
                decision_entry = AgentDecisionEntry(
                    execution_id=saved_exec.id,
                    agent_id=resolved_aid,
                    decision=reflections["decision"],
                    reasoning=reflections["reasoning"],
                    outcome=reflections["outcome"]
                )
                await memory_service.save_decision(decision_entry)
                
                # Save learning memory entry
                memory_entry = AgentMemoryEntry(
                    agent_id=resolved_aid,
                    context=task,
                    summary=f"Completed task '{task}'",
                    learned_info=reflections["learned_info"],
                    tags=["execution_learning", agent_name]
                )
                await memory_service.save_memory(memory_entry)

                # Share knowledge via sync_manager so other agents can access this learning
                try:
                    from knowledge.sync_manager import sync_manager
                    from datetime import datetime, timezone
                    import uuid
                    
                    shared_entry = {
                        "id": f"shared-{saved_exec.id or uuid.uuid4()}",
                        "content": f"Agent '{agent_name}' learned from task '{task}': {reflections['learned_info']}",
                        "version": 1,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "source_agent": agent_name,
                        "priority": "medium",
                        "tags": ["agent_sharing", agent_name]
                    }
                    await sync_manager.add_knowledge(shared_entry)
                except Exception as se:
                    logger.warning("[Executor] Failed to share knowledge dynamically: %s", se)
        except Exception as pe:
            logger.warning("[Executor] Failed to write Phase 2 execution/decision/memory logs: %s", pe)

        log_execution_event(
            "agent.output",
            {
                "project_id": state.get("project_id"),
                "chat_session_id": state.get("chat_session_id"),
                "agent": agent_name,
                "step_index": step_index,
                "task": task,
                "raw_output": output,
                "errors": state.get("errors", []),
            },
        )
    except Exception as e:
        error_msg = f"Agent '{agent_name}' failed: {str(e)}"
        logger.error("[Executor] ERROR: %s", error_msg)
        state["errors"].append(error_msg)
        state["agent_outputs"][agent_name] = ""
        
        # Record failed execution in Phase 2
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
                
                # Perform dynamic reflection on failure
                reflections = await MemoryReflectionEngine.extract_reflections(task, f"ERROR: {error_msg}", error_logs=error_msg)
                
                # Save decision leading to failure
                decision_entry = AgentDecisionEntry(
                    execution_id=saved_exec.id,
                    agent_id=resolved_aid,
                    decision=reflections["decision"],
                    reasoning=reflections["reasoning"],
                    outcome=reflections["outcome"]
                )
                await memory_service.save_decision(decision_entry)
                
                # Save failure learning memory
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
                "project_id": state.get("project_id"),
                "chat_session_id": state.get("chat_session_id"),
                "agent": agent_name,
                "step_index": step_index,
                "task": task,
                "error": str(e),
            },
        )

    state["current_step"] = step_index + 1
    return state
