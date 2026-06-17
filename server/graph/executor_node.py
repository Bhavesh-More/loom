import os
from langchain_groq import ChatGroq
from graph.state import LoomState
from prompts.prompts import AGENT_PROMPT_MAP


def executor_node(state: LoomState) -> LoomState:
    """
    Executes the current step in the execution plan.
    Calls the appropriate agent with its system prompt + context from prior agents.
    Stores output in state['agent_outputs'][agent_name].
    Increments state['current_step'].
    """
    plan = state["execution_plan"]
    step_index = state["current_step"]

    if step_index >= len(plan):
        print("[Executor] No more steps to execute.")
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
        print(f"[Executor] ERROR: {error_msg}")
        state["errors"].append(error_msg)
        state["current_step"] = step_index + 1
        return state

    # Build context from prior agent outputs
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

    user_message = f"""
Project Goal: {state['goal']}

Your specific task: {task}

Precomputed repository context:
{state.get('context_payload_text', '')}

Use the relevant files, relationships, and change_surface above as your primary
repo map. Do not repeat broad repo scanning in your answer; write code against
this context and only infer missing details when the context has an explicit gap.
{context_block}

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

    try:
        response = llm.invoke(messages)
        output = response.content
        state["agent_outputs"][agent_name] = output
        print(f"[Executor] Agent '{agent_name}' completed. Output length: {len(output)} chars")
    except Exception as e:
        error_msg = f"Agent '{agent_name}' failed: {str(e)}"
        print(f"[Executor] ERROR: {error_msg}")
        state["errors"].append(error_msg)
        state["agent_outputs"][agent_name] = ""

    state["current_step"] = step_index + 1
    return state
