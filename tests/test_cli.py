import pytest

from sales_pipeline.cli import main


def test_cli_returns_zero_and_logs_success(tmp_path, valid_orders, capsys):
    source = tmp_path / "orders.csv"
    valid_orders.to_csv(source, index=False)
    exit_code = main([str(source), "--output-dir", str(tmp_path / "reports")])
    assert exit_code == 0
    assert "Pipeline completed successfully" in capsys.readouterr().err


def test_cli_strict_mode_returns_one_after_exporting_rejections(tmp_path, valid_orders, capsys):
    source = tmp_path / "orders.csv"
    invalid = valid_orders.copy()
    invalid.loc[0, "quantity"] = 0
    invalid.to_csv(source, index=False)
    output_dir = tmp_path / "reports"
    exit_code = main([str(source), "--output-dir", str(output_dir), "--strict"])
    assert exit_code == 1
    assert (output_dir / "rejected_orders.csv").exists()
    assert "failed data quality checks" in capsys.readouterr().err


def test_cli_returns_two_for_input_failure(tmp_path, capsys):
    exit_code = main([str(tmp_path / "missing.csv")])
    assert exit_code == 2
    assert "Pipeline input failed" in capsys.readouterr().err


def test_cli_returns_three_for_export_failure(tmp_path, valid_orders, capsys):
    source = tmp_path / "orders.csv"
    valid_orders.to_csv(source, index=False)
    output_file = tmp_path / "not-a-directory"
    output_file.write_text("occupied", encoding="utf-8")
    exit_code = main([str(source), "--output-dir", str(output_file)])
    assert exit_code == 3
    assert "Pipeline output failed" in capsys.readouterr().err


def test_cli_invalid_log_level_uses_configuration_exit_code():
    with pytest.raises(SystemExit) as error:
        main(["orders.csv", "--log-level", "TRACE"])
    assert error.value.code == 2
