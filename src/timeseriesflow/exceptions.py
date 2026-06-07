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


class ColumnValidationError(FlowError):
    """Raised when required dataframe columns are missing."""


class SourceError(FlowError):
    """Base exception for data source errors."""


class SourceNotFoundError(SourceError):
    """Raised when a source location does not exist or is unreachable."""

    def __init__(self, source: str, path: object) -> None:
        self.source = source
        self.path = path
        super().__init__(f"{source} not found: {path!r}")


class SourceSchemaError(SourceError):
    """Raised when loaded data does not match the expected schema."""

    def __init__(self, source: str, message: str, *, missing: list[str] | None = None) -> None:
        self.source = source
        self.missing = missing or []
        detail = f": missing column(s) {self.missing!r}" if self.missing else ""
        super().__init__(f"{source} schema validation failed: {message}{detail}")


class SourceLoadError(SourceError):
    """Raised when data cannot be read from a source."""

    def __init__(self, source: str, message: str, cause: BaseException | None = None) -> None:
        self.source = source
        self.cause = cause
        detail = f" (caused by {type(cause).__name__}: {cause})" if cause else ""
        super().__init__(f"{source} load failed: {message}{detail}")
