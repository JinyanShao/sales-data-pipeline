"""Consistency checks between cleaned orders and business summaries."""

from collections.abc import Iterable

import pandas as pd

from sales_pipeline.exceptions import ReconciliationError
from sales_pipeline.transformation import SalesSummaries


def reconcile_summaries(summaries: SalesSummaries) -> None:
    """Require every summary to agree with accepted order totals."""
    orders = summaries.orders
    expected = {
        "order_count": len(orders),
        "units_ordered": int(orders["quantity"].sum()),
        "gross_revenue_cents": int(orders["gross_revenue_cents"].sum()),
        "revenue_cents": int(orders["sales_revenue_cents"].sum()),
    }
    summary_tables: Iterable[tuple[str, pd.DataFrame]] = (
        ("customer", summaries.by_customer),
        ("product", summaries.by_product),
        ("category", summaries.by_category),
        ("month", summaries.by_month),
    )
    mismatches: list[str] = []
    for table_name, table in summary_tables:
        actual = {
            "order_count": int(table["order_count"].sum()),
            "units_ordered": int(table["units_ordered"].sum()),
            "gross_revenue_cents": int(table["gross_revenue_cents"].sum()),
            "revenue_cents": int(table["revenue_cents"].sum()),
        }
        for metric, expected_value in expected.items():
            if actual[metric] != expected_value:
                mismatches.append(
                    f"{table_name}.{metric}: expected {expected_value}, got {actual[metric]}"
                )
    if mismatches:
        raise ReconciliationError("Summary reconciliation failed: " + "; ".join(mismatches))
