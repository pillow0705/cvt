"""Format converter registry.

The registry maps (src_ext, dst_ext) → ordered list of backend classes.
Backends are tried in registration order; the first available one wins.
"""

from __future__ import annotations

from typing import Type

from cvt.backends.base import BackendUnavailableError, BaseConverter
from cvt.log import get_logger

log = get_logger(__name__)


class Registry:
    def __init__(self) -> None:
        # (src_ext, dst_ext) → [BackendClass, ...]
        self._map: dict[tuple[str, str], list[Type[BaseConverter]]] = {}

    def register(self, backend_cls: Type[BaseConverter]) -> None:
        for src, dst in backend_cls.supported:
            key = (src.lower(), dst.lower())
            self._map.setdefault(key, []).append(backend_cls)

    def get_backends(
        self, src_fmt: str, dst_fmt: str
    ) -> list[Type[BaseConverter]]:
        """Return all registered backends for the given format pair."""
        return list(self._map.get((src_fmt.lower(), dst_fmt.lower()), []))

    def get_backend(
        self,
        src_fmt: str,
        dst_fmt: str,
        preferred: str | None = None,
    ) -> BaseConverter:
        """
        Return an instantiated backend for (src_fmt → dst_fmt).

        Parameters
        ----------
        preferred :
            Backend name (from --backend flag or config). If supplied and
            available, it is used; otherwise the first available backend
            in registration order is used.

        Raises
        ------
        BackendUnavailableError
            If no backend is registered or none is currently available.
        """
        candidates = self.get_backends(src_fmt, dst_fmt)
        if not candidates:
            raise BackendUnavailableError(
                f"No converter registered for {src_fmt} → {dst_fmt}. "
                f"Run `cvt list formats` to see supported conversions."
            )

        if preferred:
            for cls in candidates:
                if cls.name == preferred:
                    if not cls.is_available():
                        missing = cls.missing_packages()
                        raise BackendUnavailableError(
                            f"Backend '{preferred}' requires: {', '.join(missing)}. "
                            f"Install with: pip install {' '.join(missing)}"
                        )
                    return cls()
            available_names = [c.name for c in candidates]
            raise BackendUnavailableError(
                f"Backend '{preferred}' not found for {src_fmt}→{dst_fmt}. "
                f"Available: {', '.join(available_names)}"
            )

        for cls in candidates:
            if cls.is_available():
                log.debug("Selected backend: %s for %s→%s", cls.name, src_fmt, dst_fmt)
                return cls()

        # Nothing available — build helpful error message
        missing_info = []
        for cls in candidates:
            pkgs = cls.missing_packages()
            if pkgs:
                missing_info.append(f"  {cls.name}: pip install {' '.join(pkgs)}")
        hint = "\n".join(missing_info) if missing_info else "(no install hints available)"
        raise BackendUnavailableError(
            f"No backend available for {src_fmt} → {dst_fmt}.\n"
            f"Install one of the following:\n{hint}\n"
            f"Or run: pip install cvt-tool[full]"
        )

    def all_conversions(self) -> list[tuple[str, str, list[str]]]:
        """Return [(src, dst, [backend_names]), …] sorted."""
        result = []
        for (src, dst), classes in sorted(self._map.items()):
            names = [c.name for c in classes]
            result.append((src, dst, names))
        return result

    def available_conversions(self) -> list[tuple[str, str, list[str]]]:
        """Like all_conversions() but only rows where ≥1 backend is available."""
        result = []
        for src, dst, names in self.all_conversions():
            classes = self.get_backends(src, dst)
            avail = [c.name for c in classes if c.is_available()]
            if avail:
                result.append((src, dst, avail))
        return result


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: Registry | None = None


def get_registry() -> Registry:
    global _registry
    if _registry is None:
        _registry = Registry()
        _populate(_registry)
    return _registry


def _populate(reg: Registry) -> None:
    from cvt.backends import ALL_BACKENDS
    for cls in ALL_BACKENDS:
        reg.register(cls)
    log.debug("Registry: %d conversion pairs registered", len(reg._map))
