"""Tests for retry policy."""

from __future__ import annotations

import pytest

from timeseriesflow.exceptions import RetryExhaustedError
from timeseriesflow.retry import RetryPolicy


def test_retry_policy_succeeds_on_second_attempt() -> None:
    calls = {"count": 0}

    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 2:
            raise TimeoutError("temporary")
        return "ok"

    policy = RetryPolicy(max_attempts=3, initial_delay_seconds=0.01, jitter=False)
    assert policy.run(flaky) == "ok"
    assert calls["count"] == 2


def test_retry_policy_exhausted() -> None:
    policy = RetryPolicy(max_attempts=2, initial_delay_seconds=0.01, jitter=False)

    def always_fail() -> None:
        raise ConnectionError("down")

    with pytest.raises(RetryExhaustedError):
        policy.run(always_fail, entity_id="E1")
