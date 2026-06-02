from langgraph.graph import StateGraph, END
from graph.state import LoomState
from graph.executor_node import executor_node
from graph.planner_node import planner_node
from graph.file_writer_node import file_writer_node


def should_continue_execution(state: LoomState) -> str:
    """
    Conditional edge function.
    If there are still steps remaining in the plan, loop back to executor.
    Otherwise, proceed to file_writer.
    """
    current_step = state.get("current_step", 0)
    plan = state.get("execution_plan", [])

    if current_step < len(plan):
        return "continue"
    return "done"


def build_graph() -> StateGraph:
    """
    Constructs and compiles the Loom LangGraph execution graph.

    Graph flow:
        START
          ↓
        planner
          ↓
        executor  ←──────────────┐
          ↓                      │
        [should_continue] ──"continue"
          │
        "done"
          ↓
        file_writer
          ↓
         END
    """
    graph = StateGraph(LoomState)

    # Register nodes
    graph.add_node("planner",     planner_node)
    graph.add_node("executor",    executor_node)
    graph.add_node("file_writer", file_writer_node)

    # Entry point
    graph.set_entry_point("planner")

    # planner → executor (always)
    graph.add_edge("planner", "executor")

    # executor → conditional branch
    graph.add_conditional_edges(
        "executor",
        should_continue_execution,
        {
            "continue": "executor",
            "done":     "file_writer",
        },
    )

    # file_writer → END
    graph.add_edge("file_writer", END)

    return graph.compile()


# Singleton compiled graph instance
loom_graph = build_graph()
