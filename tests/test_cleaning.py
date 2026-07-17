import pandas as pd

from sales_pipeline.cleaning import clean_orders


def test_clean_orders_normalizes_accepted_values(valid_orders):
    result = clean_orders(valid_orders)
    assert len(result.accepted) == 2
    assert result.accepted.loc[0, "product_name"] == "Mouse"
    assert result.accepted.loc[0, "status"] == "completed"
    assert pd.api.types.is_datetime64_any_dtype(result.accepted["order_date"])


def test_clean_orders_quarantines_multiple_quality_issues(valid_orders):
    bad = valid_orders.iloc[[0]].copy()
    bad.loc[:, "customer_id"] = None
    bad.loc[:, "quantity"] = -1
    bad.loc[:, "status"] = "unknown"
    result = clean_orders(pd.concat([valid_orders, bad], ignore_index=True))
    assert len(result.rejected) == 1
    reasons = result.rejected.loc[0, "rejection_reasons"]
    assert "missing_customer_id" in reasons
    assert "invalid_quantity" in reasons
    assert "unsupported_status" in reasons


def test_clean_orders_flags_duplicate_rows_and_order_ids(valid_orders):
    data = pd.concat([valid_orders, valid_orders.iloc[[0]], valid_orders.iloc[[0]]], ignore_index=True)
    result = clean_orders(data)
    assert len(result.accepted) == 2
    assert result.issue_counts["duplicate_row"] == 2
    assert result.issue_counts["duplicate_order_id"] == 2
