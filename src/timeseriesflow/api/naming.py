"""Shared helpers for API naming aliases."""


def resolve_entity_column_name(
    *,
    entity_key: str | None = None,
    entity_column: str | None = None,
) -> str:
    """Resolve entity_key and entity_column to a single column name."""
    if entity_key and entity_column and entity_key != entity_column:
        raise ValueError("entity_key and entity_column must match when both are provided")
    resolved = entity_key or entity_column
    if not resolved:
        raise ValueError("entity_key or entity_column is required")
    return resolved
