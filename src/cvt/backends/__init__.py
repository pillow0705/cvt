"""Backend package — all converters are imported here for auto-registration."""

from cvt.backends.data import DataConverter
from cvt.backends.markup import (
    HtmlToMarkdownConverter,
    HtmlToPdfConverter,
    HtmlToTxtConverter,
    MarkdownToHtmlConverter,
    MarkdownToPdfConverter,
    MarkdownToTxtConverter,
    TxtToHtmlConverter,
    TxtToMarkdownConverter,
)
from cvt.backends.document import (
    CsvToXlsxConverter,
    DocxToHtmlConverter,
    DocxToMarkdownConverter,
    DocxToPdfConverter,
    DocxToTxtConverter,
    PdfToMarkdownConverter,
    PdfToTxtConverter,
    PptxToHtmlConverter,
    PptxToTxtConverter,
    XlsxToCsvConverter,
    XlsxToJsonConverter,
)
from cvt.backends.image import ImageConverter

ALL_BACKENDS = [
    DataConverter,
    MarkdownToHtmlConverter,
    MarkdownToTxtConverter,
    MarkdownToPdfConverter,
    HtmlToMarkdownConverter,
    HtmlToTxtConverter,
    HtmlToPdfConverter,
    TxtToMarkdownConverter,
    TxtToHtmlConverter,
    DocxToHtmlConverter,
    DocxToMarkdownConverter,
    DocxToTxtConverter,
    DocxToPdfConverter,
    PdfToTxtConverter,
    PdfToMarkdownConverter,
    XlsxToCsvConverter,
    XlsxToJsonConverter,
    CsvToXlsxConverter,
    PptxToTxtConverter,
    PptxToHtmlConverter,
    ImageConverter,
]
