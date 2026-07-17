# Sales Data Processing Pipeline

[![CI](https://github.com/JinyanShao/sales-data-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/JinyanShao/sales-data-pipeline/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB)
![Coverage 85% minimum](https://img.shields.io/badge/coverage-85%25%20minimum-success)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A tested Python pipeline for validating, cleaning, transforming, and reporting sales data.

## 1. Project Positioning

This repository is a small internal data-processing system that demonstrates Python automation, data quality engineering, and business-oriented transformation logic. It is designed around a single retail sales workflow and produces repeatable, auditable outputs from imperfect order exports.

## 2. Business Problem

Small retail and e-commerce teams often receive order data as CSV exports. These files can contain duplicate identifiers, missing customer information, malformed dates, invalid quantities, negative prices, inconsistent status values, and untidy product names. Using that data directly can overstate revenue, distort customer and product rankings, and make operational reports difficult to trust.

This pipeline applies explicit quality rules before calculating business metrics. Invalid rows remain traceable in a rejected-record dataset, while accepted rows feed standardized customer, product, category, and monthly reports.

## 3. Pipeline Overview

```text
Raw CSV
  ↓
Schema and Row Validation
  ↓
Cleaning and Rejection
  ↓
Business Transformations
  ↓
CSV and JSON Reports
```

Structural problems, such as missing columns, stop the run. Row-level problems are collected in a `ValidationResult` and then isolated by the cleaning stage. The transformation stage only receives accepted records.

## 4. Features

- CSV ingestion with missing-file, empty-file, encoding, and parser error handling
- Required-column and field-value validation
- Multiple rejection reasons on a single record
- String trimming and order-status normalization
- Gross and recognized sales revenue calculations
- Integer-cent monetary calculations with exact summary reconciliation
- Customer, product, category, and monthly aggregations
- Atomic output replacement that preserves the previous complete report set on failure
- Run identifiers, timestamps, durations, and machine-readable quality rates
- Operational logs for inputs, record counts, quality results, outputs, and final status
- Strict mode for automated data-quality gates
- Defined exit codes for quality, input, configuration, and export failures
- Automated linting, formatting, tests, and coverage enforcement

## 5. Architecture

```text
src/sales_pipeline/
├── cli.py             Command parsing, logging setup, and exit codes
├── config.py          Paths and business-rule configuration
├── exceptions.py      Pipeline-specific exception hierarchy
├── ingestion.py       CSV loading and input-file checks
├── validation.py      Schema rules, row rules, and ValidationResult
├── cleaning.py        Normalization and accepted/rejected separation
├── transformation.py Revenue calculations and business summaries
├── reporting.py       CSV and JSON exports
├── reconciliation.py  Cross-table count, unit, and revenue checks
└── pipeline.py        End-to-end stage orchestration
```

The package keeps input handling, rule evaluation, normalization, business logic, and file export separate. This makes each stage independently testable and keeps orchestration in one place.

## 6. Data Validation Rules

| Data issue | Processing rule |
| --- | --- |
| Duplicate `order_id` | Keep the first occurrence when otherwise valid; send later occurrences to `rejected_orders.csv` |
| Completely duplicate row | Keep the first occurrence; reject later copies and report the duplicate count |
| Missing `order_id` | Send the record to `rejected_orders.csv` |
| Missing `customer_id` | Send the record to `rejected_orders.csv` |
| Missing product ID, name, category, or country | Send the record to `rejected_orders.csv` |
| Invalid order date | Send the record to `rejected_orders.csv` |
| Non-integer quantity | Send the record to `rejected_orders.csv` |
| `quantity <= 0` | Send the record to `rejected_orders.csv` |
| Non-numeric unit price | Send the record to `rejected_orders.csv` |
| `unit_price < 0` | Send the record to `rejected_orders.csv`; zero is accepted |
| Product-name whitespace | Trim leading and trailing whitespace automatically |
| Inconsistent status casing | Trim and normalize the value to lowercase |
| Unknown status | Send the record to `rejected_orders.csv`; strict mode returns exit code `1` |

A rejected row may contain several semicolon-separated reasons. Exceptions are never silently discarded.

## 7. Input Schema

| Field | Type after cleaning | Rule |
| --- | --- | --- |
| `order_id` | string | Required and unique |
| `order_date` | date | Required and parseable |
| `customer_id` | string | Required |
| `product_id` | string | Required |
| `product_name` | string | Required; surrounding whitespace is removed |
| `category` | string | Required |
| `quantity` | integer | Greater than zero |
| `unit_price` | decimal | Zero or greater |
| `country` | string | Required |
| `status` | string | `pending`, `completed`, `shipped`, or `cancelled` |

The committed sample file at `data/raw/sales_orders.csv` deliberately includes a small number of realistic quality problems so every rejection path can be inspected.

## 8. Installation

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

The editable development installation provides the `sales-pipeline` command and installs the test, coverage, lint, and formatting tools.

## 9. CLI Usage

Run the sample dataset:

```bash
sales-pipeline data/raw/sales_orders.csv --output-dir reports
```

Example log output:

```text
INFO [run_id=20260717T113000Z-a1b2c3] Loaded 15 raw records
INFO [run_id=20260717T113000Z-a1b2c3] Validation rejected 8 records
INFO [run_id=20260717T113000Z-a1b2c3] Wrote 7 output artifacts
INFO [run_id=20260717T113000Z-a1b2c3] Pipeline completed successfully
```

Run with a quality gate and explicit log level:

```bash
sales-pipeline data/raw/sales_orders.csv \
  --output-dir reports \
  --strict \
  --log-level INFO
```

Strict mode writes the audit artifacts before evaluating the quality result.

| Exit code | Meaning |
| --- | --- |
| `0` | Pipeline completed successfully |
| `1` | Strict-mode data-quality failure |
| `2` | Input, schema, or command configuration error |
| `3` | Output export failure |

## 10. Output Files

All files are written beneath `--output-dir`.

| File | Contents |
| --- | --- |
| `cleaned_orders.csv` | Accepted orders with normalized fields, gross revenue, and recognized sales revenue |
| `rejected_orders.csv` | Invalid records with semicolon-separated rejection reasons |
| `customer_summary.csv` | Orders, units, gross revenue, and sales revenue by customer |
| `product_summary.csv` | Orders, units, gross revenue, and sales revenue by product |
| `category_summary.csv` | Orders, units, gross revenue, and sales revenue by category |
| `monthly_summary.csv` | Orders, units, gross revenue, and sales revenue by month |
| `pipeline_summary.json` | Run metadata, quality rates, data-quality counts, and business metrics |

Artifacts are first written to an isolated staging directory. After every write succeeds, the complete staged directory replaces the previous output directory. A failed write removes staging data and leaves the previous complete output set unchanged. Generated outputs are ignored by version control and can be reproduced from the committed raw input.

## 11. Example Results

Running the pipeline against the sample file produces:

| Metric | Result |
| --- | ---: |
| Total input records | 15 |
| Valid orders | 7 |
| Rejected records | 8 |
| Acceptance rate | 46.67% |
| Rejection rate | 53.33% |
| Gross revenue | 475.28 |
| Recognized sales revenue | 337.28 |
| Recognized revenue rate | 70.96% |
| Average recognized order value | 67.46 |
| Unique customers | 5 |
| Best-selling product | Notebook Set |
| Highest-revenue product | USB-C Hub |
| Highest-revenue customer | CUST-002 |

Recognized monthly revenue is 129.48 for January, 36.75 for February, and 171.05 for March 2026. The JSON report also records the order-status distribution and counts for every validation issue.

## 12. Testing

Tests use fixtures and pytest's `tmp_path`; they never depend on the repository's real output directories.

```bash
ruff check src tests
ruff format --check src tests
pytest --cov=sales_pipeline --cov-report=term-missing --cov-fail-under=85
```

The suite covers missing and empty files, header-only CSV files, missing columns, duplicate orders, invalid dates, missing customers, quantity and price boundaries, status normalization, exact monetary calculations, cross-table reconciliation, atomic export rollback, customer and product summaries, rejected records, complete pipeline runs, run metadata, logging, and CLI exit codes.

Continuous integration runs these checks on Ubuntu with Python 3.10 and 3.12.

## 13. Technology

- Python 3.10+
- pandas for tabular processing and aggregation
- Integer cents and decimal boundary conversion for monetary accuracy
- pytest for behavior and integration tests
- pytest-cov and coverage.py for coverage enforcement
- Ruff for linting and formatting
- GitHub Actions for continuous integration
- Standard-library `argparse`, `logging`, `json`, `pathlib`, and `dataclasses`

## 14. Limitations

- Input is limited to one CSV file per run.
- Processing is in memory and is intended for small internal retail exports.
- Revenue recognition is based only on order status and does not model refunds, taxes, discounts, currencies, or partial fulfillment.
- Duplicate handling keeps the first occurrence by file order; it does not compare update timestamps.
- Output replacement is atomic at the directory-switch level but does not coordinate with external readers that cache open file handles.

## 15. Roadmap

- Add configurable validation profiles for different sales-export formats.
- Add optional chunked ingestion for larger CSV files.
- Add configurable retention for previous report snapshots.

The repository will remain focused on one sales-processing workflow. Unrelated datasets and analysis projects are intentionally kept separate.

## 16. License

This project is available under the MIT License. See `LICENSE` for the full terms.
