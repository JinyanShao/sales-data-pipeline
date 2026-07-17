"""End-to-end orchestration for sales data processing."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.config import PipelineConfig
from sales_pipeline.ingestion import read_orders
from sales_pipeline.reconciliation import reconcile_summaries
from sales_pipeline.reporting import build_pipeline_summary, write_outputs
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_orders

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineResult:
    """Observable result of a completed pipeline run."""

    report: dict[str, Any]
    outputs: dict[str, Path]


def create_run_id(now: datetime | None = None) -> str:
    """Create a sortable identifier for one pipeline execution."""
    timestamp = now or datetime.now(timezone.utc)
    return f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:6]}"


def run_pipeline(
    config: PipelineConfig | None = None, base_dir: Path | None = None
) -> PipelineResult:
    """Run ingestion, validation, cleaning, transformation, and reporting."""
    settings = (config or PipelineConfig()).resolved(base_dir)
    run_id = settings.run_id or create_run_id()
    started_at = datetime.now(timezone.utc)
    started_clock = perf_counter()

    LOGGER.info("[run_id=%s] Reading sales orders from %s", run_id, settings.input_path)
    raw_orders = read_orders(settings.input_path)
    LOGGER.info("[run_id=%s] Loaded %s raw records", run_id, len(raw_orders))
    validation = validate_orders(raw_orders, settings.supported_statuses)
    LOGGER.info(
        "[run_id=%s] Detected %s duplicate rows",
        run_id,
        validation.issue_counts.get("duplicate_row", 0),
    )
    LOGGER.info("[run_id=%s] Validation rejected %s records", run_id, validation.invalid_records)
    cleaning = clean_orders(raw_orders, validation)
    summaries = transform_orders(cleaning.accepted, settings.revenue_statuses)
    reconcile_summaries(summaries)
    LOGGER.info("[run_id=%s] Reconciled order and summary totals", run_id)

    completed_at = datetime.now(timezone.utc)
    report = build_pipeline_summary(
        settings.input_path,
        validation,
        summaries,
        run_id=run_id,
        started_at=started_at.isoformat(),
        completed_at=completed_at.isoformat(),
        duration_seconds=perf_counter() - started_clock,
    )
    outputs = write_outputs(summaries, cleaning, report, settings.output_dir)
    for name, path in outputs.items():
        LOGGER.info("[run_id=%s] Wrote %s to %s", run_id, name, path)
    LOGGER.info("[run_id=%s] Wrote %s output artifacts", run_id, len(outputs))
    LOGGER.info("[run_id=%s] Pipeline processing completed successfully", run_id)
    return PipelineResult(report=report, outputs=outputs)
