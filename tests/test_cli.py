import json

from sales_pipeline.cli import main


def test_cli_runs_pipeline_and_prints_report(tmp_path, valid_orders, capsys):
    source = tmp_path / "orders.csv"
    valid_orders.to_csv(source, index=False)

    exit_code = main(
        [
            "--input",
            str(source),
            "--processed-dir",
            str(tmp_path / "processed"),
            "--reports-dir",
            str(tmp_path / "reports"),
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["accepted_rows"] == 2


def test_cli_returns_nonzero_for_expected_failure(tmp_path, capsys):
    exit_code = main(["--input", str(tmp_path / "missing.csv")])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Pipeline failed" in captured.err
