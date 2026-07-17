"""Normalization and isolation of invalid sales records."""

from dataclasses import dataclass

import pandas as pd

from sales_pipeline.validation import ValidationResult


@dataclass(frozen=True)
class CleaningResult:
    """Accepted and rejected records produced by cleaning."""

    accepted: pd.DataFrame
    rejected: pd.DataFrame


def clean_orders(frame: pd.DataFrame, validation: ValidationResult) -> CleaningResult:
    """Normalize values and split validated data into accepted and rejected records."""
    data = frame.reset_index(drop=True).copy()
    text_columns = ["order_id", "customer_id", "product_id", "product_name", "category", "country", "status"]
    for column in text_columns:
        data[column] = data[column].astype("string").str.strip().replace("", pd.NA)
    data["status"] = data["status"].str.lower()
    data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["unit_price"] = pd.to_numeric(data["unit_price"], errors="coerce")

    rejected_mask = pd.Series([bool(errors) for errors in validation.row_errors])
    rejected = data.loc[rejected_mask].copy()
    rejected["rejection_reasons"] = [";".join(validation.row_errors[position]) for position in rejected.index]
    accepted = data.loc[~rejected_mask].copy()
    accepted["quantity"] = accepted["quantity"].astype("int64")
    accepted["unit_price"] = accepted["unit_price"].astype("float64")
    accepted["order_date"] = accepted["order_date"].dt.normalize()
    return CleaningResult(accepted=accepted.reset_index(drop=True), rejected=rejected.reset_index(drop=True))
