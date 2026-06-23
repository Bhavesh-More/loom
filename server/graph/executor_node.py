import logging
import os
from langchain_groq import ChatGroq
from graph.state import LoomState
from observability.execution_logger import log_execution_event
from prompts.prompts import AGENT_PROMPT_MAP
from services.knowledge_service import knowledge_service

logger = logging.getLogger(__name__)


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
                    f"=== Output from {key} agent ===\n{prior_output}\n"
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

    user_message = f"""
Project Goal: {state['goal']}

Your specific task: {task}

Precomputed repository context:
{state.get('context_payload_text', '')}

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
        response = await llm.ainvoke(messages)
        output = response.content
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
                
                # Save decision & reasoning summary
                decision_entry = AgentDecisionEntry(
                    execution_id=saved_exec.id,
                    agent_id=resolved_aid,
                    decision=f"Generate code to address: '{task}'",
                    reasoning=f"Agent completed execution based on goal and repository context.",
                    outcome="success"
                )
                await memory_service.save_decision(decision_entry)
                
                # Save learning memory entry
                memory_entry = AgentMemoryEntry(
                    agent_id=resolved_aid,
                    context=task,
                    summary=f"Completed task '{task}'",
                    learned_info=f"In session '{chat_session_id or 'local-run'}', generated code matching: '{task}'",
                    tags=["execution_learning", agent_name]
                )
                await memory_service.save_memory(memory_entry)
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
            from knowledge.memory_models import AgentExecutionEntry
            resolved_aid = await memory_service.resolve_agent_id(agent_name)
            if resolved_aid:
                exec_entry = AgentExecutionEntry(
                    agent_id=resolved_aid,
                    task_id=task,
                    input_data=user_message,
                    output_data=f"ERROR: {error_msg}",
                    status="failed",
                    metadata={"chat_session_id": chat_session_id or "local-run"}
                )
                await memory_service.save_execution(exec_entry)
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
