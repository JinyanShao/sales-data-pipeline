"""Row-level normalization and data quality handling."""

from dataclasses import dataclass

import pandas as pd

from sales_pipeline.config import SUPPORTED_STATUSES


@dataclass(frozen=True)
class CleaningResult:
    """Accepted and rejected records produced by cleaning."""

    accepted: pd.DataFrame
    rejected: pd.DataFrame
    issue_counts: dict[str, int]


def clean_orders(
    frame: pd.DataFrame,
    supported_statuses: frozenset[str] = SUPPORTED_STATUSES,
) -> CleaningResult:
    """Normalize fields and quarantine records that violate row-level rules."""
    data = frame.copy()
    original = frame.copy()

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
        data[column] = data[column].astype("string").str.strip()
        data[column] = data[column].mask(data[column].eq(""), pd.NA)
    data["status"] = data["status"].str.lower()
    data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
    data["quantity"] = pd.to_numeric(data["quantity"], errors="coerce")
    data["unit_price"] = pd.to_numeric(data["unit_price"], errors="coerce")

    issue_masks: dict[str, pd.Series] = {
        "duplicate_row": original.duplicated(keep="first"),
        "missing_order_id": data["order_id"].isna(),
        "duplicate_order_id": data["order_id"].notna() & data["order_id"].duplicated(keep="first"),
        "invalid_order_date": data["order_date"].isna(),
        "missing_customer_id": data["customer_id"].isna(),
        "missing_product_id": data["product_id"].isna(),
        "missing_product_name": data["product_name"].isna(),
        "invalid_quantity": data["quantity"].isna() | data["quantity"].le(0),
        "invalid_unit_price": data["unit_price"].isna() | data["unit_price"].lt(0),
        "unsupported_status": data["status"].isna() | ~data["status"].isin(supported_statuses),
    }

    reasons = pd.Series([[] for _ in range(len(data))], index=data.index, dtype="object")
    for issue, mask in issue_masks.items():
        reasons.loc[mask] = reasons.loc[mask].apply(lambda values, name=issue: [*values, name])

    rejected_mask = reasons.str.len().gt(0)
    rejected = data.loc[rejected_mask].copy()
    rejected["rejection_reasons"] = reasons.loc[rejected_mask].str.join(";")
    accepted = data.loc[~rejected_mask].copy().reset_index(drop=True)
    rejected = rejected.reset_index(drop=True)

    accepted["quantity"] = accepted["quantity"].astype("int64")
    accepted["unit_price"] = accepted["unit_price"].astype("float64")
    accepted["order_date"] = accepted["order_date"].dt.normalize()

    issue_counts = {name: int(mask.sum()) for name, mask in issue_masks.items() if mask.any()}
    return CleaningResult(accepted=accepted, rejected=rejected, issue_counts=issue_counts)
