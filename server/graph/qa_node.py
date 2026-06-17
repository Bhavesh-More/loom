import os
from langchain_groq import ChatGroq
from graph.state import LoomState

QA_SYSTEM_PROMPT = """
You are a helpful technical assistant embedded in Loom, a multi-agent code generation platform.
The user has a project with a team of AI agents that will generate code for them.

Your job is to answer their question clearly and helpfully based on:
- The project goal they described
- The agents that are part of their team
- The precomputed repository context, when available
- General software engineering knowledge

Be concise, direct, and practical. If they ask how to start, give them clear actionable steps.
Do NOT generate any code unless they specifically ask for a small snippet to illustrate a concept.
"""


def qa_node(state: LoomState) -> LoomState:
    """
    Handles conversational / QnA queries.
    Calls the LLM with project context and stores the answer in state['qa_response'].
    No code is generated. No files are written.
    """
    print("\n[QA] Answering user query...")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.environ.get("GROQ_API_KEY_1"),
        temperature=0.5,
        max_tokens=2048,
    )

    user_message = f"""
Project Goal: {state['goal']}

Team Agents: {', '.join(state['selected_agents'])}

Precomputed repository context:
{state.get('context_payload_text', '')}

User Question: {state['goal']}
"""

    messages = [
        {"role": "system", "content": QA_SYSTEM_PROMPT},
        {"role": "user",   "content": user_message},
    ]

    try:
        response = llm.invoke(messages)
        answer = response.content
        state["qa_response"] = answer
        print(f"[QA] Response generated. Length: {len(answer)} chars")
    except Exception as e:
        error_msg = f"QA node failed: {str(e)}"
        print(f"[QA] ERROR: {error_msg}")
        state["errors"].append(error_msg)
        state["qa_response"] = "Sorry, I could not answer your question right now."

    return state
