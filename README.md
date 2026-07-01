# loom

Loom is a multi-agent Python workspace with a FastAPI backend, a React frontend, LangGraph orchestration, and Supabase-backed persistence.

## What is working

- Project-aware context understanding
- Confidence scoring and validation workflow
- FastAPI orchestration endpoints
- Optional Redis checkpoint cache with in-memory fallback

## Quick Start

### 1. Install System Dependencies

Project-aware context understanding requires `ripgrep` because the context scanner always runs `rg` first before semantic or graph ranking.

macOS:

```bash
brew install ripgrep
rg --version
```

Windows:

```powershell
winget install BurntSushi.ripgrep.MSVC
rg --version
```

If `winget` is unavailable, use one of these instead:

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

You also need:

- Python 3.11+ for the FastAPI backend
- Node.js 20+ and npm for the React frontend
- Supabase/Postgres with the `vector` extension enabled for context storage
- A valid `DATABASE_URL` in `server/.env`
- `GROQ_API_KEY_1` in `server/.env` for planner, router, context LLM parsing, and agent execution

### 2. Install Backend Dependencies

```bash
cd <path>/loom/server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
cd C:\path\to\loom\server
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Database Setup

Run the migrations in Supabase/Postgres:

- `server/migrations/001_context_system_tables.sql`
- `server/migrations/20260617_confidence_scoring.sql`

The first migration enables `pgvector` and creates the context-system tables. The second migration creates the confidence scoring and validation workflow tables. The backend also attempts to bootstrap the confidence workflow schema on startup, but running migrations explicitly is safer for a fresh environment.

### 4. Feature Flags

Project-aware context system:

```bash
export LOOM_CONTEXT_LOGS=true
```

This writes tagged JSONL traces to `server/logs/loom_context_runs.jsonl`, including context payloads, planner JSON, and agent input/output.

```bash
export CONTEXT_USE_LOCAL_EMBEDDINGS=true
```

This is optional. By default Loom uses Codex-style targeted reading with `rg` and LLM ranking. Set this only when you want local `sentence-transformers` embeddings and pgvector search.

Confidence scoring and validation workflow:

```bash
export REDIS_URL=redis://localhost:6379/0
```

Redis is optional. If `REDIS_URL` is missing, checkpoints use the in-memory fallback.

### 5. Start the Backend

```bash
cd <path>/loom/server
./.venv/bin/uvicorn main:app --reload
```

Open the API docs:

- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 6. Start the Frontend

```bash
cd <path>/loom/ide
npm install
npm run dev
```

Open the frontend:

- [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Project-Aware Context Verification

Use `POST /context/analyze` in Swagger with:

```json
{
  "repo_path": "<path>/loom/ide",
  "prompt": "add a dark mode toggle in the top app bar and persist the selected theme",
  "task_id": "context-smoke-1",
  "token_budget": 4096
}
```

Expected outcome:

- `files` contains task-relevant files such as `TopAppBar.tsx`, `App.tsx`, and CSS/theme files when they exist
- `relationships` contains import edges
- `change_surface` gives the dependency-aware edit order
- `gaps` is empty or explains missing context

With `LOOM_CONTEXT_LOGS=true`, verify:

```bash
tail -f server/logs/loom_context_runs.jsonl
```

You should see tags such as `context.input`, `context.output`, `context.payload`, `planner.input`, `planner.output`, `agent.input`, and `agent.output` during normal project execution.

## Orchestration Verification

Use `POST /api/orchestration/run` in Swagger with:

```json
{
  "task": "Create a calculator app which should store data in a database and have a Streamlit frontend, use Python for it.",
  "context": {}
}
```

Expected outcome:

- A `PipelineResult` response
- `status: success`
- Supported agent IDs such as `postgresql`, `fastapi`, `streamlit`, and `all_rounder`
- Per-agent scores, validation results, retry hints when validation fails, and checkpointed outputs when enabled

## Optional Context Logs

The file `server/logs/loom_context_runs.jsonl` is optional.

Turn it on by setting:

```bash
export LOOM_CONTEXT_LOGS=true
```

When enabled, the logger writes structured JSON lines for orchestration and context events.
