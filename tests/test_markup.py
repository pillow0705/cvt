"""Tests for markup/text conversions."""

from __future__ import annotations

import pytest

from cvt.backends.base import _try_import
from cvt.converter import convert_file

_weasyprint_ok = _try_import("weasyprint")


def test_md_to_html(sample_md, tmp_out):
    out = tmp_out / "out.html"
    convert_file(sample_md, out)
    content = out.read_text()
    assert "<h1" in content  # may include id="..." attribute
    assert "CVT" in content


def test_md_to_txt(sample_md, tmp_out):
    out = tmp_out / "out.txt"
    convert_file(sample_md, out)
    content = out.read_text()
    assert "CVT" in content
    assert len(content) > 10


def test_html_to_md(sample_html, tmp_out):
    out = tmp_out / "out.md"
    convert_file(sample_html, out)
    content = out.read_text()
    assert "CVT" in content


def test_html_to_txt(sample_html, tmp_out):
    out = tmp_out / "out.txt"
    convert_file(sample_html, out)
    content = out.read_text()
    assert "CVT" in content


def test_txt_to_md(sample_txt, tmp_out):
    out = tmp_out / "out.md"
    convert_file(sample_txt, out)
    content = out.read_text()
    assert "CVT" in content


def test_txt_to_html(sample_txt, tmp_out):
    out = tmp_out / "out.html"
    convert_file(sample_txt, out)
    content = out.read_text()
    assert "html" in content.lower()
    assert "CVT" in content


@pytest.mark.skipif(not _weasyprint_ok, reason="weasyprint system libs not available")
def test_md_to_pdf(sample_md, tmp_out):
    out = tmp_out / "out.pdf"
    convert_file(sample_md, out)
    assert out.exists()
    assert out.stat().st_size > 100


@pytest.mark.skipif(not _weasyprint_ok, reason="weasyprint system libs not available")
def test_html_to_pdf(sample_html, tmp_out):
    out = tmp_out / "out.pdf"
    convert_file(sample_html, out)
    assert out.exists()
    assert out.stat().st_size > 100
