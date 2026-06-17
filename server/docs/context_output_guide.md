# Context Output Guide

This guide explains how to read the JSON returned by the Project-Aware Context Understanding System.

## What The Feature Does

- Finds the most relevant files for a task before an agent starts editing.
- Reads only the files that matter, instead of scanning the whole repo blindly.
- Persists what it learns so the next similar request can reuse the same context.
- Returns a structured payload that downstream agents can use directly.

## What It Does Not Do

- It does not guarantee perfect static analysis.
- It does not replace the agent's own reasoning.
- It does not run a full repo embedding pass by default.
- It does not claim every file in the repo is relevant.
- It does not edit code by itself.

## Routes And Their Output

The same context system also runs automatically during normal Loom agent execution.
The LangGraph flow prepares context before routing, planning, QA, or executor nodes run.
When the workspace does not exist yet, the system returns an empty context payload and lets first-time generation continue.

### `POST /context/analyze`

Input:

```json
{
  "repo_path": "/path/to/repo",
  "prompt": "add authentication middleware",
  "task_id": "task-123",
  "token_budget": 2048
}
```

Output:

```json
{
  "task": "add authentication middleware",
  "files": [],
  "relationships": [],
  "change_surface": [],
  "gaps": []
}
```

The real output usually contains file entries, relationships, and a change surface. The empty shape above shows the fields.

### `POST /context/index`

Input:

```json
{
  "repo_path": "/path/to/repo"
}
```

Output:

```json
{
  "status": "scheduled",
  "repo_path": "/path/to/repo"
}
```

### `GET /context/status/{repo_path}`

Output includes coverage and cache stats:

```json
{
  "repo_path": "/path/to/repo",
  "index_coverage": 0.75,
  "file_count": 40,
  "indexed_file_count": 30,
  "cache_entries": 120,
  "cache_hit_rate": 0.62,
  "graph_edge_count": 84,
  "memory_count": 9
}
```

### `POST /context/partition`

Input:

```json
{
  "repo_path": "/path/to/repo",
  "prompt": "add theme switching and persist user preference",
  "agents": ["fastapi", "auth", "frontend"]
}
```

Output is a list of subgraph assignments:

```json
[
  {
    "agent": "frontend",
    "domain": "frontend",
    "files": ["src/App.tsx", "src/components/TopAppBar.tsx"],
    "handoff_interfaces": ["..."],
    "payload": {
      "task": "...",
      "files": [],
      "relationships": [],
      "change_surface": [],
      "gaps": []
    }
  }
]
```

## What The Main Fields Mean

`task`
: The user prompt being analyzed.

`files`
: The files the system believes matter most for the task. Each file has:

- `path`: repo-relative file path
- `role`: why the file matters
- `relevant_sections`: only the useful code slices, not the whole file
- `signatures`: important exported symbols or functions
- `confidence`: how sure the system is that the file matters
- `graph_position`: whether the file is a dependency, consumer, config, or shared abstraction

`relationships`
: Human-readable links between files, usually import relationships or other graph edges.

`change_surface`
: The dependency-ordered edit plan. This tells the agent which files to touch first and what each file should do.

`gaps`
: Things the system thinks are still missing from its knowledge. A gap is not an error. It is a signal that more indexing or reading may help.

## Why `change_surface` Matters

This is the part that makes the payload useful for agents.

Instead of giving an agent a list of file names, it gives an ordered set of edit targets with short instructions. That lets downstream agents start writing code faster and in a safer order, for example:

1. update config
2. update shared state
3. update UI consumer

## Why The Output Is Good When It Looks Like This

A good response usually:

- includes the top entry points and shared abstractions
- avoids tests, lockfiles, and generated folders
- has at least one clear UI or backend surface for the task
- includes a dependency order that makes sense
- becomes better on the second similar request because memory is reused

## Future Optimizations

- Add a stronger file-importance model for task-specific ranking.
- Reduce over-selection by teaching the reader better repo-shape priors.
- Add file-type-specific probes for frontend framework conventions.
- Store more task memories with summarized edit outcomes, not just selected files.
- Add a lightweight similarity index for memory lookup so later requests can match faster.
- Add route-specific confidence thresholds so `change_surface` only includes files that are already in `files`.
- Add UI tests or backend smoke tests for the most common task types after context analysis.
- Re-index the workspace after file writing so newly generated files are immediately available to the next request.
