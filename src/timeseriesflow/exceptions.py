"""Exception hierarchy for TimeSeriesFlow."""


class FlowError(Exception):
    """Base exception for all TimeSeriesFlow errors."""


class EntityProcessingError(FlowError):
    """Raised when an entity processor fails after all retries."""

    def __init__(self, entity_id: object, message: str, cause: BaseException | None = None) -> None:
        self.entity_id = entity_id
        self.cause = cause
        detail = f" (caused by {type(cause).__name__}: {cause})" if cause else ""
        super().__init__(f"Entity {entity_id!r} failed: {message}{detail}")


class RetryExhaustedError(EntityProcessingError):
    """Raised when retry attempts are exhausted for an entity."""


class CheckpointError(FlowError):
    """Raised when checkpoint read or write operations fail."""
