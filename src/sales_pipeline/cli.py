"""Command-line interface for the sales pipeline."""

import argparse
import logging
from pathlib import Path

from sales_pipeline.config import PipelineConfig
from sales_pipeline.exceptions import ExportError, InputFileError, SchemaValidationError
from sales_pipeline.pipeline import run_pipeline

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
    try:
        result = run_pipeline(
            PipelineConfig(input_path=args.input_file, output_dir=args.output_dir)
        )
    except ExportError as exc:
        LOGGER.error("Pipeline output failed: %s", exc)
        return 3
    except (InputFileError, SchemaValidationError) as exc:
        LOGGER.error("Pipeline input failed: %s", exc)
        return 2

    if args.strict and result.report["rejected_records"]:
        LOGGER.error(
            "Pipeline failed data quality checks with %s rejected records",
            result.report["rejected_records"],
        )
        return 1
    LOGGER.info("Pipeline completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
