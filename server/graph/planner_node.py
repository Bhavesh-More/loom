import json
import os
from langchain_groq import ChatGroq
from graph.state import LoomState
from prompts.prompts import PLANNER_SYSTEM_PROMPT

TIER_MAP = {
    "postgresql":     1,
    "mongodb":        1,
    "supabase":       1,
    "redis":          1,
    "fastapi":        2,
    "auth":           2,
    "rag":            2,
    "openai":         2,
    "web_scraping":   2,
    "langchain":      2,
    "langgraph":      2,
    "pytest":         3,
    "streamlit":      4,
    "docker":         5,
    "github_actions": 5,
}


def planner_node(state: LoomState) -> LoomState:
    """
    Calls Qwen3-32b (thinking enabled) to produce an ordered execution plan.
    Plans ONLY for state['active_agents'] — the subset the router decided is needed
    for this specific query. This prevents running mongodb/fastapi when the user
    only asked to generate the frontend.
    """
    print("\n[Planner] Generating execution plan...")

    # KEY FIX: use active_agents (what the router decided), not selected_agents (the full team)
    agents_to_plan = state.get("active_agents") or state["selected_agents"]

    print(f"[Planner] Planning for agents: {agents_to_plan}")

    llm = ChatGroq(
        model="qwen/qwen3-32b",
        api_key=os.environ.get("GROQ_API_KEY_1"),
        temperature=0.6,
        max_tokens=4096,
    )

    tier_context = {
        agent: TIER_MAP.get(agent, 99)
        for agent in agents_to_plan
    }

    user_message = f"""
Project Goal: {state['goal']}

Agents to plan for (ONLY these, do not add others): {json.dumps(agents_to_plan)}

Tier Map for these agents:
{json.dumps(tier_context, indent=2)}

Produce the execution plan now.
"""

    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user",   "content": "/think\n" + user_message},
    ]

    response = llm.invoke(messages)
    raw = response.content

    # Strip <think>...</think> block if present (Qwen3 thinking mode)
    if "<think>" in raw and "</think>" in raw:
        raw = raw[raw.index("</think>") + len("</think>"):].strip()

    # Strip markdown code fences if present
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        parsed = json.loads(raw)
        plan = parsed.get("plan", [])
    except json.JSONDecodeError as e:
        print(f"[Planner] Failed to parse plan JSON: {e}")
        print(f"[Planner] Raw output was:\n{raw}")
        plan = []
        state["errors"].append(f"Planner JSON parse error: {str(e)}")

    print(f"[Planner] Plan generated with {len(plan)} steps:")
    for step in plan:
        print(f"  Step {step.get('step')}: {step.get('agent')} — {step.get('task')[:80]}...")

    state["execution_plan"] = plan
    state["current_step"]   = 0
    return state
