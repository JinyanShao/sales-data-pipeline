"""Revenue calculations and sales aggregations."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

import pandas as pd

from sales_pipeline.config import REVENUE_STATUSES

ONE_CENT = Decimal("0.01")


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
    """Calculate integer-cent revenue and build business summaries."""
    orders = frame.copy()
    orders["unit_price_cents"] = orders["unit_price"].map(_to_cents).astype("int64")
    orders["gross_revenue_cents"] = orders["quantity"] * orders["unit_price_cents"]
    orders["sales_revenue_cents"] = orders["gross_revenue_cents"].where(
        orders["status"].isin(revenue_statuses), 0
    )
    orders["unit_price"] = orders["unit_price_cents"] / 100
    orders["gross_revenue"] = orders["gross_revenue_cents"] / 100
    orders["sales_revenue"] = orders["sales_revenue_cents"] / 100
    orders["order_month"] = orders["order_date"].dt.to_period("M").astype("string")

    customer = _summarize(orders, ["customer_id"], ["revenue_cents", "customer_id"])
    product = _summarize(
        orders,
        ["product_id", "product_name", "category"],
        ["revenue_cents", "product_id"],
    )
    category = _summarize(orders, ["category"], ["revenue_cents", "category"])
    month = _summarize(orders, ["order_month"], ["order_month"], descending=False)
    return SalesSummaries(
        orders=orders,
        by_customer=customer,
        by_product=product,
        by_category=category,
        by_month=month,
    )


def _to_cents(value: float) -> int:
    amount = Decimal(str(value)).quantize(ONE_CENT, rounding=ROUND_HALF_UP)
    return int(amount * 100)


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
            gross_revenue_cents=("gross_revenue_cents", "sum"),
            revenue_cents=("sales_revenue_cents", "sum"),
        )
        .sort_values(sort_columns, ascending=not descending)
        .reset_index(drop=True)
    )
    summary["gross_revenue"] = summary["gross_revenue_cents"] / 100
    summary["revenue"] = summary["revenue_cents"] / 100
    return summary
