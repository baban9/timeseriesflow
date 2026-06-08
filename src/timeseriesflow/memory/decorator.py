"""Memory tracking decorator."""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from timeseriesflow.logging import get_logger
from timeseriesflow.memory.tracker import MemoryTracker

F = TypeVar("F", bound=Callable[..., Any])


def track_memory(
    func: F | None = None,
    *,
    warning_threshold_mb: float | None = None,
    logger: logging.Logger | None = None,
    enabled: bool = True,
) -> F | Callable[[F], F]:
    """Decorate a function to track memory usage and runtime.

    The wrapped function returns its original result unchanged. Metrics are
    stored on ``wrapper.last_metrics`` and logged at DEBUG level.

    Example:
        @track_memory
        def build_frame():
            return pd.DataFrame({"a": range(100_000)})

        build_frame()
        print(build_frame.last_metrics.to_dict())
    """

    def decorator(fn: F) -> F:
        log = logger or get_logger("memory")

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            tracker = MemoryTracker(
                enabled=enabled,
                warning_threshold_mb=warning_threshold_mb,
                logger=log,
            )
            with tracker.measure():
                result = fn(*args, **kwargs)
            metrics = tracker.last_metrics
            wrapper.last_metrics = metrics  # type: ignore[attr-defined]
            if metrics is not None:
                log.debug(
                    "%s metrics: %s",
                    fn.__qualname__,
                    metrics.to_dict(),
                )
            return result

        wrapper.last_metrics = None  # type: ignore[attr-defined]
        return wrapper  # type: ignore[return-value]

    if func is not None:
        return decorator(func)
    return decorator
