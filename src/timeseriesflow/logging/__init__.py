"""Logging setup for TimeSeriesFlow."""

from __future__ import annotations

import logging
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_LOGGER_CONFIGURED = False


def setup_logging(level: LogLevel = "INFO") -> logging.Logger:
    """Configure and return the package logger."""
    global _LOGGER_CONFIGURED
    logger = logging.getLogger("timeseriesflow")
    if not _LOGGER_CONFIGURED:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.propagate = False
        _LOGGER_CONFIGURED = True
    logger.setLevel(level)
    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a child logger under the timeseriesflow namespace."""
    if name:
        return logging.getLogger(f"timeseriesflow.{name}")
    return logging.getLogger("timeseriesflow")
