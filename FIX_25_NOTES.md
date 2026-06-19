# Orchestration Layer Implementation & Fixes (Issue #25)

This document provides a comprehensive summary of the changes made to implement the central orchestration layer (Steps 1–8) in the Loom server and detailed instructions on how to test all of them.

---

## 1. What Has Been Fixed & Implemented

We have implemented a central orchestration layer responsible for decomposing high-level user requests, dynamically routing subtasks to specialized agents based on capability matching, and organizing them into a topological dependency graph for parallel/sequential execution.

### Step 1: Agent Capability Registry
* **File:** [server/orchestration/planning/agent_registry.py](server/orchestration/planning/agent_registry.py)
* **Description:** Created a central capability registry mapping **15 specialized agents** with detailed capability profiles (`AgentProfile` Pydantic model).
* **Registered Agents:**
  1. `postgresql` (PostgreSQL Database Agent)
  2. `mongodb` (MongoDB Database Agent)
  3. `supabase` (Supabase Agent)
  4. `redis` (Redis Cache Agent)
  5. `fastapi` (FastAPI Backend Agent)
  6. `auth` (Authentication Agent)
  7. `rag` (RAG Agent)
  8. `openai` (OpenAI Integration Agent)
  9. `web_scraping` (Web Scraping Agent)
  10. `langgraph` (LangGraph Orchestration Agent)
  11. `streamlit` (Streamlit Frontend Agent)
  12. `pytest` (Pytest Testing Agent)
  13. `docker` (Docker Containerization Agent)
  14. `github_actions` (GitHub Actions Agent)
  15. `all_rounder` (General Programming Agent)

### Step 2: Capability-Based Router
* **File:** [server/orchestration/planning/agent_router.py](server/orchestration/planning/agent_router.py)
* **Description:** Implemented `route_task(capabilities_required)` to select the best-fit agent using dynamic scoring:
  * Calculates match score (overlapping capabilities / required capabilities).
  * Implements tie-breaking (prefers specialized agents over `all_rounder`, then lowest cost category).
  * Generates a descriptive, human-readable textual explanation of the agent selection.

### Step 3: Task Graph & Planning Schemas
* **File:** [server/orchestration/planning/task_graph.py](server/orchestration/planning/task_graph.py)
* **Description:** Introduced `TaskNode` and `TaskGraph` Pydantic models:
  * Supports hierarchy (`parent_id`) and explicit dependencies (`depends_on`).
  * `topological_sort()`: Detects dependency cycles (raises `ValueError`) and sorts nodes linearly.
  * `get_parallel_groups()`: Groups tasks into parallel execution tiers.
* **Compatibility:** Integrated `task_graph` as an optional field in the existing `ExecutionPlan` ([server/orchestration/planning/plan_schema.py](server/orchestration/planning/plan_schema.py)).

### Step 4: Automatic Decomposition Engine
* **File:** [server/orchestration/planning/decomposition_engine.py](server/orchestration/planning/decomposition_engine.py)
* **Description:** Created `DecompositionEngine` to break down high-level tasks:
  * Calls `qwen/qwen3-32b` via LangChain for JSON-structured subtasks.
  * Cleans `<think>` tags and markdown code blocks before JSON parsing.
  * Automatically routes every subtask, scores capability matching, and writes routing explanations.
  * Automatically resolves invalid dependencies and clears dependency cycles to prevent deadlocks.
  * Provides a deterministic 5-node fallback plan when no API key is present or LLM invocation fails.

### Step 5: MasterPlanner Integration
* **File:** [server/orchestration/planning/master_planner.py](server/orchestration/planning/master_planner.py)
* **Description:** Integrated `DecompositionEngine` into the master planning flow:
  * Runs task decomposition in `build_plan()` and attaches the resulting `TaskGraph` to the `ExecutionPlan`.
  * Emits event logs `orchestration.plan.task_graph_built` or `orchestration.plan.task_graph_skipped`.
  * Ensures **100% backward compatibility** by wrapping the entire engine call in a try-catch to keep planning non-fatal.

### Step 6: LangGraph & State Integration
* **Files:** [server/graph/state.py](server/graph/state.py), [server/graph/planner_node.py](server/graph/planner_node.py)
* **Description:** Exposed the generated task graph to downstream workflows:
  * Added `task_graph` (dict) and `task_graph_logs` (list of formatted selection lines) to `LoomState`.
  * Updated `planner_node` to execute the decomposition engine, populate the state fields, and log events.

### Step 7: API & SSE Exposition
* **Files:** [server/api/routes/orchestration_route.py](server/api/routes/orchestration_route.py), [server/api/routes/project_route.py](server/api/routes/project_route.py)
* **Description:** Added endpoints and stream updates for the frontend:
  * Exposes `GET /api/orchestration/plan/{run_id}/task-graph` returning the task graph and its selection logs.
  * Injects `task_graph` and `task_graph_logs` in the initial state of project loads.
  * Streams graph updates to the UI in the `planner` SSE event stream.

### Step 8: Comprehensive Testing & Isolation
* **Files:** [server/orchestration/tests/test_integration.py](server/orchestration/tests/test_integration.py), [server/orchestration/tests/conftest.py](server/orchestration/tests/conftest.py)
* **Description:** Created 9 new integration tests covering end-to-end task flows, parallel groups, and capability routing. 
* **Event Loop Closed Fix:** Added an autouse fixture in `conftest.py` that clears `GROQ_API_KEY_1` for the test suite, preventing lingering background `httpx` connection pools from throwing closed event loop exceptions.

---

## 2. How to Test All the Things

### Option A: Automated Tests (Recommended)
You can run the entire test suite (comprising 35 tests, including registry, routing, contracts, planning, decomposition, and integration tests) using Pytest.

1. Open a terminal in the `server` directory:
   ```powershell
   cd server
   ```
2. Run pytest:
   ```powershell
   .venv\Scripts\pytest orchestration/tests/
   ```

**Expected Output:**
```
============================= 35 passed in 5.21s ==============================
```

### Option B: Manual API Verification

You can verify the API integration endpoints by spinning up the backend server.

1. **Start the FastAPI server:**
   ```powershell
   cd server
   uv run uvicorn main:app --reload
   ```
2. **Verify the Task Graph Endpoint:**
   Send a `GET` request to retrieve the task graph for a completed run:
   ```powershell
   curl http://localhost:8000/api/orchestration/plan/{YOUR_RUN_ID}/task-graph
   ```
   *Expected Response:* A JSON payload containing `"task_graph"` and `"task_graph_logs"`.

3. **Verify Server-Sent Events (SSE):**
   Initiate an orchestration plan and subscribe to the SSE endpoint:
   ```powershell
   curl http://localhost:8000/api/projects/{project_id}/stream
   ```
   *Expected SSE Event:* Look for the `planner` event containing `task_graph` and `task_graph_logs` in the JSON data payload.
