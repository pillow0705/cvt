"""Tests for the CLI interface."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from cvt.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "convert" in result.output


def test_convert_json_to_yaml(runner, sample_json, tmp_out):
    out = str(tmp_out / "out.yaml")
    result = runner.invoke(main, ["convert", str(sample_json), out])
    assert result.exit_code == 0, result.output
    assert Path(out).exists()


def test_convert_with_to_flag(runner, sample_json, tmp_path, monkeypatch):
    # Change cwd so we can predict output location
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main, ["convert", str(sample_json), "--to", "yaml"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "sample.yaml").exists()


def test_convert_missing_output_arg(runner, sample_json):
    result = runner.invoke(main, ["convert", str(sample_json)])
    assert result.exit_code != 0


def test_list_formats(runner):
    result = runner.invoke(main, ["list", "formats"])
    assert result.exit_code == 0
    # At minimum data conversions should show up (always available)
    assert "json" in result.output.lower()


def test_list_formats_all(runner):
    result = runner.invoke(main, ["list", "formats", "--all"])
    assert result.exit_code == 0


def test_list_backends(runner):
    result = runner.invoke(main, ["list", "backends"])
    assert result.exit_code == 0


def test_config_show(runner):
    result = runner.invoke(main, ["config", "show"])
    assert result.exit_code == 0


def test_batch_convert(runner, tmp_path, fixtures_dir):
    import shutil
    # Copy some fixtures to a temp dir
    shutil.copy(fixtures_dir / "sample.json", tmp_path / "a.json")
    shutil.copy(fixtures_dir / "sample.json", tmp_path / "b.json")
    out_dir = tmp_path / "out"
    result = runner.invoke(
        main,
        ["batch", "--from", "json", "--to", "yaml", "--dir", str(tmp_path), "--out-dir", str(out_dir)],
    )
    assert result.exit_code == 0, result.output
    assert (out_dir / "a.yaml").exists()
    assert (out_dir / "b.yaml").exists()


def test_convert_no_overwrite(runner, sample_json, tmp_out):
    out = tmp_out / "out.yaml"
    out.write_text("existing")
    result = runner.invoke(main, ["convert", str(sample_json), str(out), "--no-overwrite"])
    assert result.exit_code == 2  # FileExists


@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"
