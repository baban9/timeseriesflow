"""Retry policies for entity processing."""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import TypeVar

from timeseriesflow.exceptions import RetryExhaustedError

T = TypeVar("T")


@dataclass(slots=True)
class RetryPolicy:
    """Configurable retry behavior with exponential backoff."""

    max_attempts: int = 3
    initial_delay_seconds: float = 0.5
    max_delay_seconds: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Iterable[type[BaseException]] = field(
        default_factory=lambda: (TimeoutError, ConnectionError, OSError)
    )

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")

    def is_retryable(self, exc: BaseException) -> bool:
        if isinstance(exc, RetryExhaustedError):
            return False
        return any(isinstance(exc, exc_type) for exc_type in self.retryable_exceptions)

    def delay_for_attempt(self, attempt: int) -> float:
        """Return delay in seconds before the given attempt (1-indexed)."""
        if attempt <= 1:
            return 0.0
        delay = self.initial_delay_seconds * (self.exponential_base ** (attempt - 2))
        delay = min(delay, self.max_delay_seconds)
        if self.jitter:
            delay *= random.uniform(0.5, 1.5)
        return delay

    def run(self, func: Callable[[], T], *, entity_id: object | None = None) -> T:
        """Execute func with retries according to this policy."""
        last_exc: BaseException | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func()
            except BaseException as exc:
                last_exc = exc
                if attempt >= self.max_attempts or not self.is_retryable(exc):
                    break
                time.sleep(self.delay_for_attempt(attempt + 1))
        assert last_exc is not None
        raise RetryExhaustedError(
            entity_id=entity_id if entity_id is not None else "unknown",
            message=f"exhausted {self.max_attempts} attempt(s)",
            cause=last_exc,
        ) from last_exc
