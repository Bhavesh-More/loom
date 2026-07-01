from __future__ import annotations

import asyncio
import json
import re
from collections import defaultdict
from pathlib import Path

from context_system.db import ContextDatabase, context_db
from context_system.models import FileMatch, IntentSignals


class GrepScanner:
    def __init__(self, db: ContextDatabase = context_db):
        self.db = db

    async def scan(self, repo_path: str, signals: IntentSignals, task_id: str, prompt: str) -> list[FileMatch]:
        terms = signals.grep_terms or [prompt]
        pattern = "|".join(re.escape(term) for term in terms if term.strip())
        if not pattern:
            return []

        matches = []
        try:
            proc = await asyncio.create_subprocess_exec(
                "rg",
                "--json",
                "--ignore-case",
                "--hidden",
                "--glob",
                "!node_modules",
                "--glob",
                "!.git",
                "--glob",
                "!dist",
                "--glob",
                "!build",
                "--glob",
                "!tests",
                "--glob",
                "!tests/**",
                "--glob",
                "!outputs",
                "--glob",
                "!outputs/**",
                "--glob",
                "!__pycache__",
                "--glob",
                "!__pycache__/**",
                "--glob",
                "!pnpm-lock.yaml",
                "--glob",
                "!package-lock.json",
                "--glob",
                "!yarn.lock",
                "--glob",
                "!uv.lock",
                "--glob",
                "!Cargo.lock",
                pattern,
                repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode not in (0, 1):
                raise RuntimeError(f"ripgrep failed: {stderr.decode().strip()}")
            matches = self._parse(stdout.decode(), terms, repo_path)
        except Exception:
            matches = await self._fallback_scan(repo_path, terms)

        await self.db.persist_grep_hits(repo_path, task_id, prompt, matches, signals.concepts)
        return matches

    async def _fallback_scan(self, repo_path: str, terms: list[str]) -> list[FileMatch]:
        from context_system.graph_builder import list_source_files

        source_files = await list_source_files(repo_path)
        grouped = defaultdict(
            lambda: {"line_numbers": [], "snippets": [], "matched_terms": set(), "hit_count": 0}
        )
        lowered_terms = [(term, term.lower()) for term in terms]

        for file_path in source_files:
            try:
                content = await asyncio.to_thread(
                    Path(file_path).read_text, encoding="utf-8", errors="ignore"
                )
            except Exception:
                continue

            lines = content.splitlines()
            for idx, line in enumerate(lines, 1):
                lowered_line = line.lower()
                matched_in_line = set()
                for original, lowered in lowered_terms:
                    if lowered in lowered_line:
                        matched_in_line.add(original)
                if matched_in_line:
                    # Relativize path for key
                    repo = Path(repo_path).resolve()
                    abs_path = Path(file_path).resolve()
                    try:
                        rel_path = str(abs_path.relative_to(repo))
                    except ValueError:
                        rel_path = str(abs_path)
                    
                    # We store it by absolute path since _parse does that
                    group = grouped[str(abs_path)]
                    group["hit_count"] += 1
                    group["line_numbers"].append(idx)
                    group["matched_terms"].update(matched_in_line)
                    if len(group["snippets"]) < 5:
                        group["snippets"].append(line.strip()[:300])

        results: list[FileMatch] = []
        for path, group in grouped.items():
            term_score = len(group["matched_terms"]) / max(len(terms), 1)
            hit_score = min(group["hit_count"] / 10, 1.0)
            results.append(
                FileMatch(
                    path=path,
                    score=round(0.6 * term_score + 0.4 * hit_score, 4),
                    line_numbers=group["line_numbers"][:20],
                    snippets=group["snippets"],
                    matched_terms=sorted(group["matched_terms"]),
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)

    def _parse(self, output: str, terms: list[str], repo_path: str) -> list[FileMatch]:
        grouped: dict[str, dict] = defaultdict(
            lambda: {"line_numbers": [], "snippets": [], "matched_terms": set(), "hit_count": 0}
        )
        repo = Path(repo_path).resolve()
        lowered_terms = [(term, term.lower()) for term in terms]
        for line in output.splitlines():
            if not line.strip():
                continue
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
            try:
                str(Path(absolute).relative_to(repo))
            except ValueError:
                pass
            text = data.get("lines", {}).get("text", "").strip()
            group = grouped[absolute]
            group["hit_count"] += 1
            group["line_numbers"].append(int(data.get("line_number", 0)))
            if text and len(group["snippets"]) < 5:
                group["snippets"].append(text[:300])
            lowered_text = text.lower()
            for original, lowered in lowered_terms:
                if lowered in lowered_text:
                    group["matched_terms"].add(original)

        results: list[FileMatch] = []
        for path, group in grouped.items():
            term_score = len(group["matched_terms"]) / max(len(terms), 1)
            hit_score = min(group["hit_count"] / 10, 1.0)
            results.append(
                FileMatch(
                    path=path,
                    score=round(0.6 * term_score + 0.4 * hit_score, 4),
                    line_numbers=group["line_numbers"][:20],
                    snippets=group["snippets"],
                    matched_terms=sorted(group["matched_terms"]),
                )
            )
        return sorted(results, key=lambda item: item.score, reverse=True)
