"""Business transformations and sales aggregations."""

from dataclasses import dataclass

import pandas as pd

from sales_pipeline.config import REVENUE_STATUSES


@dataclass(frozen=True)
class SalesSummaries:
    """Transformed orders and business-level aggregations."""

    orders: pd.DataFrame
    by_customer: pd.DataFrame
    by_product: pd.DataFrame
    by_month: pd.DataFrame


def transform_orders(
    frame: pd.DataFrame,
    revenue_statuses: frozenset[str] = REVENUE_STATUSES,
) -> SalesSummaries:
    """Calculate recognized revenue and customer, product, and monthly summaries."""
    orders = frame.copy()
    gross_value = orders["quantity"] * orders["unit_price"]
    orders["order_revenue"] = gross_value.where(orders["status"].isin(revenue_statuses), 0.0).round(2)
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype("string")

    customer = (
        orders.groupby("customer_id", as_index=False)
        .agg(order_count=("order_id", "nunique"), units_ordered=("quantity", "sum"), revenue=("order_revenue", "sum"))
        .sort_values(["revenue", "customer_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
    product = (
        orders.groupby(["product_id", "product_name", "category"], as_index=False)
        .agg(order_count=("order_id", "nunique"), units_ordered=("quantity", "sum"), revenue=("order_revenue", "sum"))
        .sort_values(["revenue", "product_id"], ascending=[False, True])
        .reset_index(drop=True)
    )
    month = (
        orders.groupby("order_month", as_index=False)
        .agg(order_count=("order_id", "nunique"), units_ordered=("quantity", "sum"), revenue=("order_revenue", "sum"))
        .sort_values("order_month")
        .reset_index(drop=True)
    )
    for summary in (customer, product, month):
        summary["revenue"] = summary["revenue"].round(2)
    return SalesSummaries(orders=orders, by_customer=customer, by_product=product, by_month=month)
