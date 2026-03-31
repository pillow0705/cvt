"""Data / configuration format converters.

Supported formats: JSON, YAML, TOML, XML, CSV, TSV, INI
All conversions go through an intermediate Python object (dict/list).
"""

from __future__ import annotations

import configparser
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any

from cvt.backends.base import BaseConverter, ConversionError, _try_import
from cvt.log import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Format I/O helpers
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(data: Any, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _read_yaml(path: Path) -> Any:
    import yaml  # type: ignore[import]
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _write_yaml(data: Any, path: Path) -> None:
    import yaml  # type: ignore[import]
    with open(path, "w", encoding="utf-8") as fh:
        yaml.dump(data, fh, allow_unicode=True, default_flow_style=False)


def _read_toml(path: Path) -> Any:
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    else:
        import tomli  # type: ignore[import]
        with open(path, "rb") as fh:
            return tomli.load(fh)


def _write_toml(data: Any, path: Path) -> None:
    import tomli_w  # type: ignore[import]
    if not isinstance(data, dict):
        raise ConversionError("TOML output requires a mapping at the top level.")
    with open(path, "wb") as fh:
        tomli_w.dump(data, fh)


def _read_xml(path: Path) -> Any:
    from lxml import etree  # type: ignore[import]
    tree = etree.parse(str(path))
    return _xml_element_to_dict(tree.getroot())


def _xml_element_to_dict(elem) -> Any:
    from lxml import etree  # type: ignore[import]
    children = list(elem)
    if not children:
        return elem.text or ""
    result: dict[str, Any] = {}
    for child in children:
        tag = etree.QName(child.tag).localname
        value = _xml_element_to_dict(child)
        if tag in result:
            existing = result[tag]
            if not isinstance(existing, list):
                result[tag] = [existing]
            result[tag].append(value)
        else:
            result[tag] = value
    return result


def _write_xml(data: Any, path: Path) -> None:
    from lxml import etree  # type: ignore[import]
    root = _dict_to_xml_element("root", data)
    tree = etree.ElementTree(root)
    tree.write(str(path), pretty_print=True, xml_declaration=True, encoding="utf-8")


def _dict_to_xml_element(tag: str, data: Any):
    from lxml import etree  # type: ignore[import]
    elem = etree.Element(tag)
    if isinstance(data, dict):
        for k, v in data.items():
            child = _dict_to_xml_element(str(k), v)
            elem.append(child)
    elif isinstance(data, list):
        for item in data:
            child = _dict_to_xml_element("item", item)
            elem.append(child)
    else:
        elem.text = str(data) if data is not None else ""
    return elem


def _read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def _write_csv(data: Any, path: Path) -> None:
    rows = _normalise_to_rows(data)
    if not rows:
        path.write_text("")
        return
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _read_tsv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        return list(reader)


def _write_tsv(data: Any, path: Path) -> None:
    rows = _normalise_to_rows(data)
    if not rows:
        path.write_text("")
        return
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def _read_ini(path: Path) -> dict:
    parser = configparser.ConfigParser()
    parser.read(str(path), encoding="utf-8")
    result: dict = {}
    if parser.defaults():
        result["DEFAULT"] = dict(parser.defaults())
    for section in parser.sections():
        result[section] = dict(parser[section])
    return result


def _write_ini(data: Any, path: Path) -> None:
    if not isinstance(data, dict):
        raise ConversionError("INI output requires a mapping at the top level.")
    parser = configparser.ConfigParser()
    for section, values in data.items():
        if section == "DEFAULT":
            for k, v in values.items():
                parser.defaults()[k] = str(v)
        else:
            parser[section] = {k: str(v) for k, v in values.items()}
    with open(path, "w", encoding="utf-8") as fh:
        parser.write(fh)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _normalise_to_rows(data: Any) -> list[dict]:
    """Coerce data to a list of flat dicts suitable for CSV/TSV output."""
    if isinstance(data, list):
        return [{str(k): str(v) for k, v in (row.items() if isinstance(row, dict) else {"value": row}.items())} for row in data]
    if isinstance(data, dict):
        # If all values are dicts, treat keys as row identifiers
        if all(isinstance(v, dict) for v in data.values()):
            rows = []
            for key, val in data.items():
                row = {"_key": key}
                row.update({str(k): str(v) for k, v in val.items()})
                rows.append(row)
            return rows
        # Otherwise, single-row
        return [{str(k): str(v) for k, v in data.items()}]
    return [{"value": str(data)}]


# ---------------------------------------------------------------------------
# Reader / writer registry
# ---------------------------------------------------------------------------

READERS = {
    "json": _read_json,
    "yaml": _read_yaml,
    "yml":  _read_yaml,
    "toml": _read_toml,
    "xml":  _read_xml,
    "csv":  _read_csv,
    "tsv":  _read_tsv,
    "ini":  _read_ini,
}

WRITERS = {
    "json": _write_json,
    "yaml": _write_yaml,
    "yml":  _write_yaml,
    "toml": _write_toml,
    "xml":  _write_xml,
    "csv":  _write_csv,
    "tsv":  _write_tsv,
    "ini":  _write_ini,
}

_DATA_FORMATS = set(READERS.keys())


# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------

class DataConverter(BaseConverter):
    """Converts between data/config formats: JSON, YAML, TOML, XML, CSV, TSV, INI."""

    name = "data"
    requires = ["yaml", "lxml", "tomli_w"]

    # All pairs among supported formats
    supported = [
        (src, dst)
        for src in _DATA_FORMATS
        for dst in _DATA_FORMATS
        if src != dst
    ]

    @classmethod
    def is_available(cls) -> bool:
        # tomli is only needed on Python < 3.11
        pkgs = ["yaml", "lxml", "tomli_w"]
        if sys.version_info < (3, 11):
            pkgs.append("tomli")
        return all(_try_import(pkg) for pkg in pkgs)

    def convert(self, src: Path, dst: Path, **options) -> None:
        src_ext = src.suffix.lstrip(".").lower()
        dst_ext = dst.suffix.lstrip(".").lower()

        reader = READERS.get(src_ext)
        writer = WRITERS.get(dst_ext)

        if reader is None:
            raise ConversionError(f"No reader for format: {src_ext}")
        if writer is None:
            raise ConversionError(f"No writer for format: {dst_ext}")

        log.debug("Reading %s as %s", src, src_ext)
        try:
            data = reader(src)
        except Exception as exc:
            raise ConversionError(f"Failed to read {src}: {exc}") from exc

        log.debug("Writing %s as %s", dst, dst_ext)
        try:
            writer(data, dst)
        except Exception as exc:
            raise ConversionError(f"Failed to write {dst}: {exc}") from exc
