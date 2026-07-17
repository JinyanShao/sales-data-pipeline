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
    assert result.orders["gross_revenue_cents"].tolist() == [2000, 5000]


def test_transform_orders_builds_all_summaries(valid_orders):
    result = transformed(valid_orders)
    assert result.by_month["order_month"].tolist() == ["2026-01", "2026-02"]
    assert result.by_customer["order_count"].sum() == 2
    assert result.by_product["units_ordered"].sum() == 3
    assert set(result.by_category["category"]) == {"Electronics", "Furniture"}


def test_transform_orders_uses_integer_cents_for_fractional_amounts(valid_orders):
    orders = valid_orders.iloc[[0]].copy()
    orders.loc[:, "quantity"] = 3
    orders.loc[:, "unit_price"] = 0.1
    result = transformed(orders)
    assert result.orders["gross_revenue_cents"].item() == 30
    assert result.orders["sales_revenue_cents"].item() == 30
    assert result.by_customer["revenue_cents"].sum() == 30


def test_transform_orders_sums_multiple_fractional_amounts_exactly(valid_orders):
    orders = valid_orders.copy()
    orders.loc[:, "status"] = "completed"
    orders.loc[:, "quantity"] = [3, 7]
    orders.loc[:, "unit_price"] = [0.1, 0.1]
    result = transformed(orders)
    assert result.orders["sales_revenue_cents"].sum() == 100
    assert result.by_customer["revenue_cents"].sum() == 100
    assert result.by_product["revenue_cents"].sum() == 100
    assert result.by_category["revenue_cents"].sum() == 100
    assert result.by_month["revenue_cents"].sum() == 100
