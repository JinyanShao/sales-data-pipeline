"""CSV and JSON report generation."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from sales_pipeline.cleaning import CleaningResult
from sales_pipeline.transformation import SalesSummaries
from sales_pipeline.validation import ValidationResult


def build_pipeline_summary(
    source: Path,
    validation: ValidationResult,
    summaries: SalesSummaries,
) -> dict[str, Any]:
    """Build data-quality and business metrics for one pipeline run."""
    orders = summaries.orders
    sales_orders = orders.loc[orders["sales_revenue"].gt(0)]
    total_revenue = round(float(orders["sales_revenue"].sum()), 2)
    return {
        "source": str(source),
        "total_orders": validation.total_records,
        "valid_orders": validation.valid_records,
        "rejected_records": validation.invalid_records,
        "gross_revenue": round(float(orders["gross_revenue"].sum()), 2),
        "total_sales_revenue": total_revenue,
        "average_order_value": round(total_revenue / len(sales_orders), 2) if len(sales_orders) else 0.0,
        "unique_customers": int(orders["customer_id"].nunique()),
        "best_selling_product": _leading_value(summaries.by_product, "units_ordered", "product_name"),
        "highest_revenue_product": _leading_value(summaries.by_product, "revenue", "product_name"),
        "highest_revenue_customer": _leading_value(summaries.by_customer, "revenue", "customer_id"),
        "monthly_revenue": {
            str(month): round(float(revenue), 2)
            for month, revenue in zip(summaries.by_month["order_month"], summaries.by_month["revenue"])
        },
        "order_status_distribution": {
            str(status): int(count) for status, count in orders["status"].value_counts().items()
        },
        "issue_counts": validation.issue_counts,
    }


def _leading_value(frame: pd.DataFrame, value_column: str, label_column: str) -> str | None:
    if frame.empty:
        return None
    ranked = frame.sort_values([value_column, label_column], ascending=[False, True])
    return str(ranked.iloc[0][label_column])


def write_outputs(
    summaries: SalesSummaries,
    cleaning: CleaningResult,
    report: dict[str, Any],
    output_dir: Path,
) -> dict[str, Path]:
    """Write all pipeline artifacts to one output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "cleaned_orders": output_dir / "cleaned_orders.csv",
        "rejected_orders": output_dir / "rejected_orders.csv",
        "customer_summary": output_dir / "customer_summary.csv",
        "product_summary": output_dir / "product_summary.csv",
        "category_summary": output_dir / "category_summary.csv",
        "monthly_summary": output_dir / "monthly_summary.csv",
        "pipeline_summary": output_dir / "pipeline_summary.json",
    }
    summaries.orders.to_csv(outputs["cleaned_orders"], index=False, date_format="%Y-%m-%d")
    cleaning.rejected.to_csv(outputs["rejected_orders"], index=False, date_format="%Y-%m-%d")
    summaries.by_customer.to_csv(outputs["customer_summary"], index=False)
    summaries.by_product.to_csv(outputs["product_summary"], index=False)
    summaries.by_category.to_csv(outputs["category_summary"], index=False)
    summaries.by_month.to_csv(outputs["monthly_summary"], index=False)
    outputs["pipeline_summary"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return outputs
