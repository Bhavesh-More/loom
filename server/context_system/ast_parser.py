from __future__ import annotations

import asyncio
import re
from pathlib import Path

from context_system.models import ASTDiff, ASTFileInfo, ImportEdge, SymbolEntry


EXTENSION_LANGUAGE = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
}


class ASTParser:
    def __init__(self):
        self._languages_loaded = False
        self._tree_sitter_available = False

    def detect_language(self, file_path: str | Path) -> str | None:
        return EXTENSION_LANGUAGE.get(Path(file_path).suffix.lower())

    async def parse_file(self, repo_path: str, file_path: str | Path) -> ASTFileInfo:
        path = Path(file_path)
        language = self.detect_language(path) or "unsupported"
        if not path.is_absolute():
            path = Path(repo_path) / path
        if not path.exists() or not path.is_file():
            return ASTFileInfo(file_path=str(path), language=language, parse_ok=False)

        content = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="ignore")
        # Tree-sitter packages are loaded when available; regex extraction remains
        # the fallback for unsupported versions or grammars.
        self._try_load_tree_sitter()
        parse_ok = self._tree_sitter_parse_ok(language, content)
        imports = self._extract_imports(language, content, Path(repo_path), path)
        symbols = self._extract_symbols(language, content, repo_path, path)
        return ASTFileInfo(
            file_path=str(path),
            language=language,
            imports=imports,
            symbols=symbols,
            parse_ok=parse_ok,
        )

    async def diff_files(self, repo_path: str, old_file: str | Path, new_file: str | Path) -> ASTDiff:
        old_info = await self.parse_file(repo_path, old_file)
        new_info = await self.parse_file(repo_path, new_file)
        old_symbols = {symbol.name: symbol.signature or "" for symbol in old_info.symbols}
        new_symbols = {symbol.name: symbol.signature or "" for symbol in new_info.symbols}
        common = set(old_symbols) & set(new_symbols)
        return ASTDiff(
            file_path=str(new_file),
            added_symbols=sorted(set(new_symbols) - set(old_symbols)),
            removed_symbols=sorted(set(old_symbols) - set(new_symbols)),
            changed_signatures=sorted(name for name in common if old_symbols[name] != new_symbols[name]),
            added_imports=sorted(set(new_info.imports) - set(old_info.imports)),
            removed_imports=sorted(set(old_info.imports) - set(new_info.imports)),
        )

    def to_edges(self, repo_path: str, info: ASTFileInfo) -> list[ImportEdge]:
        return [
            ImportEdge(
                repo_path=repo_path,
                from_file=info.file_path,
                to_file=target,
                edge_type="imports",
                verified=True,
            )
            for target in info.imports
        ]

    def _try_load_tree_sitter(self) -> None:
        if self._languages_loaded:
            return
        self._languages_loaded = True
        try:
            import tree_sitter  # noqa: F401
            import tree_sitter_go  # noqa: F401
            import tree_sitter_javascript  # noqa: F401
            import tree_sitter_python  # noqa: F401
            import tree_sitter_rust  # noqa: F401
            import tree_sitter_typescript  # noqa: F401

            self._tree_sitter_available = True
        except Exception:
            self._tree_sitter_available = False

    def _tree_sitter_parse_ok(self, language: str, content: str) -> bool:
        if not self._tree_sitter_available or language == "unsupported":
            return True
        try:
            from tree_sitter import Language, Parser

            grammar = self._grammar(language)
            if grammar is None:
                return True
            parser = Parser()
            ts_language = Language(grammar) if not isinstance(grammar, Language) else grammar
            if hasattr(parser, "set_language"):
                parser.set_language(ts_language)
            else:
                parser.language = ts_language
            tree = parser.parse(content.encode("utf-8"))
            return not tree.root_node.has_error
        except Exception:
            return True

    def _grammar(self, language: str):
        if language == "python":
            import tree_sitter_python

            return tree_sitter_python.language()
        if language == "javascript":
            import tree_sitter_javascript

            return tree_sitter_javascript.language()
        if language == "typescript":
            import tree_sitter_typescript

            return tree_sitter_typescript.language_typescript()
        if language == "go":
            import tree_sitter_go

            return tree_sitter_go.language()
        if language == "rust":
            import tree_sitter_rust

            return tree_sitter_rust.language()
        return None

    def _extract_imports(self, language: str, content: str, repo_root: Path, file_path: Path) -> list[str]:
        raw_imports: list[str] = []
        if language == "python":
            raw_imports.extend(re.findall(r"^\s*from\s+([A-Za-z0-9_\.]+)\s+import\s+", content, re.MULTILINE))
            raw_imports.extend(re.findall(r"^\s*import\s+([A-Za-z0-9_\.]+)", content, re.MULTILINE))
        elif language in {"typescript", "javascript"}:
            raw_imports.extend(re.findall(r"import\s+(?:.+?\s+from\s+)?['\"]([^'\"]+)['\"]", content))
            raw_imports.extend(re.findall(r"export\s+.+?\s+from\s+['\"]([^'\"]+)['\"]", content))
            raw_imports.extend(re.findall(r"import\(['\"]([^'\"]+)['\"]\)", content))
            raw_imports.extend(re.findall(r"require\(['\"]([^'\"]+)['\"]\)", content))
        elif language == "go":
            raw_imports.extend(re.findall(r"import\s+\"([^\"]+)\"", content))
            raw_imports.extend(re.findall(r"\"([^\"]+)\"", self._import_block(content)))
        elif language == "rust":
            raw_imports.extend(re.findall(r"^\s*use\s+([^;]+);", content, re.MULTILINE))
            raw_imports.extend(re.findall(r"^\s*mod\s+([A-Za-z0-9_]+);", content, re.MULTILINE))

        resolved = []
        for value in raw_imports:
            target = self._resolve_import(value.strip(), language, repo_root, file_path)
            if target:
                resolved.append(target)
        return sorted(set(resolved))

    def _extract_symbols(self, language: str, content: str, repo_path: str, file_path: Path) -> list[SymbolEntry]:
        patterns: list[tuple[str, str]] = []
        if language == "python":
            patterns = [
                ("class", r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))?:"),
                ("function", r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))\s*:"),
            ]
        elif language in {"typescript", "javascript"}:
            patterns = [
                ("class", r"(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)"),
                ("function", r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))"),
                ("type", r"export\s+(?:interface|type)\s+([A-Za-z_][A-Za-z0-9_]*)"),
                ("component", r"export\s+const\s+([A-Z][A-Za-z0-9_]*)\s*="),
                ("function", r"export\s+const\s+([a-z][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
            ]
        elif language == "go":
            patterns = [
                ("function", r"^func\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))"),
                ("type", r"^type\s+([A-Za-z_][A-Za-z0-9_]*)\s+"),
            ]
        elif language == "rust":
            patterns = [
                ("function", r"(?:pub\s+)?fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*(\([^)]*\))"),
                ("type", r"(?:pub\s+)?(?:struct|enum|trait)\s+([A-Za-z_][A-Za-z0-9_]*)"),
            ]

        symbols: list[SymbolEntry] = []
        for kind, pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                name = match.group(1)
                signature = match.group(0).strip().split("{")[0].rstrip(":")
                symbols.append(
                    SymbolEntry(
                        name=name,
                        kind=kind,
                        file_path=str(file_path),
                        repo_path=repo_path,
                        signature=signature,
                    )
                )
        return symbols

    def _resolve_import(self, value: str, language: str, repo_root: Path, file_path: Path) -> str | None:
        if not value or value.startswith(("http:", "https:")):
            return None
        if language in {"typescript", "javascript"} and value.startswith("."):
            base = (file_path.parent / value).resolve()
            for suffix in ["", ".ts", ".tsx", ".js", ".jsx", ".json", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"]:
                candidate = Path(str(base) + suffix)
                if candidate.exists() and candidate.is_file():
                    return str(candidate)
            return str(base)
        if language == "python":
            module_path = Path(*value.split("."))
            for root in [file_path.parent, repo_root]:
                for suffix in [".py", "/__init__.py"]:
                    candidate = Path(str(root / module_path) + suffix)
                    if candidate.exists() and candidate.is_file():
                        return str(candidate.resolve())
        if language == "rust":
            module = value.split("::")[0].strip()
            for candidate in [file_path.parent / f"{module}.rs", file_path.parent / module / "mod.rs"]:
                if candidate.exists():
                    return str(candidate.resolve())
        return None

    def _import_block(self, content: str) -> str:
        match = re.search(r"import\s*\((.*?)\)", content, re.DOTALL)
        return match.group(1) if match else ""
