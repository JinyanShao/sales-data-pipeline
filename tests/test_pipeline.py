import json

from sales_pipeline.config import PipelineConfig
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
