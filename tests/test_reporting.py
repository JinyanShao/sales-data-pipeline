import json

from sales_pipeline.cleaning import clean_orders
from sales_pipeline.reporting import build_quality_report, write_outputs
from sales_pipeline.transformation import transform_orders


def test_write_outputs_creates_all_artifacts(tmp_path, valid_orders):
    cleaning = clean_orders(valid_orders)
    summaries = transform_orders(cleaning.accepted)
    report = build_quality_report(tmp_path / "source.csv", len(valid_orders), cleaning, summaries)
    outputs = write_outputs(summaries, cleaning, report, tmp_path / "processed", tmp_path / "reports")
    assert all(path.exists() for path in outputs.values())
    saved_report = json.loads(outputs["quality_report"].read_text(encoding="utf-8"))
    assert saved_report["recognized_revenue"] == 20.0
    assert saved_report["rejected_rows"] == 0
