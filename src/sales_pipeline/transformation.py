"""Revenue calculations and sales aggregations."""

from dataclasses import dataclass

import pandas as pd

from sales_pipeline.config import REVENUE_STATUSES


@dataclass(frozen=True)
class SalesSummaries:
    """Transformed orders and business-level aggregations."""

    orders: pd.DataFrame
    by_customer: pd.DataFrame
    by_product: pd.DataFrame
    by_category: pd.DataFrame
    by_month: pd.DataFrame


def transform_orders(
    frame: pd.DataFrame,
    revenue_statuses: frozenset[str] = REVENUE_STATUSES,
) -> SalesSummaries:
    """Calculate gross and recognized revenue and build business summaries."""
    orders = frame.copy()
    orders["gross_revenue"] = (orders["quantity"] * orders["unit_price"]).round(2)
    orders["sales_revenue"] = (
        orders["gross_revenue"].where(orders["status"].isin(revenue_statuses), 0.0).round(2)
    )
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype("string")

    customer = _summarize(orders, ["customer_id"], ["revenue", "customer_id"])
    product = _summarize(
        orders,
        ["product_id", "product_name", "category"],
        ["revenue", "product_id"],
    )
    category = _summarize(orders, ["category"], ["revenue", "category"])
    month = _summarize(orders, ["order_month"], ["order_month"], descending=False)
    return SalesSummaries(
        orders=orders,
        by_customer=customer,
        by_product=product,
        by_category=category,
        by_month=month,
    )


def _summarize(
    orders: pd.DataFrame,
    group_columns: list[str],
    sort_columns: list[str],
    descending: bool = True,
) -> pd.DataFrame:
    summary = (
        orders.groupby(group_columns, as_index=False)
        .agg(
            order_count=("order_id", "nunique"),
            units_ordered=("quantity", "sum"),
            gross_revenue=("gross_revenue", "sum"),
            revenue=("sales_revenue", "sum"),
        )
        .sort_values(sort_columns, ascending=not descending)
        .reset_index(drop=True)
    )
    summary[["gross_revenue", "revenue"]] = summary[["gross_revenue", "revenue"]].round(2)
    return summary
