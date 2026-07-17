"""Command-line interface for the sales pipeline."""

import argparse
import json
import logging
from pathlib import Path

from sales_pipeline.config import PipelineConfig
from sales_pipeline.exceptions import PipelineError
from sales_pipeline.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate, clean, transform, and report sales orders.")
    parser.add_argument("input_file", type=Path, help="CSV file containing sales orders")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--strict", action="store_true", help="Return a non-zero status when records are rejected")
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(message)s", force=True)
    try:
        result = run_pipeline(
            PipelineConfig(input_path=args.input_file, output_dir=args.output_dir)
        )
    except PipelineError as exc:
        logging.error("Pipeline failed: %s", exc)
        return 1

    print(json.dumps(result.report, indent=2))
    if args.strict and result.report["rejected_records"]:
        logging.error("Strict validation failed with %s rejected records", result.report["rejected_records"])
        return 2
    logging.info("Pipeline completed; outputs written to %s", args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
