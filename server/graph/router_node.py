import json
import os
from graph.llm_clients import get_groq_router_llm
from graph.state import LoomState

ROUTER_SYSTEM_PROMPT = """
You are a query classifier for Loom, a multi-agent code generation platform.

Your job is to analyse the user's query and decide two things:
1. Is this a QA question or a code generation request?
2. If it's code generation, which specific agents from the team are actually needed?

## Query Types

"qa"      — The user is asking a question, seeking advice, asking for explanation,
             or having a general discussion. No code needs to be generated.
             Examples:
               - "how do I start implementing this project?"
               - "what does the redis agent do?"
               - "which database should I use?"
               - "explain the architecture to me"

"codegen" — The user explicitly wants code to be written or generated.
             Examples:
               - "generate the frontend"
               - "build the database layer"
               - "write the fastapi routes"
               - "generate everything"
               - "create the full project"

## Active Agents Rule (for codegen only)
Look at the user's query carefully. If they ask for a specific part (e.g. "generate frontend"),
only include the agents relevant to that part from the team.
If they ask for everything ("generate the project", "build it all"), include all team agents.

## Output Format
Return ONLY valid JSON. No markdown. No explanation. No preamble.

{
  "query_type": "qa" | "codegen",
  "active_agents": ["agent1", "agent2"],
  "reasoning": "<one sentence why>"
}

For "qa" queries, active_agents must always be an empty list [].
For "codegen" queries, active_agents must be a non-empty subset of the team agents provided.
"""


def router_node(state: LoomState) -> LoomState:
    """
    Classifies the user's query as 'qa' or 'codegen'.
    For 'codegen', also determines which subset of selected_agents are actually needed.
    Sets state['query_type'] and state['active_agents'].
    """
    print("\n[Router] Classifying query...")

    llm = get_groq_router_llm()

    user_message = f"""
User Query: {state['goal']}

Team Agents (all agents attached to this project):
{json.dumps(state['selected_agents'])}

Classify this query and return JSON.
"""

    messages = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if model wraps in them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip().rstrip("```").strip()

        parsed = json.loads(raw)
        query_type   = parsed.get("query_type", "codegen")
        active_agents = parsed.get("active_agents", state["selected_agents"])
        reasoning    = parsed.get("reasoning", "")

        print(f"[Router] Type: {query_type}")
        print(f"[Router] Active agents: {active_agents}")
        print(f"[Router] Reasoning: {reasoning}")

    except Exception as e:
        # Safe fallback: treat as full codegen if classification fails
        print(f"[Router] Classification failed ({e}), defaulting to full codegen.")
        query_type    = "codegen"
        active_agents = state["selected_agents"]

    state["query_type"]    = query_type
    state["active_agents"] = active_agents
    return state
