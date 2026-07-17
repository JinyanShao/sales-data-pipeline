"""Schema and row-level validation for sales orders."""

from dataclasses import dataclass

import pandas as pd

from sales_pipeline.config import REQUIRED_COLUMNS, SUPPORTED_STATUSES
from sales_pipeline.exceptions import SchemaValidationError


@dataclass(frozen=True)
class ValidationResult:
    """Counts and row-level reasons produced by order validation."""

    total_records: int
    valid_records: int
    invalid_records: int
    issue_counts: dict[str, int]
    row_errors: tuple[tuple[str, ...], ...]


def validate_schema(frame: pd.DataFrame) -> None:
    """Reject datasets that do not contain an unambiguous required schema."""
    duplicate_columns = frame.columns[frame.columns.duplicated()].tolist()
    missing_columns = sorted(set(REQUIRED_COLUMNS) - set(frame.columns))
    problems: list[str] = []
    if missing_columns:
        problems.append(f"missing required columns: {', '.join(missing_columns)}")
    if duplicate_columns:
        problems.append(f"duplicate columns: {', '.join(duplicate_columns)}")
    if problems:
        raise SchemaValidationError("Invalid sales order schema: " + "; ".join(problems))


def validate_orders(
    frame: pd.DataFrame,
    supported_statuses: frozenset[str] = SUPPORTED_STATUSES,
) -> ValidationResult:
    """Validate field values and return quality results without changing input data."""
    validate_schema(frame)
    data = frame.reset_index(drop=True).copy()
    text_columns = [
        "order_id",
        "customer_id",
        "product_id",
        "product_name",
        "category",
        "country",
        "status",
    ]
    for column in text_columns:
        data[column] = data[column].astype("string").str.strip().replace("", pd.NA)
    data["status"] = data["status"].str.lower()

    dates = pd.to_datetime(data["order_date"], errors="coerce")
    quantities = pd.to_numeric(data["quantity"], errors="coerce")
    prices = pd.to_numeric(data["unit_price"], errors="coerce")
    issue_masks: dict[str, pd.Series] = {
        "duplicate_row": frame.reset_index(drop=True).duplicated(keep="first"),
        "missing_order_id": data["order_id"].isna(),
        "duplicate_order_id": data["order_id"].notna() & data["order_id"].duplicated(keep="first"),
        "invalid_order_date": dates.isna(),
        "missing_customer_id": data["customer_id"].isna(),
        "missing_product_id": data["product_id"].isna(),
        "missing_product_name": data["product_name"].isna(),
        "missing_category": data["category"].isna(),
        "missing_country": data["country"].isna(),
        "invalid_quantity_type": quantities.isna() | quantities.mod(1).ne(0),
        "non_positive_quantity": quantities.notna() & quantities.le(0),
        "invalid_unit_price_type": prices.isna(),
        "negative_unit_price": prices.notna() & prices.lt(0),
        "unsupported_status": data["status"].isna() | ~data["status"].isin(supported_statuses),
    }

    errors: list[list[str]] = [[] for _ in range(len(data))]
    for issue, mask in issue_masks.items():
        for position in mask[mask].index:
            errors[position].append(issue)
    row_errors = tuple(tuple(row) for row in errors)
    invalid_records = sum(bool(row) for row in row_errors)
    return ValidationResult(
        total_records=len(data),
        valid_records=len(data) - invalid_records,
        invalid_records=invalid_records,
        issue_counts={name: int(mask.sum()) for name, mask in issue_masks.items() if mask.any()},
        row_errors=row_errors,
    )
