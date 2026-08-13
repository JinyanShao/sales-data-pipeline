# Sales Data Pipeline

A runnable Python pipeline that reads recurring sales order CSV files and writes cleaned orders, rejected rows, revenue summaries, and a JSON pipeline summary.

## Pipeline at a glance

```text
Raw files
  ↓
Validation
  ↓
Normalization
  ↓
Transformation
  ↓
Aggregation
  ↓
Reports
```

The current pipeline is intentionally small: one CSV in, one report directory out. It is built to make data-quality decisions visible instead of hiding them inside a spreadsheet or a notebook.

## Input data

The pipeline currently supports UTF-8 CSV files with sales-order rows.

The sample input lives at `data/raw/sales_orders.csv`. Each row is expected to describe one order line with fields such as:

```text
order_id, order_date, customer_id, product_id, product_name, category,
quantity, unit_price, country, status
```

The pipeline assumes:

* `order_id` identifies an order record.
* `quantity` and `unit_price` are used to calculate revenue.
* `status` controls recognized revenue: completed and shipped orders count as revenue; pending and cancelled orders stay visible but are not recognized as sales revenue.
* Input files can contain imperfect operational data: missing values, inconsistent status casing, duplicate IDs, invalid dates, and bad numeric values.

## Pipeline stages

### 1. Ingestion

Reads the source CSV and turns file, encoding, empty-file, and parser failures into explicit pipeline errors.

### 2. Validation

Checks required columns and row-level rules before any business metrics are calculated.

### 3. Transformation

Normalizes accepted rows, including trimmed text, parsed dates, lower-case statuses, and integer-cent revenue calculations.

### 4. Aggregation

Builds customer, product, category, and monthly summaries from accepted rows only.

### 5. Reporting

Writes all CSV and JSON outputs to a staging directory, reconciles totals, then replaces the target report directory as a complete set.

## Example run

Install dependencies with the locked environment:

```bash
uv sync --all-extras --locked
```

Run the sample pipeline:

```bash
uv run sales-pipeline data/raw/sales_orders.csv --output-dir reports
```

Run with a stricter quality gate:

```bash
uv run sales-pipeline data/raw/sales_orders.csv --output-dir reports --strict --max-rejection-rate 0.2
```

## Example output

The sample input contains 15 rows. The current demo accepts 7 rows and rejects 8 rows.

Generated files:

```text
reports/
├── cleaned_orders.csv
├── rejected_orders.csv
├── customer_summary.csv
├── product_summary.csv
├── category_summary.csv
├── monthly_summary.csv
└── pipeline_summary.json
```

Small excerpt from `monthly_summary.csv`:

```csv
order_month,order_count,units_ordered,gross_revenue,revenue
2026-01,3,4,171.48,129.48
2026-02,1,3,36.75,36.75
2026-03,3,9,267.05,171.05
```

Small excerpt from `pipeline_summary.json`:

```json
{
  "total_orders": 15,
  "valid_orders": 7,
  "rejected_records": 8,
  "gross_revenue": 475.28,
  "total_sales_revenue": 337.28
}
```

## Data quality rules

Invalid rows are written to `rejected_orders.csv` with one or more reasons. They are not used for revenue or summary reports.

Current checks include:

* missing required columns
* missing `order_id`, `order_date`, `customer_id`, `product_id`, `product_name`, or `status`
* invalid `order_date`
* non-positive `quantity`
* negative `unit_price`
* unsupported `status`
* duplicate rows
* duplicate `order_id`

Duplicate order handling is deliberately conservative: the first otherwise-valid row for an `order_id` is kept, and later valid rows with the same `order_id` are rejected. If an earlier row is already invalid, it does not block a later valid row with the same ID.

## Project layout

```text
.
├── src/sales_pipeline/
│   ├── ingestion.py
│   ├── validation.py
│   ├── cleaning.py
│   ├── transformation.py
│   ├── reconciliation.py
│   ├── reporting.py
│   ├── pipeline.py
│   └── cli.py
├── tests/
├── data/raw/
├── reports/
├── docs/
├── scripts/
├── pyproject.toml
├── uv.lock
└── README.md
```

## Tests and CI

Run the test suite:

```bash
uv run pytest --cov=sales_pipeline --cov-report=term-missing --cov-fail-under=85
```

Run the same style checks used in CI:

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run python scripts/verify_demo.py
```

The tests cover ingestion errors, validation and rejection reasons, cleaning behavior, revenue transformation, reconciliation, reporting, CLI exit codes, and the end-to-end demo output.

GitHub Actions installs dependencies from `uv.lock`, runs Ruff, runs pytest with coverage, and verifies the sample pipeline command.

## Design choices

* The pipeline is split into stages so each data decision has a narrow place to live.
* Validation and transformation are separate because bad rows should be rejected before revenue is calculated.
* Rejected rows are kept as an output artifact so data-quality failures can be reviewed instead of disappearing.
* Money is calculated with integer cents internally to avoid floating-point drift in report totals.
* Reports are written as a complete directory set so a failed run does not leave a partially updated output.

## Known limitations

The project currently handles a single CSV input per run. It does not yet support multiple source formats, incremental loading, chunked processing, currency conversion, taxes, discounts, refunds, or partial fulfilment.

This is a batch command-line pipeline, not a scheduler or dashboard. Those pieces are intentionally outside the current scope.

## Documentation

Additional notes are available in `docs/`:

* `docs/DEPLOYMENT.md` explains local setup and operational use.
* `docs/DEMO.md` describes the reproducible sample run.

## Licence

This project is licensed under the MIT License. See `LICENSE` for details.
