from __future__ import annotations

import ast
import concurrent.futures
import inspect
import signal
import textwrap
import threading
from collections.abc import Callable
from typing import Any


BLOCKED_IMPORTS = {"os", "subprocess", "socket", "sys", "shutil"}


class CheckValidator:
    def validate_custom_check(self, check_fn: Callable[[dict[str, Any], Any], bool], agent_id: str) -> tuple[bool, list[str]]:
        errors: list[str] = []
        errors.extend(self._validate_signature(check_fn))
        errors.extend(self._validate_imports(check_fn))
        if errors:
            return False, errors

        try:
            result = self._run_with_timeout(check_fn, {}, {})
        except TimeoutError:
            return False, [f"Custom check for {agent_id} did not complete within 2 seconds"]
        except Exception as exc:
            return False, [f"Custom check for {agent_id} raised during validation: {exc}"]

        if not isinstance(result, bool):
            errors.append(f"Custom check for {agent_id} must return bool, got {type(result).__name__}")
        return not errors, errors

    def _validate_signature(self, check_fn: Callable[..., Any]) -> list[str]:
        signature = inspect.signature(check_fn)
        params = list(signature.parameters.values())
        if len(params) != 2 or [param.name for param in params] != ["output", "spec"]:
            return ["Custom check signature must be exactly (output, spec)"]
        return []

    def _validate_imports(self, check_fn: Callable[..., Any]) -> list[str]:
        try:
            source = inspect.getsource(check_fn)
        except OSError:
            return []
        tree = ast.parse(textwrap.dedent(source))
        errors: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root in BLOCKED_IMPORTS:
                        errors.append(f"Custom check imports blocked module '{root}'")
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".", 1)[0]
                if root in BLOCKED_IMPORTS:
                    errors.append(f"Custom check imports blocked module '{root}'")
        return errors

    def _run_with_timeout(self, check_fn: Callable[..., Any], output: dict[str, Any], spec: Any) -> Any:
        if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
            def _timeout_handler(signum: int, frame: Any) -> None:
                raise TimeoutError

            previous = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(2)
            try:
                return check_fn(output, spec)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, previous)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(check_fn, output, spec)
            return future.result(timeout=2)
