import pandas as pd
import pytest

from sales_pipeline.exceptions import SchemaValidationError
from sales_pipeline.validation import validate_orders, validate_schema


def test_validate_orders_returns_quality_counts(valid_orders):
    result = validate_orders(valid_orders)
    assert result.total_records == 2
    assert result.valid_records == 2
    assert result.invalid_records == 0
    assert result.issue_counts == {}


def test_validate_orders_reports_field_and_business_rule_errors(valid_orders):
    invalid = valid_orders.iloc[[0]].copy()
    invalid = invalid.astype({"quantity": "object", "unit_price": "object"})
    invalid.loc[:, "order_date"] = "not-a-date"
    invalid.loc[:, "quantity"] = 1.5
    invalid.loc[:, "unit_price"] = "unknown"
    result = validate_orders(invalid)
    assert result.invalid_records == 1
    assert result.issue_counts == {
        "invalid_order_date": 1,
        "invalid_quantity_type": 1,
        "invalid_unit_price_type": 1,
    }


def test_validate_orders_rejects_duplicate_order_id(valid_orders):
    duplicate = pd.concat([valid_orders, valid_orders.iloc[[0]]], ignore_index=True)
    result = validate_orders(duplicate)
    assert result.issue_counts["duplicate_order_id"] == 1
    assert result.invalid_records == 1


def test_validate_orders_rejects_invalid_date(valid_orders):
    invalid = valid_orders.iloc[[0]].copy()
    invalid.loc[:, "order_date"] = "2026-99-99"
    assert validate_orders(invalid).issue_counts["invalid_order_date"] == 1


def test_validate_orders_rejects_missing_customer(valid_orders):
    invalid = valid_orders.iloc[[0]].copy()
    invalid.loc[:, "customer_id"] = None
    assert validate_orders(invalid).issue_counts["missing_customer_id"] == 1


@pytest.mark.parametrize("quantity", [0, -1])
def test_validate_orders_rejects_non_positive_quantity(valid_orders, quantity):
    invalid = valid_orders.iloc[[0]].copy()
    invalid.loc[:, "quantity"] = quantity
    assert validate_orders(invalid).issue_counts["non_positive_quantity"] == 1


def test_validate_orders_accepts_zero_price_and_rejects_negative_price(valid_orders):
    boundary = valid_orders.copy()
    boundary.loc[0, "unit_price"] = 0
    boundary.loc[1, "unit_price"] = -0.01
    result = validate_orders(boundary)
    assert result.issue_counts["negative_unit_price"] == 1
    assert result.valid_records == 1


def test_validate_schema_lists_missing_columns(valid_orders):
    with pytest.raises(SchemaValidationError, match="status"):
        validate_schema(valid_orders.drop(columns=["status"]))


def test_validate_schema_rejects_duplicate_columns(valid_orders):
    duplicated = pd.concat([valid_orders, valid_orders[["status"]]], axis=1)
    with pytest.raises(SchemaValidationError, match="duplicate columns"):
        validate_schema(duplicated)
