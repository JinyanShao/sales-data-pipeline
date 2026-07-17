import pandas as pd
import pytest

from sales_pipeline.exceptions import SchemaValidationError
from sales_pipeline.validation import validate_schema


def test_validate_schema_accepts_required_columns(valid_orders):
    validate_schema(valid_orders)


def test_validate_schema_lists_missing_columns(valid_orders):
    with pytest.raises(SchemaValidationError, match="status"):
        validate_schema(valid_orders.drop(columns=["status"]))


def test_validate_schema_rejects_duplicate_columns(valid_orders):
    duplicated = pd.concat([valid_orders, valid_orders[["status"]]], axis=1)
    with pytest.raises(SchemaValidationError, match="duplicate columns"):
        validate_schema(duplicated)
