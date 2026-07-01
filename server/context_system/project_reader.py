from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

from context_system.models import CodeChunk, ContextMemory, FileMatch, IntentSignals, RankedChunk


IGNORE_GLOBS = [
    "!node_modules",
    "!.git",
    "!dist",
    "!build",
    "!tests",
    "!tests/**",
    "!outputs",
    "!outputs/**",
    "!__pycache__",
    "!__pycache__/**",
    "!pnpm-lock.yaml",
    "!package-lock.json",
    "!yarn.lock",
    "!uv.lock",
    "!Cargo.lock",
]


class ProjectReader:
    """
    Codex-style targeted project reading.

    This keeps work light on the user's machine: ripgrep finds candidates, this
    reader opens only a small set of files, and the LLM ranks/selects sections.
    Local embedding search remains available separately for deployments that
    want a persistent vector cache.
    """

    def __init__(self, max_files: int = 16, max_chars_per_file: int = 12000, max_rounds: int = 3):
        self.max_files = max_files
        self.max_chars_per_file = max_chars_per_file
        self.max_rounds = max_rounds

    async def read_and_rank(
        self,
        repo_path: str,
        prompt: str,
        candidates: list[FileMatch],
        task_id: str,
        signals: IntentSignals | None = None,
        memories: list[ContextMemory] | None = None,
    ) -> list[RankedChunk]:
        selected = self._seed_candidates(repo_path, candidates, memories or [])
        selected = self._dedupe_matches([*await self._discover_likely_files(repo_path, prompt), *selected])
        searched_terms: set[str] = set()
        ranked: list[dict] = []
        payload_by_path: dict[str, dict] = {}

        for _round in range(self.max_rounds):
            selected = selected[: self.max_files]
            file_payloads = await asyncio.gather(*(self._read_candidate(match) for match in selected))
            file_payloads = [payload for payload in file_payloads if payload["content"]]
            payload_by_path.update({payload["path"]: payload for payload in file_payloads})
            if not file_payloads:
                break

            try:
                decision = await self._decide_with_llm(prompt, file_payloads, signals, memories or [])
            except Exception:
                decision = self._decide_heuristically(prompt, file_payloads)

            ranked = self._merge_ranked(ranked, decision.get("files", []))
            if decision.get("done", True) or len(ranked) >= 8:
                break

            followup_terms = [
                term.strip()
                for term in decision.get("followup_search_terms", [])
                if isinstance(term, str) and term.strip()
            ]
            new_matches: list[FileMatch] = []
            for term in followup_terms[:6]:
                key = term.lower()
                if key in searched_terms:
                    continue
                searched_terms.add(key)
                new_matches.extend(await self._search_term(repo_path, term))
            selected = self._dedupe_matches([*selected, *new_matches])

        chunks: list[RankedChunk] = []
        for item in ranked:
            path = item["path"]
            source = payload_by_path.get(path)
            if not source:
                continue
            section = self._section_from_lines(
                source["content"],
                int(item.get("start_line") or 1),
                int(item.get("end_line") or 80),
            )
            chunks.append(
                RankedChunk(
                    chunk=CodeChunk(
                        file_path=path,
                        chunk_index=0,
                        content=section["content"],
                        start_line=section["start_line"],
                        end_line=section["end_line"],
                        content_hash=f"reader:{task_id}:{path}:{section['start_line']}:{section['end_line']}",
                    ),
                    score=float(item.get("score") or 0.5),
                )
            )
        return sorted(chunks, key=lambda chunk: chunk.score, reverse=True)

    def _seed_candidates(
        self,
        repo_path: str,
        candidates: list[FileMatch],
        memories: list[ContextMemory],
    ) -> list[FileMatch]:
        memory_matches: list[FileMatch] = []
        repo = Path(repo_path).resolve()
        for memory in memories:
            for index, file_path in enumerate(memory.files):
                absolute = Path(file_path)
                if not absolute.is_absolute():
                    absolute = repo / file_path
                if absolute.exists() and absolute.is_file():
                    memory_matches.append(
                        FileMatch(
                            path=str(absolute.resolve()),
                            score=max(0.55, memory.confidence - index * 0.03),
                            snippets=[memory.summary[:300]],
                            matched_terms=["memory"],
                        )
                    )
        return self._dedupe_matches([*memory_matches, *candidates])

    def _dedupe_matches(self, matches: list[FileMatch]) -> list[FileMatch]:
        by_path: dict[str, FileMatch] = {}
        for match in matches:
            path = str(Path(match.path).resolve())
            existing = by_path.get(path)
            if existing is None or match.score > existing.score:
                by_path[path] = match.model_copy(update={"path": path})
        return sorted(by_path.values(), key=lambda item: item.score, reverse=True)

    async def _discover_likely_files(self, repo_path: str, prompt: str) -> list[FileMatch]:
        lower = prompt.lower()
        names: list[str] = []
        if any(term in lower for term in ["dark", "theme", "toggle", "appearance"]):
            names = [
                "App.tsx",
                "App.jsx",
                "App.css",
                "index.css",
                "main.tsx",
                "TopAppBar.tsx",
                "Sidebar.tsx",
                "ThemeProvider.tsx",
                "theme.ts",
                "tailwind.config.js",
                "tailwind.config.ts",
            ]
        elif any(term in lower for term in ["auth", "login", "middleware", "protected", "token"]):
            names = [
                "main.py",
                "auth.py",
                "middleware.py",
                "security.py",
                "dependencies.py",
                "router.py",
                "project_route.py",
                "chat_route.py",
                "login.tsx",
                "auth.ts",
            ]
        if not names:
            return []

        async def _rg_files() -> list[str]:
            try:
                args = ["rg", "--files"]
                for glob in IGNORE_GLOBS:
                    args.extend(["--glob", glob])
                args.append(repo_path)
                proc = await asyncio.create_subprocess_exec(
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _stderr = await proc.communicate()
                if proc.returncode not in (0, 1):
                    return []
                return [line for line in stdout.decode().splitlines() if line.strip()]
            except Exception:
                return []

        def _find() -> list[FileMatch]:
            root = Path(repo_path)
            wanted = {name.lower() for name in names}
            matches: list[FileMatch] = []
            for path in root.rglob("*"):
                if self._is_low_value_path(str(path)):
                    continue
                if path.is_file() and path.name.lower() in wanted:
                    matches.append(
                        FileMatch(
                            path=str(path.resolve()),
                            score=0.78 + self._path_boost(str(path), prompt),
                            snippets=["Likely entry point or UI surface inferred from repo shape."],
                            matched_terms=["repo-shape"],
                        )
                    )
            return matches

        wanted = {name.lower() for name in names}
        rg_paths = await _rg_files()
        if rg_paths:
            matches = []
            for raw_path in rg_paths:
                path = Path(raw_path)
                absolute = path if path.is_absolute() else Path(repo_path) / path
                if absolute.name.lower() in wanted and not self._is_low_value_path(str(absolute)):
                    matches.append(
                        FileMatch(
                            path=str(absolute.resolve()),
                            score=0.78 + self._path_boost(str(absolute), prompt),
                            snippets=["Likely entry point or UI surface inferred from repo shape."],
                            matched_terms=["repo-shape"],
                        )
                    )
            return matches

        return await asyncio.to_thread(_find)

    async def _read_candidate(self, match: FileMatch) -> dict:
        path = Path(match.path)
        if not path.exists() or not path.is_file() or path.stat().st_size > 750_000:
            return {"path": match.path, "content": "", "grep_score": match.score}
        text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
        return {
            "path": str(path.resolve()),
            "content": text[: self.max_chars_per_file],
            "grep_score": match.score,
            "snippets": match.snippets[:3],
        }

    async def _decide_with_llm(
        self,
        prompt: str,
        file_payloads: list[dict],
        signals: IntentSignals | None,
        memories: list[ContextMemory],
    ) -> dict:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.environ.get("GROQ_API_KEY_1"),
            temperature=0.0,
            max_tokens=2048,
        )
        compact_files = [
            {
                "path": payload["path"],
                "grep_score": payload["grep_score"],
                "snippets": payload["snippets"],
                "outline": self._outline(payload["content"]),
            }
            for payload in file_payloads
        ]
        messages = [
            {
                "role": "system",
                "content": (
                    "You are the project-reading step of an AI coding agent. "
                    "Act like Codex: choose files that likely need edits or are necessary context, "
                    "ask for another search only when the current files are insufficient, and avoid lockfiles/generated files. "
                    "Return ONLY JSON with keys: done:boolean, followup_search_terms:string[], "
                    "files:[{path,score,start_line,end_line,reason,role}]. "
                    "Pick a small set of high-value files; do not include files just because they mention a word."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Task: {prompt}\n"
                    f"Intent signals: {signals.model_dump() if signals else {}}\n"
                    f"Prior memory: {[memory.model_dump() for memory in memories]}\n\n"
                    f"Candidate files:\n{json.dumps(compact_files, indent=2)}"
                ),
            },
        ]
        response = await asyncio.to_thread(llm.invoke, messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip().rstrip("```").strip())
        parsed["files"] = [item for item in parsed.get("files", []) if item.get("path")]
        return parsed

    def _decide_heuristically(self, prompt: str, file_payloads: list[dict]) -> dict:
        terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_]{3,}", prompt)]
        ranked: list[dict] = []
        for payload in file_payloads:
            if self._is_low_value_path(payload["path"]):
                continue
            content = payload["content"].lower()
            term_hits = sum(1 for term in terms if term in content)
            line_count = max(payload["content"].count("\n") + 1, 1)
            path_boost = self._path_boost(payload["path"], prompt)
            score = min(1.0, payload["grep_score"] * 0.45 + (term_hits / max(len(terms), 1)) * 0.35 + path_boost)
            ranked.append(
                {
                    "path": payload["path"],
                    "score": score,
                    "start_line": 1,
                    "end_line": min(line_count, 120),
                    "reason": "heuristic keyword/path relevance",
                }
            )
        ranked = sorted(ranked, key=lambda item: item["score"], reverse=True)
        followups = []
        lower = prompt.lower()
        if any(term in lower for term in ["dark", "theme", "toggle"]):
            followups = ["theme", "dark", "className", "TopAppBar", "index.css", "App"]
        elif any(term in lower for term in ["auth", "login", "middleware"]):
            followups = ["auth", "middleware", "protected", "login", "token", "route"]
        return {"done": len(ranked) >= 5, "followup_search_terms": followups, "files": ranked[:10]}

    def _merge_ranked(self, current: list[dict], incoming: list[dict]) -> list[dict]:
        by_path = {item["path"]: item for item in current if item.get("path")}
        for item in incoming:
            path = item.get("path")
            if not path or self._is_low_value_path(path):
                continue
            old = by_path.get(path)
            if old is None or float(item.get("score") or 0) > float(old.get("score") or 0):
                by_path[path] = item
        return sorted(by_path.values(), key=lambda item: float(item.get("score") or 0), reverse=True)

    async def _search_term(self, repo_path: str, term: str) -> list[FileMatch]:
        try:
            args = ["rg", "--json", "--ignore-case"]
            for glob in IGNORE_GLOBS:
                args.extend(["--glob", glob])
            args.extend([term, repo_path])
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await proc.communicate()
            if proc.returncode not in (0, 1):
                return []
            grouped: dict[str, dict] = {}
            for line in stdout.decode().splitlines():
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if payload.get("type") != "match":
                    continue
                data = payload.get("data", {})
                path = data.get("path", {}).get("text")
                if not path:
                    continue
                absolute = str(Path(path).resolve())
                if self._is_low_value_path(absolute):
                    continue
                group = grouped.setdefault(absolute, {"lines": [], "snippets": [], "hits": 0})
                group["hits"] += 1
                group["lines"].append(int(data.get("line_number", 0)))
                text = data.get("lines", {}).get("text", "").strip()
                if text and len(group["snippets"]) < 3:
                    group["snippets"].append(text[:300])
            return [
                FileMatch(
                    path=path,
                    score=min(1.0, 0.35 + group["hits"] / 10),
                    line_numbers=group["lines"][:10],
                    snippets=group["snippets"],
                    matched_terms=[term],
                )
                for path, group in grouped.items()
            ]
        except Exception:
            return await self._fallback_search_term(repo_path, term)

    async def _fallback_search_term(self, repo_path: str, term: str) -> list[FileMatch]:
        from context_system.graph_builder import list_source_files

        source_files = await list_source_files(repo_path)
        grouped: dict[str, dict] = {}
        term_lower = term.lower()

        for file_path in source_files:
            if self._is_low_value_path(file_path):
                continue
            try:
                content = await asyncio.to_thread(
                    Path(file_path).read_text, encoding="utf-8", errors="ignore"
                )
            except Exception:
                continue

            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                if term_lower in line.lower():
                    group = grouped.setdefault(file_path, {"lines": [], "snippets": [], "hits": 0})
                    group["hits"] += 1
                    group["lines"].append(idx)
                    if line.strip() and len(group["snippets"]) < 3:
                        group["snippets"].append(line.strip()[:300])

        return [
            FileMatch(
                path=path,
                score=min(1.0, 0.35 + group["hits"] / 10),
                line_numbers=group["lines"][:10],
                snippets=group["snippets"],
                matched_terms=[term],
            )
            for path, group in grouped.items()
        ]

    def _outline(self, content: str) -> list[str]:
        outline: list[str] = []
        for index, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            if re.match(
                r"^(def|class|function|export\s+(function|class|const|interface|type)|const\s+\w+\s*=|async\s+function)\b",
                stripped,
            ):
                outline.append(f"{index}: {stripped[:180]}")
            elif index <= 20 and stripped:
                outline.append(f"{index}: {stripped[:180]}")
            if len(outline) >= 80:
                break
        return outline

    def _is_low_value_path(self, path: str) -> bool:
        name = Path(path).name.lower()
        parts = {part.lower() for part in Path(path).parts}
        return (
            name in {"pnpm-lock.yaml", "package-lock.json", "yarn.lock", "uv.lock", "cargo.lock"}
            or name.endswith((".map", ".min.js"))
            or bool(parts & {"node_modules", "dist", "build", "coverage", "outputs", "tests", "__pycache__"})
        )

    def _path_boost(self, path: str, prompt: str) -> float:
        lower_path = path.lower()
        lower_prompt = prompt.lower()
        boost = 0.0
        if any(term in lower_prompt for term in ["dark", "theme", "toggle"]):
            if any(term in lower_path for term in ["app.", "index.css", "app.css", "topappbar", "sidebar", "theme"]):
                boost += 0.25
        if any(term in lower_prompt for term in ["auth", "login", "middleware"]):
            if any(term in lower_path for term in ["auth", "middleware", "route", "main.py", "api"]):
                boost += 0.25
        if "/src/" in lower_path or "\\src\\" in lower_path:
            boost += 0.05
        return boost

    def _section_from_lines(self, content: str, start_line: int, end_line: int) -> dict:
        lines = content.splitlines()
        start = max(start_line - 1, 0)
        end = min(max(end_line, start_line), len(lines))
        if start >= len(lines):
            start = 0
            end = min(len(lines), 80)
        return {
            "content": "\n".join(lines[start:end]),
            "start_line": start + 1,
            "end_line": end,
        }
