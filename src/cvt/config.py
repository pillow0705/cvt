"""User configuration management for cvt.

Config file location:
  Linux/macOS : ~/.config/cvt/config.toml
  Windows     : %APPDATA%/cvt/config.toml

Example config.toml:
  [defaults]
  output_dir = "cwd"      # "cwd" | "source"
  verbose    = false

  [backends]
  "md->pdf"   = "weasyprint"
  "html->pdf" = "weasyprint"
  "docx->pdf" = "docx2pdf"
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from cvt.log import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# TOML read / write helpers (handle Python 3.10 vs 3.11+)
# ---------------------------------------------------------------------------

def _load_toml(path: Path) -> dict:
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path, "rb") as fh:
            return tomllib.load(fh)
    else:
        import tomli  # type: ignore[import]
        with open(path, "rb") as fh:
            return tomli.load(fh)


def _dump_toml(data: dict, path: Path) -> None:
    import tomli_w  # type: ignore[import]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        tomli_w.dump(data, fh)


# ---------------------------------------------------------------------------
# Config path
# ---------------------------------------------------------------------------

def _config_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "cvt" / "config.toml"


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULTS: dict[str, Any] = {
    "defaults": {
        "output_dir": "cwd",   # where to write output when not specified
        "verbose": False,
    },
    "backends": {},  # e.g. {"md->pdf": "weasyprint"}
}


# ---------------------------------------------------------------------------
# Config class
# ---------------------------------------------------------------------------

class Config:
    def __init__(self) -> None:
        self._path = _config_path()
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = _load_toml(self._path)
                log.debug("Loaded config from %s", self._path)
            except Exception as exc:
                log.warning("Could not read config %s: %s", self._path, exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        _dump_toml(self._data, self._path)
        log.debug("Saved config to %s", self._path)

    # ------------------------------------------------------------------
    # Low-level get / set  (dot-separated keys, e.g. "defaults.verbose")
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        node: Any = self._data
        for part in parts:
            if not isinstance(node, dict) or part not in node:
                # Fall back to built-in defaults
                node2: Any = _DEFAULTS
                for p2 in parts:
                    if isinstance(node2, dict) and p2 in node2:
                        node2 = node2[p2]
                    else:
                        return default
                return node2
            node = node[part]
        return node

    def set(self, key: str, value: Any) -> None:
        parts = key.split(".")
        node = self._data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
        self._save()

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def output_dir_mode(self) -> str:
        """'cwd' or 'source'."""
        return str(self.get("defaults.output_dir", "cwd"))

    @property
    def verbose(self) -> bool:
        return bool(self.get("defaults.verbose", False))

    def preferred_backend(self, src_fmt: str, dst_fmt: str) -> str | None:
        key = f"{src_fmt}->{dst_fmt}"
        backends = self._data.get("backends", {})
        return backends.get(key)

    def as_dict(self) -> dict:
        import copy
        merged = _merge(_DEFAULTS, self._data)
        return merged

    @property
    def path(self) -> Path:
        return self._path


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_config: Config | None = None


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _merge(result[k], v)
        else:
            result[k] = v
    return result
