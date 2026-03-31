"""Abstract base class for all format converters."""

from __future__ import annotations

import importlib
import io
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar


# For packages that silently fail (don't raise but export nothing useful),
# verify a known attribute exists after import.
_REQUIRED_ATTRS: dict[str, str] = {
    "weasyprint": "HTML",
}


def _try_import(pkg: str) -> bool:
    """Try importing a package, suppressing any stdout/stderr noise (e.g. from weasyprint).

    Returns True only if the package imports successfully AND any required
    attribute is actually present (to catch packages that silently swallow
    errors and export nothing).
    """
    sink = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout = sink
    sys.stderr = sink
    try:
        mod = importlib.import_module(pkg)
        attr = _REQUIRED_ATTRS.get(pkg)
        if attr is not None and not hasattr(mod, attr):
            return False
        return True
    except Exception:
        return False
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class ConversionError(Exception):
    """Raised when a conversion fails."""


class BackendUnavailableError(Exception):
    """Raised when a required library is not installed."""


class BaseConverter(ABC):
    """
    All concrete backends inherit from this class.

    Attributes
    ----------
    name : str
        Short identifier used in CLI (--backend) and config file.
    supported : list[tuple[str, str]]
        Pairs of (source_ext, dest_ext) this backend can handle.
        Extensions are lowercase without leading dot, e.g. ("md", "pdf").
    requires : list[str]
        Python package names that must be importable for this backend to work.
    """

    name: ClassVar[str] = ""
    supported: ClassVar[list[tuple[str, str]]] = []
    requires: ClassVar[list[str]] = []

    # ------------------------------------------------------------------
    # Availability check
    # ------------------------------------------------------------------

    @classmethod
    def is_available(cls) -> bool:
        """Return True if all required packages are importable and functional."""
        for pkg in cls.requires:
            if not _try_import(pkg):
                return False
        return True

    @classmethod
    def missing_packages(cls) -> list[str]:
        return [pkg for pkg in cls.requires if not _try_import(pkg)]

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    @abstractmethod
    def convert(self, src: Path, dst: Path, **options) -> None:
        """
        Convert *src* and write the result to *dst*.

        Parameters
        ----------
        src :
            Path to the existing source file.
        dst :
            Path where the output should be written (parent dir is
            guaranteed to exist before this is called).
        **options :
            Backend-specific keyword arguments (passed through from CLI).

        Raises
        ------
        ConversionError
            If the conversion fails for any reason.
        """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"
