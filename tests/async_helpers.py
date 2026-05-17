"""Helpers for async-style tests without a real event loop."""

from __future__ import annotations

import inspect
import sys
import types
from typing import Any


def run_coro(awaitable: Any):
    """Drive awaitables that only rely on fake asyncio primitives."""
    if not inspect.isawaitable(awaitable):
        return awaitable

    iterator = awaitable.__await__()
    try:
        yielded = next(iterator)
        while True:
            yielded_result = run_coro(yielded)
            yielded = iterator.send(yielded_result)
    except StopIteration as exc:
        return exc.value


class _FakeLock:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeSemaphore(_FakeLock):
    def __init__(self, value: int):
        self.value = value


class FakeAsyncio(types.SimpleNamespace):
    def __init__(self):
        self.semaphore_values: list[int] = []
        super().__init__(
            Lock=_FakeLock,
            Semaphore=self._make_semaphore,
            create_task=lambda coro: coro,
            as_completed=lambda tasks: list(tasks),
            to_thread=self._to_thread,
            sleep=self._sleep,
            run=run_coro,
        )

    def _make_semaphore(self, value: int):
        self.semaphore_values.append(value)
        return _FakeSemaphore(value)

    async def _to_thread(self, func, *args, **kwargs):
        return func(*args, **kwargs)

    async def _sleep(self, delay: float):
        return None


def install_fake_asyncio(monkeypatch):
    fake = FakeAsyncio()
    monkeypatch.setitem(sys.modules, "asyncio", fake)
    return fake
