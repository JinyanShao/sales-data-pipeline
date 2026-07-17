# Sales Data Processing Pipeline

A tested Python pipeline for validating, cleaning, transforming, and reporting sales data.

This repository models an internal data-processing task for a small retail or e-commerce business. It turns imperfect order exports into repeatable, auditable datasets and business summaries. The focus is automation, reliable data processing, business rules, and backend-adjacent engineering—not machine learning.

## What the pipeline does

The pipeline runs six explicit stages:

1. **Ingest** a CSV export while preserving business identifiers.
2. **Validate** the required schema before processing any records.
3. **Clean** whitespace and inconsistent status casing, and coerce dates and numeric fields.
4. **Quarantine** invalid records with one or more traceable rejection reasons.
5. **Transform** accepted orders and calculate gross and recognized revenue.
6. **Report** customer, product, category, and monthly summaries plus data-quality metrics.

Structural failures such as a missing input file or required column stop the run. Row-level issues do not silently disappear: affected records are written to `rejected_orders.csv` with a `rejection_reasons` field.

## Input contract

| Field | Meaning | Rule |
| --- | --- | --- |
| `order_id` | Unique order identifier | Required and unique |
| `order_date` | Order date | Must be parseable |
| `customer_id` | Customer identifier | Required |
| `product_id` | Product identifier | Required |
| `product_name` | Display name | Required; whitespace is trimmed |
| `category` | Product category | Required by the schema |
| `quantity` | Units ordered | Must be greater than zero |
| `unit_price` | Price per unit | Must be zero or greater |
| `country` | Customer/order country | Required by the schema |
| `status` | Order lifecycle state | `pending`, `completed`, `shipped`, or `cancelled` |

The sample input intentionally contains duplicate orders, a duplicate row, a missing customer ID, an invalid date, zero and negative quantities, a negative price, inconsistent status casing, padded product names, and an unsupported status.

## Business rules

- Status values are trimmed and normalized to lowercase.
- Product names and other text fields are trimmed.
- The first occurrence of an `order_id` is retained when it passes all other rules; later occurrences are quarantined.
- A rejected row may carry several semicolon-separated reasons.
- `gross_revenue = quantity × unit_price` for every valid order.
- `sales_revenue` equals gross revenue only when status is `completed` or `shipped`.
- Pending and cancelled orders remain available for operational analysis but contribute zero recognized revenue.

## Module responsibilities

- `ingestion.py` handles file existence, empty input, CSV parsing, encoding errors, and DataFrame loading.
- `validation.py` checks the schema, field types, identifiers, dates, quantities, prices, and statuses. It returns a `ValidationResult` containing record counts, issue counts, and row-level errors.
- `cleaning.py` trims strings, normalizes statuses, converts dates and numbers, and separates accepted records from rejected records without silently discarding failures.
- `transformation.py` calculates revenue and builds customer, product, category, and monthly summaries.
- `reporting.py` writes the processed datasets, summaries, and pipeline metrics.
- `pipeline.py` runs ingestion, validation, cleaning, transformation, and export in sequence.
- `cli.py` exposes the pipeline as a repeatable command-line job.

## Project structure

```text
sales-data-pipeline/
├── .github/workflows/ci.yml
├── data/
│   ├── raw/sales_orders.csv
│   └── processed/.gitkeep
├── reports/.gitkeep
├── src/sales_pipeline/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── exceptions.py
│   ├── ingestion.py
│   ├── validation.py
│   ├── cleaning.py
│   ├── transformation.py
│   ├── reporting.py
│   └── pipeline.py
├── tests/
├── .gitignore
├── LICENSE
├── README.md
└── pyproject.toml
```

## Run locally

Python 3.10 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
sales-pipeline data/raw/sales_orders.csv --output-dir reports
```

Custom paths can be supplied without changing source code:

```bash
sales-pipeline data/raw/sales_orders.csv \
  --output-dir reports \
  --log-level INFO
```

Add `--strict` to return exit status `2` when any records are rejected. Audit files are still written before strict-mode status is evaluated. File and schema failures return exit status `1`.

## Outputs

| Artifact | Purpose |
| --- | --- |
| `cleaned_orders.csv` | Normalized accepted orders with gross and recognized revenue |
| `rejected_orders.csv` | Quarantined records and rejection reasons |
| `customer_summary.csv` | Orders, units, gross revenue, and recognized revenue by customer |
| `product_summary.csv` | Orders, units, gross revenue, and recognized revenue by product |
| `category_summary.csv` | Orders, units, gross revenue, and recognized revenue by category |
| `monthly_summary.csv` | Orders, units, gross revenue, and recognized revenue by calendar month |
| `pipeline_summary.json` | Data-quality counts and business metrics for the run |

All artifacts are written beneath `--output-dir`. The JSON summary includes total, valid, and rejected order counts; gross and recognized revenue; average order value; unique customers; best-selling and highest-revenue products; highest-revenue customer; monthly revenue; order-status distribution; and validation issue counts.

Generated outputs are ignored by Git so repeated local and CI runs do not create repository noise.

## Tests and CI

```bash
pytest --cov=sales_pipeline --cov-report=term-missing
```

Tests cover ingestion failures, schema validation, multi-reason rejection, duplicate handling, business transformations, artifact generation, and an end-to-end run. GitHub Actions tests Python 3.10–3.12 and executes the pipeline against the sample dataset.

## Repository metadata

- **Repository name:** `sales-data-pipeline`
- **GitHub description:** A tested Python pipeline for validating, cleaning, transforming, and reporting sales data.

## License

MIT
