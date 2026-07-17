import json

import pytest

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.exceptions import ExportError
from sales_pipeline.reporting import build_pipeline_summary, write_outputs
from sales_pipeline.transformation import transform_orders
from sales_pipeline.validation import validate_orders


def build_report(source, validation, summaries):
    return build_pipeline_summary(
        source,
        validation,
        summaries,
        run_id="20260717T113000Z-a1b2c3",
        started_at="2026-07-17T11:30:00+00:00",
        completed_at="2026-07-17T11:30:00.420000+00:00",
        duration_seconds=0.42,
    )


def test_pipeline_summary_contains_quality_and_business_metrics(tmp_path, valid_orders):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_report(tmp_path / "source.csv", validation, summaries)
    assert report["run_id"] == "20260717T113000Z-a1b2c3"
    assert report["duration_seconds"] == 0.42
    assert report["total_orders"] == 2
    assert report["valid_orders"] == 2
    assert report["rejected_records"] == 0
    assert report["acceptance_rate"] == 1.0
    assert report["rejection_rate"] == 0.0
    assert report["gross_revenue"] == 70.0
    assert report["total_sales_revenue"] == 20.0
    assert report["recognized_revenue_rate"] == 0.2857
    assert report["average_order_value"] == 20.0
    assert report["best_selling_product"] == "Mouse"
    assert report["monthly_revenue"] == {"2026-01": 20.0, "2026-02": 0.0}
    assert report["order_status_distribution"] == {"completed": 1, "cancelled": 1}


def test_write_outputs_creates_named_artifacts(tmp_path, valid_orders):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_report(tmp_path / "source.csv", validation, summaries)
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


def test_write_outputs_wraps_filesystem_errors(tmp_path, valid_orders):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_report(tmp_path / "source.csv", validation, summaries)
    output_file = tmp_path / "occupied"
    output_file.write_text("not a directory", encoding="utf-8")
    with pytest.raises(ExportError, match="not a directory"):
        write_outputs(summaries, cleaning, report, output_file)


def test_write_outputs_preserves_previous_set_when_staging_fails(
    tmp_path, valid_orders, monkeypatch
):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_report(tmp_path / "source.csv", validation, summaries)
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    previous = output_dir / "pipeline_summary.json"
    previous.write_text('{"run_id": "previous"}\n', encoding="utf-8")

    def fail_staging(*args, **kwargs):
        raise OSError("simulated staging failure")

    monkeypatch.setattr("sales_pipeline.reporting._write_staged_outputs", fail_staging)
    with pytest.raises(ExportError, match="atomically"):
        write_outputs(summaries, cleaning, report, output_dir)

    assert json.loads(previous.read_text())["run_id"] == "previous"
    assert not list(tmp_path.glob(".reports.staging-*"))


def test_write_outputs_atomically_replaces_previous_set(tmp_path, valid_orders):
    validation = validate_orders(valid_orders)
    cleaning = clean_orders(valid_orders, validation)
    summaries = transform_orders(cleaning.accepted)
    report = build_report(tmp_path / "source.csv", validation, summaries)
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    (output_dir / ".gitkeep").touch()
    stale_file = output_dir / "stale-report.csv"
    stale_file.write_text("old", encoding="utf-8")

    outputs = write_outputs(summaries, cleaning, report, output_dir)

    assert all(path.exists() for path in outputs.values())
    assert (output_dir / ".gitkeep").exists()
    assert not stale_file.exists()
    assert not list(tmp_path.glob(".reports.backup-*"))
