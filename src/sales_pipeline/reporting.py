"""Atomic CSV and JSON report generation."""

import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from sales_pipeline.cleaning import CleaningResult
from sales_pipeline.exceptions import ExportError
from sales_pipeline.transformation import SalesSummaries
from sales_pipeline.validation import ValidationResult

MONEY_INTERNAL_COLUMNS = [
    "unit_price_cents",
    "gross_revenue_cents",
    "sales_revenue_cents",
    "revenue_cents",
]


def build_pipeline_summary(
    source: Path,
    validation: ValidationResult,
    summaries: SalesSummaries,
    *,
    run_id: str,
    started_at: str,
    completed_at: str,
    duration_seconds: float,
) -> dict[str, Any]:
    """Build run metadata, data-quality rates, and business metrics."""
    orders = summaries.orders
    sales_order_count = int(orders["sales_revenue_cents"].gt(0).sum())
    gross_revenue_cents = int(orders["gross_revenue_cents"].sum())
    sales_revenue_cents = int(orders["sales_revenue_cents"].sum())
    total_orders = validation.total_records
    return {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": round(duration_seconds, 3),
        "source": str(source),
        "total_orders": total_orders,
        "valid_orders": validation.valid_records,
        "rejected_records": validation.invalid_records,
        "acceptance_rate": round(validation.valid_records / total_orders, 4),
        "rejection_rate": round(validation.invalid_records / total_orders, 4),
        "gross_revenue": gross_revenue_cents / 100,
        "total_sales_revenue": sales_revenue_cents / 100,
        "recognized_revenue_rate": round(sales_revenue_cents / gross_revenue_cents, 4)
        if gross_revenue_cents
        else 0.0,
        "average_order_value": round(sales_revenue_cents / sales_order_count) / 100
        if sales_order_count
        else 0.0,
        "unique_customers": int(orders["customer_id"].nunique()),
        "best_selling_product": _leading_value(
            summaries.by_product, "units_ordered", "product_name"
        ),
        "highest_revenue_product": _leading_value(
            summaries.by_product, "revenue_cents", "product_name"
        ),
        "highest_revenue_customer": _leading_value(
            summaries.by_customer, "revenue_cents", "customer_id"
        ),
        "monthly_revenue": {
            str(month): int(revenue_cents) / 100
            for month, revenue_cents in zip(
                summaries.by_month["order_month"],
                summaries.by_month["revenue_cents"],
                strict=True,
            )
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
    """Stage every artifact and replace the previous complete output set."""
    output_dir = Path(output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        raise ExportError(f"Output path is not a directory: {output_dir}")

    run_id = str(report["run_id"])
    staging_dir = output_dir.parent / f".{output_dir.name}.staging-{run_id}"
    backup_dir = output_dir.parent / f".{output_dir.name}.backup-{run_id}"
    staged_outputs = _output_paths(staging_dir)
    final_outputs = _output_paths(output_dir)
    try:
        output_dir.parent.mkdir(parents=True, exist_ok=True)
        staging_dir.mkdir()
        if (output_dir / ".gitkeep").exists():
            (staging_dir / ".gitkeep").touch()
        _write_staged_outputs(staged_outputs, summaries, cleaning, report)
        if output_dir.exists():
            output_dir.rename(backup_dir)
        try:
            staging_dir.rename(output_dir)
        except OSError:
            if backup_dir.exists():
                backup_dir.rename(output_dir)
            raise
        if backup_dir.exists():
            shutil.rmtree(backup_dir, ignore_errors=True)
    except Exception as exc:
        shutil.rmtree(staging_dir, ignore_errors=True)
        if backup_dir.exists() and not output_dir.exists():
            try:
                backup_dir.rename(output_dir)
            except OSError:
                pass
        raise ExportError(f"Could not atomically write outputs to {output_dir}: {exc}") from exc
    return final_outputs


def _output_paths(directory: Path) -> dict[str, Path]:
    return {
        "cleaned_orders": directory / "cleaned_orders.csv",
        "rejected_orders": directory / "rejected_orders.csv",
        "customer_summary": directory / "customer_summary.csv",
        "product_summary": directory / "product_summary.csv",
        "category_summary": directory / "category_summary.csv",
        "monthly_summary": directory / "monthly_summary.csv",
        "pipeline_summary": directory / "pipeline_summary.json",
    }


def _write_staged_outputs(
    outputs: dict[str, Path],
    summaries: SalesSummaries,
    cleaning: CleaningResult,
    report: dict[str, Any],
) -> None:
    _for_export(summaries.orders).to_csv(
        outputs["cleaned_orders"], index=False, date_format="%Y-%m-%d"
    )
    cleaning.rejected.to_csv(outputs["rejected_orders"], index=False, date_format="%Y-%m-%d")
    _for_export(summaries.by_customer).to_csv(outputs["customer_summary"], index=False)
    _for_export(summaries.by_product).to_csv(outputs["product_summary"], index=False)
    _for_export(summaries.by_category).to_csv(outputs["category_summary"], index=False)
    _for_export(summaries.by_month).to_csv(outputs["monthly_summary"], index=False)
    outputs["pipeline_summary"].write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def _for_export(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop(columns=MONEY_INTERNAL_COLUMNS, errors="ignore")
