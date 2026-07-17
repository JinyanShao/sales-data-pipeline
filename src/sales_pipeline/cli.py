"""Command-line interface for the sales pipeline."""

import argparse
import json
import sys
from pathlib import Path

from sales_pipeline.config import PipelineConfig
from sales_pipeline.exceptions import PipelineError
from sales_pipeline.pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate, clean, transform, and report sales orders.")
    parser.add_argument("--input", type=Path, default=Path("data/raw/sales_orders.csv"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = PipelineConfig(
        input_path=args.input,
        processed_dir=args.processed_dir,
        reports_dir=args.reports_dir,
    )
    try:
        result = run_pipeline(config)
    except PipelineError as exc:
        print(f"Pipeline failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result.report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
