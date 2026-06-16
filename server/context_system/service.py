from __future__ import annotations

import asyncio
import hashlib
import os
import re
from pathlib import Path

from context_system.centrality_scorer import CentralityScorer
from context_system.db import ContextDatabase, context_db
from context_system.domain_analyzer import ProjectIntelligence
from context_system.final_scorer import FinalScorer
from context_system.graph_builder import GraphBuilder, list_source_files
from context_system.grep_scanner import GrepScanner
from context_system.intent_parser import IntentParser
from context_system.models import ContextMemory, ContextPayload, ContextStatus, SubgraphAssignment
from context_system.payload_builder import PayloadBuilder
from context_system.project_reader import ProjectReader
from context_system.repo_orientator import RepoOrientator
from context_system.semantic_searcher import SemanticSearcher, embedding_provider
from context_system.subgraph_partitioner import SubgraphPartitioner


class ContextUnderstandingSystem:
    def __init__(self, db: ContextDatabase = context_db):
        self.db = db
        self.intent_parser = IntentParser()
        self.grep_scanner = GrepScanner(db)
        self.semantic_searcher = SemanticSearcher(db)
        self.project_reader = ProjectReader()
        self.graph_builder = GraphBuilder(db)
        self.centrality_scorer = CentralityScorer()
        self.final_scorer = FinalScorer()
        self.orientator = RepoOrientator()
        self.project_intelligence = ProjectIntelligence(db)
        self.subgraph_partitioner = SubgraphPartitioner()

    async def startup(self) -> None:
        if self._use_local_embeddings():
            await embedding_provider.load()

    async def analyze(self, repo_path: str, prompt: str, task_id: str, token_budget: int = 2048) -> ContextPayload:
        if not repo_path:
            return ContextPayload(task=prompt, files=[], relationships=[], change_surface=[], gaps=[])
        repo_path = str(Path(repo_path).resolve())
        if not repo_path or not Path(repo_path).exists():
            return ContextPayload(task=prompt, files=[], relationships=[], change_surface=[], gaps=[])
        orientation_task = asyncio.create_task(self.orientator.orient(repo_path))
        signals = await self.intent_parser.parse(prompt)
        memory_terms = signals.grep_terms + re.findall(r"[A-Za-z0-9_]{3,}", prompt)
        memories = await self.db.get_context_memories(repo_path, memory_terms, signals.domain)

        # Grep always runs first and persists hits immediately.
        grep_matches = await self.grep_scanner.scan(repo_path, signals, task_id, prompt)
        graph_scores, new_edges = await self.graph_builder.build_from_matches(repo_path, grep_matches)
        all_edges = await self.graph_builder.load_edges(repo_path)
        if new_edges:
            all_edges = [*all_edges, *new_edges]
        centrality = self.centrality_scorer.compute(all_edges)
        if self._use_local_embeddings():
            semantic_chunks = await self.semantic_searcher.search(repo_path, prompt, grep_matches, task_id)
        else:
            semantic_chunks = await self.project_reader.read_and_rank(
                repo_path,
                prompt,
                grep_matches,
                task_id,
                signals=signals,
                memories=memories,
            )
        final_scores = self.final_scorer.merge(
            signals.task_type,
            grep_matches,
            semantic_chunks,
            graph_scores,
            centrality,
        )
        await orientation_task
        await self.project_intelligence.analyze(repo_path, all_edges, centrality)
        payload = await PayloadBuilder(token_budget).build(
            repo_path,
            prompt,
            signals,
            final_scores,
            semantic_chunks,
            all_edges,
        )
        await self._log_observability(repo_path, payload)
        await self._remember_payload(repo_path, prompt, signals.domain, payload)
        return payload

    async def index_repo(self, repo_path: str) -> dict:
        repo_path = str(Path(repo_path).resolve())
        orientation = await self.orientator.orient(repo_path)
        indexed_count = await self.graph_builder.index_repo(repo_path)
        edges = await self.graph_builder.load_edges(repo_path)
        centrality = self.centrality_scorer.compute(edges)
        await self.project_intelligence.analyze(repo_path, edges, centrality)
        return {
            "repo_path": repo_path,
            "indexed_files": indexed_count,
            "detected_languages": orientation.detected_languages,
            "conventions": orientation.conventions,
        }

    async def status(self, repo_path: str) -> ContextStatus:
        repo_path = str(Path(repo_path).resolve())
        files = await list_source_files(repo_path)
        raw = await self.db.status(repo_path, len(files))
        return ContextStatus(repo_path=repo_path, file_count=len(files), **raw)

    async def partition(self, repo_path: str, prompt: str, agents: list[str]) -> list[SubgraphAssignment]:
        payload = await self.analyze(repo_path, prompt, task_id=f"partition:{hash(prompt)}")
        edges = await self.graph_builder.load_edges(str(Path(repo_path).resolve()))
        return self.subgraph_partitioner.partition(str(Path(repo_path).resolve()), prompt, agents, payload, edges)

    def payload_to_prose(self, payload: ContextPayload) -> str:
        return PayloadBuilder().to_prose(payload)

    async def _log_observability(self, repo_path: str, payload: ContextPayload) -> None:
        status = await self.status(repo_path)
        await self.db.log_metric("index_coverage_percent", status.index_coverage * 100, {"repo_path": repo_path})
        await self.db.log_metric("cache_hit_rate", status.cache_hit_rate, {"repo_path": repo_path})
        await self.db.log_metric("payload_token_count", len(payload.model_dump_json(by_alias=True)) / 4, {"repo_path": repo_path})

    def _use_local_embeddings(self) -> bool:
        return os.getenv("CONTEXT_USE_LOCAL_EMBEDDINGS", "").lower() in {"1", "true", "yes"}

    async def _remember_payload(self, repo_path: str, prompt: str, domain: str, payload: ContextPayload) -> None:
        if not payload.files:
            return
        files = [file.path for file in payload.files[:10]]
        summary = "; ".join(
            f"{item.path}: {item.role} ({item.confidence:.2f})"
            for item in payload.files[:6]
        )
        task_signature = self._task_signature(prompt, domain)
        confidence = max((file.confidence for file in payload.files), default=0.0)
        await self.db.upsert_context_memory(
            ContextMemory(
                repo_path=repo_path,
                task_signature=task_signature,
                prompt=prompt,
                domain=domain,
                files=files,
                summary=summary,
                confidence=confidence,
            )
        )

    def _task_signature(self, prompt: str, domain: str) -> str:
        words = [
            word.lower()
            for word in re.findall(r"[A-Za-z0-9_]{3,}", prompt)
            if word.lower() not in {"the", "and", "for", "with", "that", "this", "add", "fix", "make"}
        ]
        stable = " ".join(sorted(set(words))[:12])
        return hashlib.sha256(f"{domain}:{stable}".encode()).hexdigest()


context_system = ContextUnderstandingSystem()
