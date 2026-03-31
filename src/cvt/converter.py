"""High-level conversion orchestrator."""

from __future__ import annotations

import re
from pathlib import Path

from cvt.backends.base import BackendUnavailableError, ConversionError
from cvt.config import get_config
from cvt.log import get_logger
from cvt.registry import get_registry

log = get_logger(__name__)


def _resolve_output(
    src: Path,
    dst_arg: Path | None,
    dst_ext: str | None,
) -> Path:
    """
    Determine the output file path.

    Priority:
      1. Explicit dst_arg if given and looks like a file (has extension).
      2. If dst_arg is a directory, place file inside it.
      3. If only dst_ext given, use config output_dir_mode to choose location.
    """
    config = get_config()

    if dst_arg is not None:
        dst_arg = Path(dst_arg)
        if dst_arg.is_dir():
            ext = dst_ext or src.suffix
            return dst_arg / (src.stem + ("." + ext.lstrip(".") if ext else src.suffix))
        return dst_arg

    # No explicit destination — derive from source name + ext
    if dst_ext is None:
        raise ValueError("Either output path or --to extension must be provided.")

    stem = src.stem
    ext = "." + dst_ext.lstrip(".")
    filename = stem + ext

    if config.output_dir_mode == "source":
        return src.parent / filename
    else:
        return Path.cwd() / filename


def convert_file(
    src: Path,
    dst: Path | None = None,
    dst_ext: str | None = None,
    backend: str | None = None,
    overwrite: bool = True,
) -> Path:
    """
    Convert a single file.

    Parameters
    ----------
    src :
        Source file path.
    dst :
        Explicit output path or directory. If None, derived automatically.
    dst_ext :
        Target format extension (without dot). Used when dst is not given.
    backend :
        Force a specific backend name.
    overwrite :
        Whether to overwrite an existing destination file.

    Returns
    -------
    Path
        The path of the written output file.
    """
    src = Path(src).resolve()
    if not src.exists():
        raise FileNotFoundError(f"Source file not found: {src}")

    out_path = _resolve_output(src, dst, dst_ext)
    out_path = out_path.resolve()

    if not overwrite and out_path.exists():
        raise FileExistsError(f"Output already exists (use --overwrite): {out_path}")

    src_ext = src.suffix.lstrip(".").lower()
    out_ext = out_path.suffix.lstrip(".").lower()

    if src_ext == out_ext:
        log.warning("Source and destination have the same extension (%s); copying.", src_ext)
        import shutil
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, out_path)
        return out_path

    config = get_config()
    preferred = backend or config.preferred_backend(src_ext, out_ext)

    registry = get_registry()
    try:
        converter = registry.get_backend(src_ext, out_ext, preferred)
    except BackendUnavailableError as exc:
        raise BackendUnavailableError(str(exc)) from exc

    out_path.parent.mkdir(parents=True, exist_ok=True)
    log.info("Converting %s → %s  [%s]", src.name, out_path.name, converter.name)
    try:
        converter.convert(src, out_path)
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Unexpected error during conversion: {exc}") from exc

    log.info("Output written to %s", out_path)
    return out_path


def batch_convert(
    src_ext: str,
    dst_ext: str,
    input_dir: Path = Path("."),
    output_dir: Path | None = None,
    recursive: bool = False,
    backend: str | None = None,
    overwrite: bool = True,
    pattern: str | None = None,
) -> list[tuple[Path, Path | Exception]]:
    """
    Convert all files matching src_ext in input_dir.

    Returns
    -------
    list of (src_path, result)
        result is the output Path on success, or an Exception on failure.
    """
    input_dir = Path(input_dir).resolve()
    glob_fn = input_dir.rglob if recursive else input_dir.glob
    glob_pat = f"*.{src_ext.lstrip('.')}"

    files = sorted(glob_fn(glob_pat))
    if pattern:
        rx = re.compile(pattern, re.IGNORECASE)
        files = [f for f in files if rx.search(f.name)]

    results: list[tuple[Path, Path | Exception]] = []

    for src in files:
        if output_dir is not None:
            dst = Path(output_dir) / (src.stem + "." + dst_ext.lstrip("."))
        else:
            dst = None

        try:
            out = convert_file(
                src,
                dst=dst,
                dst_ext=dst_ext,
                backend=backend,
                overwrite=overwrite,
            )
            results.append((src, out))
        except Exception as exc:
            log.error("Failed to convert %s: %s", src, exc)
            results.append((src, exc))

    return results
