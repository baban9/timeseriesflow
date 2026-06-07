"""CLI error types."""

from __future__ import annotations


class CliError(Exception):
    """User-facing CLI error with a friendly message."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        self.message = message
        self.hint = hint
        super().__init__(message)

    def format(self) -> str:
        if self.hint:
            return f"{self.message}\n\nHint: {self.hint}"
        return self.message
