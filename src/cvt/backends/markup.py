"""Markup / text converters.

Supported conversions:
  md   → html, txt, pdf (requires weasyprint)
  html → md, txt, pdf   (requires weasyprint)
  rst  → html, txt
"""

from __future__ import annotations

import re
from pathlib import Path

from cvt.backends.base import BaseConverter, ConversionError
from cvt.log import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helper: strip HTML to plain text
# ---------------------------------------------------------------------------

def _html_to_text(html: str) -> str:
    import html2text as h2t  # type: ignore[import]
    handler = h2t.HTML2Text()
    handler.ignore_links = False
    handler.body_width = 0
    return handler.handle(html)


def _md_to_html(md_text: str) -> str:
    import markdown  # type: ignore[import]
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "footnotes", "attr_list"],
    )


def _html_to_pdf(html: str, dst: Path) -> None:
    from weasyprint import HTML  # type: ignore[import]
    HTML(string=html).write_pdf(str(dst))


# ---------------------------------------------------------------------------
# Markdown → HTML
# ---------------------------------------------------------------------------

class MarkdownToHtmlConverter(BaseConverter):
    name = "markdown"
    supported = [("md", "html")]
    requires = ["markdown"]

    def convert(self, src: Path, dst: Path, **options) -> None:
        md_text = src.read_text(encoding="utf-8")
        html = _md_to_html(md_text)
        full_html = f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'></head><body>\n{html}\n</body></html>"
        dst.write_text(full_html, encoding="utf-8")
        log.debug("Converted %s → %s (markdown→html)", src.name, dst.name)


# ---------------------------------------------------------------------------
# Markdown → TXT
# ---------------------------------------------------------------------------

class MarkdownToTxtConverter(BaseConverter):
    name = "markdown-txt"
    supported = [("md", "txt")]
    requires = ["markdown", "html2text"]

    def convert(self, src: Path, dst: Path, **options) -> None:
        md_text = src.read_text(encoding="utf-8")
        html = _md_to_html(md_text)
        text = _html_to_text(html)
        dst.write_text(text, encoding="utf-8")
        log.debug("Converted %s → %s (markdown→txt)", src.name, dst.name)


# ---------------------------------------------------------------------------
# Markdown → PDF
# ---------------------------------------------------------------------------

class MarkdownToPdfConverter(BaseConverter):
    name = "weasyprint"
    supported = [("md", "pdf")]
    requires = ["markdown", "weasyprint"]

    def convert(self, src: Path, dst: Path, **options) -> None:
        md_text = src.read_text(encoding="utf-8")
        html = _md_to_html(md_text)
        full_html = f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'><style>body{{font-family:sans-serif;max-width:800px;margin:auto;padding:2em}}</style></head><body>\n{html}\n</body></html>"
        try:
            _html_to_pdf(full_html, dst)
        except Exception as exc:
            raise ConversionError(f"PDF generation failed: {exc}") from exc
        log.debug("Converted %s → %s (markdown→pdf)", src.name, dst.name)


# ---------------------------------------------------------------------------
# HTML → Markdown
# ---------------------------------------------------------------------------

class HtmlToMarkdownConverter(BaseConverter):
    name = "html2text"
    supported = [("html", "md"), ("htm", "md")]
    requires = ["html2text"]

    def convert(self, src: Path, dst: Path, **options) -> None:
        html = src.read_text(encoding="utf-8")
        md = _html_to_text(html)
        dst.write_text(md, encoding="utf-8")
        log.debug("Converted %s → %s (html→md)", src.name, dst.name)


# ---------------------------------------------------------------------------
# HTML → TXT
# ---------------------------------------------------------------------------

class HtmlToTxtConverter(BaseConverter):
    name = "html-txt"
    supported = [("html", "txt"), ("htm", "txt")]
    requires = ["html2text"]

    def convert(self, src: Path, dst: Path, **options) -> None:
        html = src.read_text(encoding="utf-8")
        text = _html_to_text(html)
        dst.write_text(text, encoding="utf-8")
        log.debug("Converted %s → %s (html→txt)", src.name, dst.name)


# ---------------------------------------------------------------------------
# HTML → PDF
# ---------------------------------------------------------------------------

class HtmlToPdfConverter(BaseConverter):
    name = "weasyprint-html"
    supported = [("html", "pdf"), ("htm", "pdf")]
    requires = ["weasyprint"]

    def convert(self, src: Path, dst: Path, **options) -> None:
        html = src.read_text(encoding="utf-8")
        try:
            _html_to_pdf(html, dst)
        except Exception as exc:
            raise ConversionError(f"PDF generation failed: {exc}") from exc
        log.debug("Converted %s → %s (html→pdf)", src.name, dst.name)


# ---------------------------------------------------------------------------
# TXT → MD  (trivial wrap)
# ---------------------------------------------------------------------------

class TxtToMarkdownConverter(BaseConverter):
    name = "txt-md"
    supported = [("txt", "md")]
    requires = []

    def convert(self, src: Path, dst: Path, **options) -> None:
        text = src.read_text(encoding="utf-8")
        # Wrap in a fenced code block if it looks like code, else copy as-is
        dst.write_text(text, encoding="utf-8")
        log.debug("Converted %s → %s (txt→md)", src.name, dst.name)


# ---------------------------------------------------------------------------
# TXT → HTML
# ---------------------------------------------------------------------------

class TxtToHtmlConverter(BaseConverter):
    name = "txt-html"
    supported = [("txt", "html")]
    requires = []

    def convert(self, src: Path, dst: Path, **options) -> None:
        import html as html_mod
        text = src.read_text(encoding="utf-8")
        escaped = html_mod.escape(text)
        body = "<pre>" + escaped + "</pre>"
        full = f"<!DOCTYPE html>\n<html><head><meta charset='utf-8'></head><body>\n{body}\n</body></html>"
        dst.write_text(full, encoding="utf-8")
        log.debug("Converted %s → %s (txt→html)", src.name, dst.name)
