"""Tests for data/config format conversions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from cvt.converter import convert_file


# ---------------------------------------------------------------------------
# JSON ↔ YAML
# ---------------------------------------------------------------------------

def test_json_to_yaml(sample_json, tmp_out):
    out = tmp_out / "out.yaml"
    convert_file(sample_json, out)
    import yaml
    data = yaml.safe_load(out.read_text())
    assert data["name"] == "cvt"
    assert "features" in data


def test_yaml_to_json(sample_yaml, tmp_out):
    out = tmp_out / "out.json"
    convert_file(sample_yaml, out)
    data = json.loads(out.read_text())
    assert data["name"] == "cvt"
    assert isinstance(data["features"], list)


# ---------------------------------------------------------------------------
# JSON ↔ TOML
# ---------------------------------------------------------------------------

def test_json_to_toml(sample_json, tmp_out):
    out = tmp_out / "out.toml"
    convert_file(sample_json, out)
    if sys.version_info >= (3, 11):
        import tomllib
        with open(out, "rb") as fh:
            data = tomllib.load(fh)
    else:
        import tomli
        with open(out, "rb") as fh:
            data = tomli.load(fh)
    assert data["name"] == "cvt"


def test_toml_to_json(sample_toml, tmp_out):
    out = tmp_out / "out.json"
    convert_file(sample_toml, out)
    data = json.loads(out.read_text())
    assert data["name"] == "cvt"


# ---------------------------------------------------------------------------
# JSON ↔ XML
# ---------------------------------------------------------------------------

def test_json_to_xml(sample_json, tmp_out):
    out = tmp_out / "out.xml"
    convert_file(sample_json, out)
    assert out.exists()
    content = out.read_text()
    assert "<name>" in content or "cvt" in content


def test_xml_to_json(tmp_out):
    xml_file = tmp_out / "sample.xml"
    xml_file.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<root><name>cvt</name><version>0.1.0</version></root>',
        encoding="utf-8",
    )
    out = tmp_out / "out.json"
    convert_file(xml_file, out)
    data = json.loads(out.read_text())
    assert data["name"] == "cvt"


# ---------------------------------------------------------------------------
# CSV ↔ JSON
# ---------------------------------------------------------------------------

def test_csv_to_json(sample_csv, tmp_out):
    out = tmp_out / "out.json"
    convert_file(sample_csv, out)
    data = json.loads(out.read_text())
    assert isinstance(data, list)
    assert data[0]["name"] == "Alice"


def test_json_to_csv(tmp_out):
    src = tmp_out / "data.json"
    src.write_text(
        json.dumps([{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]),
        encoding="utf-8",
    )
    out = tmp_out / "out.csv"
    convert_file(src, out)
    content = out.read_text()
    assert "Alice" in content
    assert "Bob" in content


# ---------------------------------------------------------------------------
# CSV ↔ TSV
# ---------------------------------------------------------------------------

def test_csv_to_tsv(sample_csv, tmp_out):
    out = tmp_out / "out.tsv"
    convert_file(sample_csv, out)
    content = out.read_text()
    assert "\t" in content
    assert "Alice" in content


def test_tsv_to_csv(tmp_out):
    tsv = tmp_out / "sample.tsv"
    tsv.write_text("id\tname\n1\tAlice\n2\tBob\n", encoding="utf-8")
    out = tmp_out / "out.csv"
    convert_file(tsv, out)
    content = out.read_text()
    assert "," in content
    assert "Alice" in content


# ---------------------------------------------------------------------------
# YAML ↔ TOML
# ---------------------------------------------------------------------------

def test_yaml_to_toml(sample_yaml, tmp_out):
    out = tmp_out / "out.toml"
    convert_file(sample_yaml, out)
    assert out.exists()
    content = out.read_bytes()
    assert b"cvt" in content


# ---------------------------------------------------------------------------
# INI round-trip
# ---------------------------------------------------------------------------

def test_json_to_ini(tmp_out):
    src = tmp_out / "cfg.json"
    src.write_text(
        json.dumps({"server": {"host": "localhost", "port": "8080"}}),
        encoding="utf-8",
    )
    out = tmp_out / "out.ini"
    convert_file(src, out)
    content = out.read_text()
    assert "[server]" in content
    assert "localhost" in content


def test_ini_to_json(tmp_out):
    ini = tmp_out / "cfg.ini"
    ini.write_text("[server]\nhost = localhost\nport = 8080\n", encoding="utf-8")
    out = tmp_out / "out.json"
    convert_file(ini, out)
    data = json.loads(out.read_text())
    assert data["server"]["host"] == "localhost"
