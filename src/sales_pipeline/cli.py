"""Command-line interface for the sales pipeline."""

import argparse
import logging
from pathlib import Path

from sales_pipeline.config import PipelineConfig
from sales_pipeline.exceptions import (
    ExportError,
    InputFileError,
    ReconciliationError,
    SchemaValidationError,
)
from sales_pipeline.pipeline import create_run_id, run_pipeline

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate, clean, transform, and report sales orders."
    )
    parser.add_argument("input_file", type=Path, help="CSV file containing sales orders")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--strict", action="store_true", help="Fail when records are rejected")
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s %(message)s",
        force=True,
    )
    run_id = create_run_id()
    try:
        result = run_pipeline(
            PipelineConfig(input_path=args.input_file, output_dir=args.output_dir, run_id=run_id)
        )
    except ExportError as exc:
        LOGGER.error("[run_id=%s] Pipeline output failed: %s", run_id, exc)
        return 3
    except (InputFileError, SchemaValidationError) as exc:
        LOGGER.error("[run_id=%s] Pipeline input failed: %s", run_id, exc)
        return 2
    except ReconciliationError as exc:
        LOGGER.error("[run_id=%s] Pipeline reconciliation failed: %s", run_id, exc)
        return 1

    if args.strict and result.report["rejected_records"]:
        LOGGER.error(
            "[run_id=%s] Pipeline failed data quality checks with %s rejected records",
            run_id,
            result.report["rejected_records"],
        )
        return 1
    LOGGER.info("[run_id=%s] Pipeline completed successfully", run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
