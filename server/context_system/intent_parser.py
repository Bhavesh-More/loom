from __future__ import annotations

import asyncio
import json
import os
import re

from context_system.models import IntentSignals, TaskType


INTENT_SYSTEM_PROMPT = """
You extract repository search signals for a code-aware agent context system.
Return ONLY valid JSON with keys:
concepts, likely_symbols, fuzzy_synonyms, task_type, domain.
task_type must be one of: new_feature, bug_fix, refactor, qa, unknown.
Keep lists concise and useful for grep.
"""


class IntentParser:
    async def parse(self, prompt: str) -> IntentSignals:
        try:
            parsed = await self._parse_with_llm(prompt)
            return self._normalize(parsed, prompt)
        except Exception:
            return self._heuristic_parse(prompt)

    async def _parse_with_llm(self, prompt: str) -> dict:
        from langchain_groq import ChatGroq

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.environ.get("GROQ_API_KEY_1"),
            temperature=0.0,
            max_tokens=512,
        )
        messages = [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        response = await asyncio.to_thread(llm.invoke, messages)
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip().rstrip("```").strip())

    def _normalize(self, parsed: dict, prompt: str) -> IntentSignals:
        fallback = self._heuristic_parse(prompt)
        return IntentSignals(
            concepts=self._list(parsed.get("concepts")) or fallback.concepts,
            likely_symbols=self._list(parsed.get("likely_symbols")) or fallback.likely_symbols,
            fuzzy_synonyms=self._list(parsed.get("fuzzy_synonyms")) or fallback.fuzzy_synonyms,
            task_type=TaskType(parsed.get("task_type", fallback.task_type.value)),
            domain=str(parsed.get("domain") or fallback.domain),
        )

    def _heuristic_parse(self, prompt: str) -> IntentSignals:
        lower = prompt.lower()
        if any(word in lower for word in ["fix", "bug", "error", "broken", "failing"]):
            task_type = TaskType.BUG_FIX
        elif any(word in lower for word in ["refactor", "rename", "migrate", "cleanup"]):
            task_type = TaskType.REFACTOR
        elif any(word in lower for word in ["how", "what", "explain", "why"]):
            task_type = TaskType.QA
        elif any(word in lower for word in ["add", "build", "create", "implement", "generate"]):
            task_type = TaskType.NEW_FEATURE
        else:
            task_type = TaskType.UNKNOWN

        words = [word for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", prompt) if word.lower() not in STOP_WORDS]
        camel = [self._to_camel(word) for word in words]
        symbols = list(dict.fromkeys([*words, *camel]))
        synonyms = self._synonyms(lower)
        domain = self._domain(lower)
        concepts = list(dict.fromkeys([*words[:8], *synonyms[:6]]))
        return IntentSignals(
            concepts=concepts,
            likely_symbols=symbols[:16],
            fuzzy_synonyms=synonyms,
            task_type=task_type,
            domain=domain,
        )

    def _synonyms(self, lower_prompt: str) -> list[str]:
        groups = {
            "theme": ["theme", "darkMode", "dark mode", "appearance", "colorScheme", "prefers-color-scheme"],
            "auth": ["auth", "authentication", "authorization", "session", "token", "login"],
            "api": ["api", "route", "endpoint", "handler", "controller"],
            "database": ["database", "db", "model", "schema", "repository", "query"],
            "frontend": ["component", "page", "view", "ui", "button", "layout"],
            "cache": ["cache", "memo", "redis", "ttl", "invalidation"],
            "rate": ["rate limit", "throttle", "quota", "middleware", "limiter"],
        }
        terms: list[str] = []
        for key, values in groups.items():
            if key in lower_prompt or any(value in lower_prompt for value in values):
                terms.extend(values)
        return list(dict.fromkeys(terms))

    def _domain(self, lower_prompt: str) -> str:
        if any(term in lower_prompt for term in ["ui", "frontend", "component", "theme", "dark"]):
            return "UI/styling"
        if any(term in lower_prompt for term in ["auth", "login", "session", "token"]):
            return "auth"
        if any(term in lower_prompt for term in ["database", "schema", "sql", "mongodb", "postgres"]):
            return "data"
        if any(term in lower_prompt for term in ["api", "endpoint", "route"]):
            return "api"
        return "general"

    def _to_camel(self, value: str) -> str:
        pieces = re.split(r"[-_\s]+", value)
        if not pieces:
            return value
        return pieces[0].lower() + "".join(piece[:1].upper() + piece[1:] for piece in pieces[1:])

    def _list(self, value) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "add",
    "build",
    "create",
    "implement",
    "fix",
    "make",
    "should",
}
