import json

from sales_pipeline.config import PipelineConfig
from sales_pipeline.pipeline import run_pipeline


def test_run_pipeline_end_to_end(tmp_path, valid_orders):
    source = tmp_path / "raw" / "orders.csv"
    source.parent.mkdir()
    valid_orders.to_csv(source, index=False)
    config = PipelineConfig(
        input_path=source,
        processed_dir=tmp_path / "processed",
        reports_dir=tmp_path / "reports",
    )
    result = run_pipeline(config)
    assert result.report["input_rows"] == 2
    assert result.report["accepted_rows"] == 2
    assert result.report["recognized_revenue"] == 20.0
    assert json.loads(result.outputs["quality_report"].read_text())["unique_products"] == 2
