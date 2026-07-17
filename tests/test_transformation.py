from sales_pipeline.cleaning import clean_orders
from sales_pipeline.transformation import transform_orders


def test_transform_orders_recognizes_only_completed_or_shipped_revenue(valid_orders):
    cleaned = clean_orders(valid_orders).accepted
    result = transform_orders(cleaned)
    assert result.orders["order_revenue"].tolist() == [20.0, 0.0]
    assert result.by_customer.loc[result.by_customer["customer_id"] == "C-1", "revenue"].item() == 20.0


def test_transform_orders_builds_monthly_summary(valid_orders):
    result = transform_orders(clean_orders(valid_orders).accepted)
    assert result.by_month["order_month"].tolist() == ["2026-01", "2026-02"]
    assert result.by_month["order_count"].tolist() == [1, 1]
