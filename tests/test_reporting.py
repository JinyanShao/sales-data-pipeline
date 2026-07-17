import json

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.reporting import build_pipeline_summary, write_outputs
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_orders


def test_pipeline_summary_contains_quality_and_business_metrics(tmp_path, valid_orders):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_pipeline_summary(tmp_path / "source.csv", validation, summaries)
    assert report["total_orders"] == 2
    assert report["valid_orders"] == 2
    assert report["rejected_records"] == 0
    assert report["gross_revenue"] == 70.0
    assert report["total_sales_revenue"] == 20.0
    assert report["average_order_value"] == 20.0
    assert report["best_selling_product"] == "Mouse"
    assert report["monthly_revenue"] == {"2026-01": 20.0, "2026-02": 0.0}
    assert report["order_status_distribution"] == {"completed": 1, "cancelled": 1}


def test_write_outputs_creates_named_artifacts(tmp_path, valid_orders):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_pipeline_summary(tmp_path / "source.csv", validation, summaries)
    outputs = write_outputs(summaries, cleaning, report, tmp_path / "reports")
    assert set(path.name for path in outputs.values()) == {
        "cleaned_orders.csv",
        "rejected_orders.csv",
        "customer_summary.csv",
        "product_summary.csv",
        "category_summary.csv",
        "monthly_summary.csv",
        "pipeline_summary.json",
    }
    assert all(path.exists() for path in outputs.values())
    assert json.loads(outputs["pipeline_summary"].read_text())["unique_customers"] == 2
