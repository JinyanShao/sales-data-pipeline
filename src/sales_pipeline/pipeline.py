"""End-to-end orchestration for sales data processing."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.config import PipelineConfig
from sales_pipeline.ingestion import read_orders
from sales_pipeline.reporting import build_quality_report, write_outputs
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_schema


@dataclass(frozen=True)
class PipelineResult:
    """Observable result of a completed pipeline run."""

    report: dict[str, Any]
    outputs: dict[str, Path]


def run_pipeline(config: PipelineConfig | None = None, base_dir: Path | None = None) -> PipelineResult:
    """Run ingestion, validation, cleaning, transformation, and reporting."""
    settings = (config or PipelineConfig()).resolved(base_dir)
    raw_orders = read_orders(settings.input_path)
    validate_schema(raw_orders)
    cleaning = clean_orders(raw_orders, settings.supported_statuses)
    summaries = transform_orders(cleaning.accepted, settings.revenue_statuses)
    report = build_quality_report(settings.input_path, len(raw_orders), cleaning, summaries)
    outputs = write_outputs(summaries, cleaning, report, settings.processed_dir, settings.reports_dir)
    return PipelineResult(report=report, outputs=outputs)
