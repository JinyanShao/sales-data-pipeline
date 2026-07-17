import pandas as pd
import pytest

from sales_pipeline.exceptions import InputFileError
from sales_pipeline.ingestion import read_orders


def test_read_orders_preserves_identifiers(tmp_path):
    source = tmp_path / "orders.csv"
    source.write_text("order_id,customer_id,product_id\n001,002,003\n", encoding="utf-8")
    result = read_orders(source)
    assert result.loc[0, "order_id"] == "001"
    assert isinstance(result, pd.DataFrame)


def test_read_orders_rejects_missing_file(tmp_path):
    with pytest.raises(InputFileError, match="does not exist"):
        read_orders(tmp_path / "missing.csv")


def test_read_orders_rejects_empty_file(tmp_path):
    source = tmp_path / "empty.csv"
    source.touch()
    with pytest.raises(InputFileError, match="empty"):
        read_orders(source)


def test_read_orders_rejects_header_only_csv(tmp_path):
    source = tmp_path / "headers.csv"
    source.write_text("order_id,order_date,customer_id\n", encoding="utf-8")
    with pytest.raises(InputFileError, match="no records"):
        read_orders(source)


def test_read_orders_rejects_directory(tmp_path):
    with pytest.raises(InputFileError, match="not a file"):
        read_orders(tmp_path)
