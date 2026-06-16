# Project-Aware Context Understanding System

This implementation adds Loom's backend context intelligence layer under `server/context_system`.

## What Was Added

- Async Supabase/Postgres access for symbol indexing, import graph edges, embedding cache, grep hit persistence, domain summaries, and MVCC knowledge versions.
- A layered search pipeline: intent parsing, ripgrep scanning, semantic ranking, graph expansion, centrality scoring, and final weighted ranking.
- Tree-sitter-ready AST parsing with automatic language detection for Python, TypeScript, JavaScript, Go, and Rust, plus regex fallback for unsupported or unavailable grammars.
- Watchdog-based repository invalidation with AST-level diffs, import cascade invalidation, semantic drift checks, and versioned knowledge writes.
- Structured `ContextPayload` generation matching the issue interface: files, relationships, change surface, and gaps.
- FastAPI routes for analyze, indexing, status, watching invalidation events, and multi-agent partitioning.
- A stateless LangGraph node that writes the context payload into graph state for downstream agents.
- Codex-style targeted project reading is the default runtime mode: `rg` finds candidate files, the system reads only those files, and the LLM ranks relevant sections. Local sentence-transformer embeddings remain available by setting `CONTEXT_USE_LOCAL_EMBEDDINGS=true`.

## Technology Choices

| Component | Choice | Why |
| --- | --- | --- |
| Persistent store | Supabase Postgres + pgvector | Matches the existing stack and stores symbols, edges, versions, and embeddings in one place. |
| Embedding model | `all-MiniLM-L6-v2` via sentence-transformers | Local, free, 384-dimensional vectors, no API key. |
| AST parsing | tree-sitter grammars | Language-aware parsing with extension-based detection and graceful fallback. |
| Graph ops | networkx | In-memory PageRank and connected-component analysis with persisted Postgres edges. |
| Grep engine | ripgrep via subprocess | Fast first-pass candidate reduction. |
| File watcher | watchdog | Cross-platform live invalidation support. |
| Async DB | asyncpg | Non-blocking access from FastAPI routes. |

## Routes

- `POST /context/analyze`
- `POST /context/index`
- `GET /context/status/{repo_path:path}`
- `WebSocket /context/watch`
- `POST /context/partition`

## Notes

The heavy runtime packages are listed in `server/requirements.txt` and `server/pyproject.toml`. The code keeps fallback behavior for local tests when optional parsing or embedding packages are not installed, but production should install the full requirements and have `rg` available on the system path.

By default, startup does not load the local embedding model. To use CPU/local-vector search instead of Codex-style targeted reading, set:

```env
CONTEXT_USE_LOCAL_EMBEDDINGS=true
```
