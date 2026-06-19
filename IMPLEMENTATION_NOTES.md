<!--
Reconnaissance report for Issue #20 — Confidence Scoring & Validation Workflow

Repository layout:
- Backend lives in server/ with FastAPI entrypoint at server/main.py.
- API routers are collected in server/api/router.py and route files live in server/api/routes/.
- LangGraph workflow lives in server/graph/. The compiled graph is server/graph/builder.py::loom_graph.
- Frontend lives in ide/ and is not touched by this additive backend feature.
- Existing database access uses asyncpg through server/db/database.py::database, pointing at DATABASE_URL.
- Existing migrations live under server/migrations/.

Existing agent-like components:
- server/graph/router_node.py::router_node — LLM-backed query classifier.
- server/graph/planner_node.py::planner_node — LLM-backed execution-plan builder.
- server/graph/executor_node.py::executor_node — prompt-backed agent executor for selected agent prompts.
- server/graph/qa_node.py::qa_node — LLM-backed QA agent.
- server/graph/file_writer_node.py::file_writer_node — output materialization node.
- server/context_system/langgraph_node.py::context_understanding_node_async — async LangGraph node for repo context.
- server/api/routes/project_route.py streams graph execution and behaves as the current orchestration entrypoint.

LangGraph setup:
- A single StateGraph[LoomState] wires context_understanding -> router -> qa or planner -> executor loop -> file_writer.
- Agents are not separate classes; executor_node calls the shared ChatGroq client with prompts from server/prompts/prompts.py.

Existing scoring/validation/orchestration logic:
- server/context_system/final_scorer.py scores repository context relevance only; it is not an agent-output confidence scorer.
- server/context_system/cache_invalidator.py has cascade invalidation for repo context, not pipeline blast-radius handling.
- No existing contract validation, checkpointing, custom-check governance, or confidence gate was found.

Redis check:
- redis-cli ping failed with "Connection refused" on 2026-06-17, so Redis is not locally running.
- REDIS_SETUP.md was added, and runtime/checkpoint.py falls back to an in-memory dict when REDIS_URL is absent or Redis cannot connect.

Supabase/Postgres schema:
- Existing schema files are in server/migrations/ and server/tests/table_creation/.
- The project uses Supabase-compatible PostgreSQL via asyncpg rather than a Supabase SDK client, so new persistence uses the existing database wrapper.
-->

# Implementation Notes

This file intentionally starts with the reconnaissance report requested by Issue #20.
