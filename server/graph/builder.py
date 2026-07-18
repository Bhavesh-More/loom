from langgraph.graph import StateGraph, END

from graph.state import LoomState

from graph.executor_node import executor_node
from graph.qa_node import qa_node
from graph.planner_node import planner_node
from graph.router_node import router_node
from graph.file_writer_node import file_writer_node
from graph.folder_structure_node import folder_structure_node
from context_system.langgraph_node import context_understanding_node_async

# ---------------------------------------------------------------------------
# Conditional edge: router decision
# ---------------------------------------------------------------------------

def route_after_router(state: LoomState) -> str:
    """
    Called after router_node.
    'qa'      → jump to qa_node, skip all codegen
    'codegen' → proceed to planner
    """
    return state.get("query_type", "codegen")


# ---------------------------------------------------------------------------
# Conditional edge: executor loop
# ---------------------------------------------------------------------------

def should_continue_execution(state: LoomState) -> str:
    """
    Loop executor until all plan steps are done,
    then hand off to file_writer.
    """
    current_step = state.get("current_step", 0)
    plan         = state.get("execution_plan", [])

    if current_step < len(plan):
        return "continue"
    return "done"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    """
    Full Loom execution graph.

    Flow:
        START
          ↓
        context_understanding
          ↓
        router
          ├─ "qa"      → qa_node → END
          └─ "codegen" → planner
                           ↓
                    folder_structure   ← plans dirs, pre-creates in sandbox
                           ↓
                         executor ←──────────┐
                           ↓                 │
                    [should_continue]──"continue"
                           │
                         "done"
                           ↓
                        file_writer
                           ↓
                          END
    """
    graph = StateGraph(LoomState)

    # Register all nodes
    graph.add_node("router",           router_node)
    graph.add_node("context_understanding", context_understanding_node_async)
    graph.add_node("qa",               qa_node)
    graph.add_node("planner",          planner_node)
    graph.add_node("folder_structure", folder_structure_node)
    graph.add_node("executor",         executor_node)
    graph.add_node("file_writer",      file_writer_node)

    # Entry point first builds reusable repo context for downstream agents.
    graph.set_entry_point("context_understanding")
    graph.add_edge("context_understanding", "router")

    # router → qa or planner
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "qa":      "qa",
            "codegen": "planner",
        },
    )

    # qa → END (no file writing for QA)
    graph.add_edge("qa", END)

    # planner → folder_structure (plan and pre-create the directory skeleton)
    graph.add_edge("planner", "folder_structure")

    # folder_structure → executor
    graph.add_edge("folder_structure", "executor")

    # executor → loop or done
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
