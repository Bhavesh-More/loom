from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from context_system.ast_parser import EXTENSION_LANGUAGE
from context_system.graph_builder import SKIP_DIRS
from context_system.models import RepoOrientation


class RepoOrientator:
    async def orient(self, repo_path: str) -> RepoOrientation:
        root = Path(repo_path)
        manifests = await self._read_manifests(root)
        shape, languages = await self._scan_shape(root)
        concepts = await self._read_readme_concepts(root)
        return RepoOrientation(
            repo_path=repo_path,
            manifests=manifests,
            directory_shape=shape,
            named_concepts=concepts,
            detected_languages=languages,
            conventions=self._infer_conventions(shape, manifests),
        )

    async def _read_manifests(self, root: Path) -> dict:
        manifests: dict = {}
        for name in ["package.json", "requirements.txt", "go.mod", "Cargo.toml", "pyproject.toml"]:
            path = root / name
            if not path.exists():
                continue
            text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
            if name == "package.json":
                try:
                    manifests[name] = json.loads(text)
                except json.JSONDecodeError:
                    manifests[name] = {"raw": text[:2000]}
            else:
                manifests[name] = {"raw": text[:2000]}
        return manifests

    async def _scan_shape(self, root: Path) -> tuple[list[str], dict[str, int]]:
        def _walk():
            shape: list[str] = []
            languages: dict[str, int] = {}
            for path in root.rglob("*"):
                if any(part in SKIP_DIRS for part in path.parts):
                    continue
                rel = str(path.relative_to(root))
                if path.is_dir() and rel.count("/") < 3:
                    shape.append(rel + "/")
                elif path.is_file():
                    language = EXTENSION_LANGUAGE.get(path.suffix.lower())
                    if language:
                        languages[language] = languages.get(language, 0) + 1
            return shape[:300], languages

        return await asyncio.to_thread(_walk)

    async def _read_readme_concepts(self, root: Path) -> list[str]:
        for name in ["README.md", "readme.md"]:
            path = root / name
            if path.exists():
                text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
                words = re.findall(r"\b[A-Z][A-Za-z0-9]*(?:[A-Z][A-Za-z0-9]*)+\b|\b[A-Za-z]+(?:Provider|Service|Controller|Middleware|Agent)\b", text)
                return list(dict.fromkeys(words))[:50]
        return []

    def _infer_conventions(self, shape: list[str], manifests: dict) -> list[str]:
        conventions: list[str] = []
        joined = "\n".join(shape)
        package = manifests.get("package.json", {})
        deps = {**package.get("dependencies", {}), **package.get("devDependencies", {})} if isinstance(package, dict) else {}
        if "src/components/" in joined:
            conventions.append("React-style component directory detected")
        if "app/api/" in joined or "pages/api/" in joined:
            conventions.append("API routes are organized by filesystem routing")
        if "fastapi" in str(manifests).lower():
            conventions.append("FastAPI backend conventions detected")
        if "tailwindcss" in deps:
            conventions.append("Tailwind CSS styling conventions detected")
        if "requirements.txt" in manifests or "pyproject.toml" in manifests:
            conventions.append("Python project manifest detected")
        return conventions
