"""Durable CSV and JSON output generation."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from sales_pipeline.cleaning import CleaningResult
from sales_pipeline.transformation import SalesSummaries


def build_quality_report(
    source: Path,
    input_rows: int,
    cleaning: CleaningResult,
    summaries: SalesSummaries,
) -> dict[str, Any]:
    """Build a serializable run report with quality and business metrics."""
    return {
        "source": str(source),
        "input_rows": input_rows,
        "accepted_rows": len(cleaning.accepted),
        "rejected_rows": len(cleaning.rejected),
        "issue_counts": cleaning.issue_counts,
        "recognized_revenue": round(float(summaries.orders["order_revenue"].sum()), 2),
        "unique_customers": int(summaries.orders["customer_id"].nunique()),
        "unique_products": int(summaries.orders["product_id"].nunique()),
    }


def write_outputs(
    summaries: SalesSummaries,
    cleaning: CleaningResult,
    report: dict[str, Any],
    processed_dir: Path,
    reports_dir: Path,
) -> dict[str, Path]:
    """Write all pipeline artifacts and return their paths."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "cleaned_orders": processed_dir / "cleaned_orders.csv",
        "rejected_orders": processed_dir / "rejected_orders.csv",
        "customer_summary": reports_dir / "sales_by_customer.csv",
        "product_summary": reports_dir / "sales_by_product.csv",
        "monthly_summary": reports_dir / "sales_by_month.csv",
        "quality_report": reports_dir / "data_quality_report.json",
    }
    summaries.orders.to_csv(outputs["cleaned_orders"], index=False, date_format="%Y-%m-%d")
    cleaning.rejected.to_csv(outputs["rejected_orders"], index=False, date_format="%Y-%m-%d")
    summaries.by_customer.to_csv(outputs["customer_summary"], index=False)
    summaries.by_product.to_csv(outputs["product_summary"], index=False)
    summaries.by_month.to_csv(outputs["monthly_summary"], index=False)
    outputs["quality_report"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return outputs
