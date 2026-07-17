# Sales Data Processing Pipeline

A tested Python pipeline for validating, cleaning, transforming, and reporting sales data.

This repository models an internal data-processing task for a small retail or e-commerce business. It turns imperfect order exports into repeatable, auditable datasets and business summaries. The focus is automation, reliable data processing, business rules, and backend-adjacent engineering—not machine learning.

## What the pipeline does

The pipeline runs six explicit stages:

1. **Ingest** a CSV export while preserving business identifiers.
2. **Validate** the required schema before processing any records.
3. **Clean** whitespace and inconsistent status casing, and coerce dates and numeric fields.
4. **Quarantine** invalid records with one or more traceable rejection reasons.
5. **Transform** accepted orders and recognize revenue for completed and shipped orders.
6. **Report** customer, product, and monthly sales summaries plus data-quality metrics.

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
- The first valid occurrence of an `order_id` is retained; later occurrences are quarantined.
- A rejected row may carry several semicolon-separated reasons.
- `order_revenue = quantity × unit_price` only when status is `completed` or `shipped`.
- Pending and cancelled orders remain available for operational analysis but contribute zero recognized revenue.

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
sales-pipeline
```

Custom paths can be supplied without changing source code:

```bash
sales-pipeline \
  --input data/raw/sales_orders.csv \
  --processed-dir data/processed \
  --reports-dir reports
```

The command prints the run summary as JSON and returns a non-zero exit code for expected ingestion or schema failures.

## Outputs

| Artifact | Purpose |
| --- | --- |
| `data/processed/cleaned_orders.csv` | Normalized accepted orders with recognized revenue |
| `data/processed/rejected_orders.csv` | Quarantined records and rejection reasons |
| `reports/sales_by_customer.csv` | Orders, units, and revenue by customer |
| `reports/sales_by_product.csv` | Orders, units, and revenue by product |
| `reports/sales_by_month.csv` | Orders, units, and revenue by calendar month |
| `reports/data_quality_report.json` | Input, acceptance, rejection, issue, and business metrics |

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
