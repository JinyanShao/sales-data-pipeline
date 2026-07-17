import json

from sales_pipeline.cli import main


def test_cli_runs_pipeline_and_prints_report(tmp_path, valid_orders, capsys):
    source = tmp_path / "orders.csv"
    valid_orders.to_csv(source, index=False)
    exit_code = main([str(source), "--output-dir", str(tmp_path / "reports"), "--log-level", "WARNING"])
    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["valid_orders"] == 2


def test_cli_strict_mode_returns_two_after_exporting_rejections(tmp_path, valid_orders, capsys):
    source = tmp_path / "orders.csv"
    invalid = valid_orders.copy()
    invalid.loc[0, "quantity"] = 0
    invalid.to_csv(source, index=False)
    output_dir = tmp_path / "reports"
    exit_code = main([str(source), "--output-dir", str(output_dir), "--strict"])
    assert exit_code == 2
    assert (output_dir / "rejected_orders.csv").exists()
    assert "Strict validation failed" in capsys.readouterr().err


def test_cli_returns_nonzero_for_expected_failure(tmp_path, capsys):
    exit_code = main([str(tmp_path / "missing.csv")])
    assert exit_code == 1
    assert "Pipeline failed" in capsys.readouterr().err
