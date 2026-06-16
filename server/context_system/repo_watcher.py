from __future__ import annotations

import asyncio
from pathlib import Path

from context_system.cache_invalidator import CascadeInvalidationService
from context_system.models import InvalidationEvent


class RepoWatcherManager:
    def __init__(self, invalidator: CascadeInvalidationService | None = None):
        self.invalidator = invalidator or CascadeInvalidationService()
        self._observers: dict[str, object] = {}
        self.events: asyncio.Queue[InvalidationEvent] = asyncio.Queue()

    async def watch(self, repo_path: str) -> None:
        repo_path = str(Path(repo_path).resolve())
        if repo_path in self._observers:
            return
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer
        except Exception as exc:
            raise RuntimeError("watchdog is required for live repo watching") from exc

        loop = asyncio.get_running_loop()
        manager = self

        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.is_directory:
                    return
                loop.call_soon_threadsafe(lambda: asyncio.create_task(manager._invalidate(repo_path, event.src_path)))

            def on_created(self, event):
                if event.is_directory:
                    return
                loop.call_soon_threadsafe(lambda: asyncio.create_task(manager._invalidate(repo_path, event.src_path)))

        observer = Observer()
        observer.schedule(Handler(), path=repo_path, recursive=True)
        observer.start()
        self._observers[repo_path] = observer

    async def stop(self, repo_path: str) -> None:
        repo_path = str(Path(repo_path).resolve())
        observer = self._observers.pop(repo_path, None)
        if not observer:
            return
        await asyncio.to_thread(observer.stop)
        await asyncio.to_thread(observer.join, timeout=2)

    async def _invalidate(self, repo_path: str, file_path: str) -> None:
        try:
            event = await self.invalidator.invalidate_file(repo_path, file_path)
            await self.events.put(event)
        except Exception:
            return


repo_watcher_manager = RepoWatcherManager()
