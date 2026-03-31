"""Image format converters (requires Pillow)."""

from __future__ import annotations

from pathlib import Path

from cvt.backends.base import BaseConverter, ConversionError
from cvt.log import get_logger

log = get_logger(__name__)

_IMAGE_FMTS = ["png", "jpg", "jpeg", "webp", "bmp", "gif", "tiff", "tif", "ico"]


class ImageConverter(BaseConverter):
    name = "pillow"
    requires = ["PIL"]
    supported = [
        (src, dst)
        for src in _IMAGE_FMTS
        for dst in _IMAGE_FMTS
        if src != dst
    ]

    # Pillow format name by extension
    _FMT_MAP = {
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
        "bmp": "BMP",
        "gif": "GIF",
        "tiff": "TIFF",
        "tif": "TIFF",
        "ico": "ICO",
    }

    def convert(self, src: Path, dst: Path, **options) -> None:
        from PIL import Image  # type: ignore[import]
        dst_ext = dst.suffix.lstrip(".").lower()
        fmt = self._FMT_MAP.get(dst_ext)
        if fmt is None:
            raise ConversionError(f"Unsupported image output format: {dst_ext}")
        try:
            with Image.open(src) as img:
                # Convert palette/RGBA to RGB for JPEG
                if fmt == "JPEG" and img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                img.save(str(dst), format=fmt)
        except Exception as exc:
            raise ConversionError(f"Image conversion failed: {exc}") from exc
        log.debug("Converted %s → %s (image/%s)", src.name, dst.name, fmt)
