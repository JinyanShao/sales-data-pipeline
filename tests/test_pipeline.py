import json

import pytest

from sales_pipeline.config import PipelineConfig
from sales_pipeline.exceptions import ReconciliationError
from sales_pipeline.pipeline import run_pipeline


def test_run_pipeline_end_to_end(tmp_path, valid_orders):
    source = tmp_path / "raw" / "orders.csv"
    source.parent.mkdir()
    valid_orders.to_csv(source, index=False)
    config = PipelineConfig(input_path=source, output_dir=tmp_path / "reports")
    result = run_pipeline(config)
    assert result.report["total_orders"] == 2
    assert result.report["valid_orders"] == 2
    assert result.report["total_sales_revenue"] == 20.0
    assert json.loads(result.outputs["pipeline_summary"].read_text())["unique_customers"] == 2


def test_run_pipeline_logs_processing_counts_and_outputs(tmp_path, valid_orders, caplog):
    source = tmp_path / "orders.csv"
    valid_orders.to_csv(source, index=False)
    run_id = "20260717T113000Z-a1b2c3"
    with caplog.at_level("INFO", logger="sales_pipeline.pipeline"):
        run_pipeline(
            PipelineConfig(
                input_path=source,
                output_dir=tmp_path / "reports",
                run_id=run_id,
            )
        )
    assert "Loaded 2 raw records" in caplog.text
    assert "Detected 0 duplicate rows" in caplog.text
    assert "Validation rejected 0 records" in caplog.text
    assert "Wrote pipeline_summary" in caplog.text
    assert "processing completed successfully" in caplog.text
    assert all(f"[run_id={run_id}]" in record.message for record in caplog.records)


def test_run_pipeline_exports_reports_when_every_record_is_rejected(tmp_path, valid_orders):
    source = tmp_path / "orders.csv"
    invalid = valid_orders.iloc[[0]].copy()
    invalid.loc[:, "quantity"] = 0
    invalid.to_csv(source, index=False)
    result = run_pipeline(PipelineConfig(input_path=source, output_dir=tmp_path / "reports"))
    assert result.report["valid_orders"] == 0
    assert result.report["rejected_records"] == 1
    assert result.report["best_selling_product"] is None
    assert result.outputs["monthly_summary"].exists()


def test_run_pipeline_stops_before_export_when_reconciliation_fails(
    tmp_path, valid_orders, monkeypatch
):
    source = tmp_path / "orders.csv"
    valid_orders.to_csv(source, index=False)
    export_called = False

    def fail_reconciliation(*args, **kwargs):
        raise ReconciliationError("summary mismatch")

    def track_export(*args, **kwargs):
        nonlocal export_called
        export_called = True

    monkeypatch.setattr("sales_pipeline.pipeline.reconcile_summaries", fail_reconciliation)
    monkeypatch.setattr("sales_pipeline.pipeline.write_outputs", track_export)
    with pytest.raises(ReconciliationError, match="summary mismatch"):
        run_pipeline(PipelineConfig(input_path=source, output_dir=tmp_path / "reports"))
    assert export_called is False
