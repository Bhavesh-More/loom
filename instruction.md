# Loom Setup And Verification

This file is for another developer who wants to set up Loom, run it, and verify the two orchestration features we added.

## 1. Backend Setup

Install the required system dependency for the Project-Aware Context Understanding System first. The scanner always uses `ripgrep` (`rg`) as the first pass.

macOS:

```bash
brew install ripgrep
rg --version
```

Windows PowerShell:

```powershell
winget install BurntSushi.ripgrep.MSVC
rg --version
```

If `winget` is unavailable:

```powershell
choco install ripgrep
scoop install ripgrep
```

Linux:

```bash
sudo apt update
sudo apt install ripgrep
rg --version
```

Install backend Python dependencies:

```bash
cd /Users/bhaveshmore/Documents/Hackathon/loom/server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell:

```powershell
cd C:\path\to\loom\server
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Required backend environment:

- `DATABASE_URL`: Supabase/Postgres connection string
- `GROQ_API_KEY_1`: LLM key used by routing, planning, context parsing, and agents
- Supabase/Postgres must have `pgvector` available

Optional feature flags:

```bash
export LOOM_CONTEXT_LOGS=true
export CONTEXT_USE_LOCAL_EMBEDDINGS=true
export REDIS_URL=redis://localhost:6379/0
```

`LOOM_CONTEXT_LOGS=true` writes context, planner, and agent JSON traces to `server/logs/loom_context_runs.jsonl`.

`CONTEXT_USE_LOCAL_EMBEDDINGS=true` enables local `sentence-transformers` embedding search. Leave it unset for the default Codex-style targeted reading mode.

`REDIS_URL` enables Redis checkpointing for the Confidence Scoring & Validation Workflow. If it is not set, Loom uses an in-memory fallback.

```bash
cd /Users/bhaveshmore/Documents/Hackathon/loom/server
./.venv/bin/uvicorn main:app --reload
```

If you need the orchestration tables in a fresh database, the backend now bootstraps them on startup from:

- `server/migrations/20260617_confidence_scoring.sql`

For the Project-Aware Context Understanding System, run:

- `server/migrations/001_context_system_tables.sql`

That migration enables `pgvector` and creates `symbol_index`, `import_graph_edges`, `embedding_cache`, `knowledge_versions`, `domain_summaries`, and context memory/cache tables.

## 2. Frontend Setup

```bash
cd /Users/bhaveshmore/Documents/Hackathon/loom/ide
npm install
npm run dev
```

Open:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## 3. FastAPI Docs Verification

Open:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Then verify these routes exist under `Orchestration`:

- `POST /api/orchestration/run`
- `GET /api/orchestration/status/{run_id}`
- `GET /api/orchestration/agent/{run_id}/{agent_id}/output`
- `POST /api/orchestration/retry/{run_id}`

Use this JSON in `POST /api/orchestration/run`:

```json
{
  "task": "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
  "context": {}
}
```

Expected response:

- `run_id`
- `status`
- `plan`
- `results`

The successful supported-agent path should use real Loom keys like:

- `postgresql`
- `fastapi`
- `streamlit`
- `all_rounder`

## 4. Live End-to-End Verification

After the backend is running, hit the orchestration endpoint from Swagger and confirm:

1. The response is `status: success`
2. The planned agents are supported Loom keys
3. The output for each agent appears in `results`

Then retry a run by calling:

- `POST /api/orchestration/retry/{run_id}`

Use the same `run_id` from the first response and include:

```json
{
  "fix_description": "Update the failing agent output so it matches the expected contract."
}
```

## 5. Project-Aware Context Understanding Verification

From Swagger, call `POST /context/analyze` with:

```json
{
  "repo_path": "/Users/bhaveshmore/Documents/Hackathon/loom/ide",
  "prompt": "add a dark mode toggle in the top app bar and persist the selected theme",
  "task_id": "context-smoke-1",
  "token_budget": 4096
}
```

Expected response shape:

- `task`: the original prompt
- `files`: the most relevant files with roles, line sections, signatures, confidence, and graph position
- `relationships`: import/dependency relationships between files
- `change_surface`: dependency-aware order of files to change and what to do in each file
- `gaps`: missing or weak context areas, ideally empty for a well-indexed repo

Open the normal project development flow in the app and confirm that:

- repository context is gathered first
- the context payload is logged into the orchestration or context trace when logging is enabled
- the file selection and change-surface output are visible in the dev logs

The main evidence is the context output written during project analysis before code generation starts.

With logs enabled:

```bash
tail -f server/logs/loom_context_runs.jsonl
```

Expected tags during a normal project run:

- `context.input`
- `context.output`
- `context.payload`
- `planner.input`
- `planner.output`
- `agent.input`
- `agent.output`
- `agent.error` when an agent call fails

## 6. Optional Context Logs

The log file is optional:

- `server/logs/loom_context_runs.jsonl`

Enable it only when you want structured execution traces:

```bash
export LOOM_CONTEXT_LOGS=true
```

If `LOOM_CONTEXT_LOGS` is not set, Loom will skip the file logger and keep running normally.

## 7. Run Tests

From the backend directory:

```bash
cd /Users/bhaveshmore/Documents/Hackathon/loom/server
./.venv/bin/pytest orchestration/tests -q
```

For the Project-Aware Context Understanding System:

```bash
./.venv/bin/python -m pytest tests/test_intent_parser.py tests/test_payload_builder.py tests/test_cache_invalidator.py tests/test_project_reader.py
```

Expected result:

- all orchestration tests pass
- all context-system focused tests pass

## 8. Redis Optionality

Redis is optional for checkpointing.

If `REDIS_URL` is not set, the checkpoint cache falls back to memory automatically.

To enable Redis locally:

```bash
export REDIS_URL=redis://localhost:6379/0
```

See also:

- [REDIS_SETUP.md](/Users/bhaveshmore/Documents/Hackathon/loom/REDIS_SETUP.md)
