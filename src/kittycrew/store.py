from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from kittycrew.models import AppState

MutationResult = TypeVar("MutationResult")


class JsonStateStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    async def load(self) -> AppState:
        async with self._lock:
            return self._read_unlocked()

    async def mutate(self, operation: Callable[[AppState], MutationResult]) -> MutationResult:
        async with self._lock:
            state = self._read_unlocked()
            result = operation(state)
            self._write_unlocked(state)
            return result

    def _read_unlocked(self) -> AppState:
        if not self._path.exists():
            return AppState()

        raw = self._path.read_text(encoding="utf-8").strip()
        if not raw:
            return AppState()
        return AppState.model_validate_json(raw)

    def _write_unlocked(self, state: AppState) -> None:
        self._path.write_text(
            json.dumps(state.model_dump(mode="json"), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )