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


def test_validate_schema_lists_missing_columns(valid_orders):
    with pytest.raises(SchemaValidationError, match="status"):
        validate_schema(valid_orders.drop(columns=["status"]))


def test_validate_schema_rejects_duplicate_columns(valid_orders):
    duplicated = pd.concat([valid_orders, valid_orders[["status"]]], axis=1)
    with pytest.raises(SchemaValidationError, match="duplicate columns"):
        validate_schema(duplicated)
