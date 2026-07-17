"""Dataset-level schema validation."""

import pandas as pd

from sales_pipeline.config import REQUIRED_COLUMNS
from sales_pipeline.exceptions import SchemaValidationError


def validate_schema(frame: pd.DataFrame) -> None:
    """Validate required columns and reject ambiguous duplicate headers."""
    duplicate_columns = frame.columns[frame.columns.duplicated()].tolist()
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    problems: list[str] = []
    if missing_columns:
        problems.append(f"missing required columns: {', '.join(missing_columns)}")
    if duplicate_columns:
        problems.append(f"duplicate columns: {', '.join(duplicate_columns)}")
    if problems:
        raise SchemaValidationError("Invalid sales order schema: " + "; ".join(problems))
