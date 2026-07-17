"""End-to-end orchestration for sales data processing."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.config import PipelineConfig
from sales_pipeline.ingestion import read_orders
from sales_pipeline.reporting import build_pipeline_summary, write_outputs
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_orders

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    """Observable result of a completed pipeline run."""

    report: dict[str, Any]
    outputs: dict[str, Path]


def run_pipeline(
    config: PipelineConfig | None = None, base_dir: Path | None = None
) -> PipelineResult:
    """Run ingestion, validation, cleaning, transformation, and reporting."""
    settings = (config or PipelineConfig()).resolved(base_dir)
    LOGGER.info("Reading sales orders from %s", settings.input_path)
    raw_orders = read_orders(settings.input_path)
    LOGGER.info("Loaded %s raw records", len(raw_orders))
    validation = validate_orders(raw_orders, settings.supported_statuses)
    LOGGER.info("Detected %s duplicate rows", validation.issue_counts.get("duplicate_row", 0))
    LOGGER.info("Validation rejected %s records", validation.invalid_records)
    cleaning = clean_orders(raw_orders, validation)
    summaries = transform_orders(cleaning.accepted, settings.revenue_statuses)
    report = build_pipeline_summary(settings.input_path, validation, summaries)
    outputs = write_outputs(summaries, cleaning, report, settings.output_dir)
    for name, path in outputs.items():
        LOGGER.info("Wrote %s to %s", name, path)
    LOGGER.info("Pipeline processing completed successfully")
    return PipelineResult(report=report, outputs=outputs)
