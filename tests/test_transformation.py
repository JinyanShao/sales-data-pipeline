from sales_pipeline.cleaning import clean_orders
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_orders


def transformed(valid_orders):
    cleaned = clean_orders(valid_orders, validate_orders(valid_orders)).accepted
    return transform_orders(cleaned)


def test_transform_orders_calculates_gross_and_sales_revenue(valid_orders):
    result = transformed(valid_orders)
    assert result.orders["gross_revenue"].tolist() == [20.0, 50.0]
    assert result.orders["sales_revenue"].tolist() == [20.0, 0.0]


def test_transform_orders_builds_all_summaries(valid_orders):
    result = transformed(valid_orders)
    assert result.by_month["order_month"].tolist() == ["2026-01", "2026-02"]
    assert result.by_customer["order_count"].sum() == 2
    assert result.by_product["units_ordered"].sum() == 3
    assert set(result.by_category["category"]) == {"Electronics", "Furniture"}
