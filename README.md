# Sales Data Processing Pipeline

A tested Python pipeline that turns imperfect retail order CSV exports into validated, auditable sales reports.

## Overview

Sales Data Processing Pipeline is a data-processing tool designed to help small retail and e-commerce teams produce trustworthy operational reports from inconsistent order exports.

The project focuses on:

* CSV validation, cleaning, and rejection reporting
* Business-oriented sales transformations and summaries
* Reproducible reports with reconciliation checks
* Safe output replacement, logs, and automated quality gates

## Problem

Retail order exports often contain duplicate identifiers, missing customer information, malformed dates, invalid quantities, negative prices, and inconsistent order statuses. Using these records directly can overstate revenue and make customer, product, and monthly reporting unreliable.

Data-quality failures must be visible rather than silently discarded. A failed export must not leave consumers with a half-written report directory.

Typical challenges include:

* Invalid or incomplete CSV files
* Duplicate orders and inconsistent status values
* Incorrect revenue calculations caused by invalid records
* Partially written reports after an export failure

## Solution

The system addresses these challenges by providing:

* Schema and row-level validation with multiple rejection reasons per record
* Normalization and separation of accepted and rejected orders
* Revenue calculations and customer, product, category, and monthly summaries
* Atomic report replacement, reconciliation checks, logs, and strict quality gates

## Current Status

### Implemented

* CSV ingestion with missing-file, empty-file, encoding, and parser error handling
* Data-quality validation, normalization, rejected-record reports, and strict mode
* Gross and recognized revenue calculations using integer cents
* CSV and JSON output reports, automated tests, coverage enforcement, and CI

### In Progress

* Deployment and reproducibility documentation for the committed demonstration workflow

### Planned

* Configurable validation profiles for different export formats
* Optional chunked ingestion for larger datasets
* Configurable retention of previous report snapshots

Planned capabilities are not included in the current release unless explicitly marked as implemented.

## Architecture

```mermaid
flowchart LR
    CSV[Raw sales CSV] --> Ingestion[Ingestion]
    Ingestion --> Validation[Schema and row validation]
    Validation --> Cleaning[Cleaning and rejection]
    Cleaning --> Transform[Business transformations]
    Transform --> Reconcile[Reconciliation]
    Reconcile --> Reports[CSV and JSON reports]
```

### Main Components

| Component | Responsibility |
| --- | --- |
| CLI | Parses commands, configures logging, and returns defined exit codes |
| Validation | Applies schema and row-level business rules |
| Cleaning | Normalizes records and separates accepted and rejected orders |
| Transformation | Calculates revenue and business summaries |
| Reporting | Writes staged CSV/JSON artifacts and safely replaces output |

## Key Engineering Decisions

### Rejection reporting instead of silent data loss

**Decision:** Invalid rows are written to `rejected_orders.csv` with one or more explicit reasons.

**Reason:** Teams can inspect and correct data-quality issues without losing visibility into failed records.

**Trade-off:** Downstream users need to review a separate rejected-record artifact.

### Atomic output-directory replacement

**Decision:** Reports are written to a staging directory before replacing the previous complete output directory.

**Reason:** A failed export leaves the prior complete report set intact.

**Trade-off:** The tool does not coordinate with external readers that keep old file handles open.

## Technology Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.10+ |
| Framework | None; command-line application |
| Data processing | pandas |
| Testing | pytest, pytest-cov, Coverage |
| Packaging | Python package managed with uv |
| CI/CD | GitHub Actions, Ruff |

## Repository Structure

```text
.
├── src/sales_pipeline/  # CLI, validation, cleaning, transformation, reporting
├── tests/               # Automated tests
├── data/raw/            # Synthetic sample input
├── docs/                # Deployment and demonstration documentation
├── scripts/             # Demo verification script
├── .github/workflows/   # Continuous integration
└── README.md
```

## Getting Started

### Prerequisites

* Python 3.10+
* [uv](https://docs.astral.sh/uv/getting-started/installation/)
* Git

### Installation

```bash
git clone https://github.com/JinyanShao/sales-data-pipeline.git
cd sales-data-pipeline
uv sync --all-extras --locked
```

### Configuration

No credentials or environment file are required. Input and output paths are passed directly to the command.

### Run Locally

```bash
uv run sales-pipeline data/raw/sales_orders.csv --output-dir reports
```

## Testing

Run the complete automated test suite:

```bash
uv run pytest --cov=sales_pipeline --cov-report=term-missing --cov-fail-under=85
```

Run quality checks:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python scripts/verify_demo.py
```

## Example Workflow

1. An operations user supplies a retail order CSV export.
2. The pipeline validates each record and records invalid rows with explicit reasons.
3. Accepted records are normalized and transformed into revenue metrics.
4. Reconciliation verifies counts and money totals before reports are published.
5. The pipeline writes cleaned orders, rejected records, summary CSVs, and a JSON run report.

Run with a data-quality gate:

```bash
uv run sales-pipeline data/raw/sales_orders.csv --output-dir reports --strict --log-level INFO
```

## Reliability and Safety

The project includes the following reliability measures where applicable:

* Schema and field-level validation
* Explicit error handling and defined exit codes
* Automated unit and end-to-end tests
* Exact money calculations using integer cents
* Atomic output replacement and reconciliation checks
* Structured logs, run metadata, and no committed credentials

## Limitations

The current version does not yet include:

* Multiple source formats in one run
* Chunked processing for large files
* Refunds, taxes, discounts, currencies, or partial-fulfilment models

These limitations are documented intentionally to distinguish implemented functionality from future work.

## Roadmap

* [ ] Add configurable validation profiles for different sales-export formats
* [ ] Add optional chunked ingestion for larger CSV files
* [ ] Add configurable retention for previous report snapshots

## Documentation

Additional documentation is available in the `docs/` directory:

* Deployment and operational instructions
* Synthetic demo input and reproducible verification

## Licence

This project is licensed under the MIT License. See `LICENSE` for details.

## Author

Jinyan Shao<br>
Software Engineer — Business Applications, Backend and Automation

* Website: [https://jinyanshao.ch](https://jinyanshao.ch/)
* GitHub: [https://github.com/JinyanShao](https://github.com/JinyanShao)
* LinkedIn: [https://www.linkedin.com/in/jinyanshao/](https://www.linkedin.com/in/jinyanshao/)
