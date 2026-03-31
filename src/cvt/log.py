"""Logging configuration for cvt."""

import logging
import sys

from rich.console import Console
from rich.logging import RichHandler

_console = Console(stderr=True)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=_console,
                show_path=verbose,
                rich_tracebacks=True,
            )
        ],
    )
    # Quieten noisy third-party loggers unless in verbose mode
    if not verbose:
        for name in ("weasyprint", "fontTools", "PIL", "mammoth"):
            logging.getLogger(name).setLevel(logging.ERROR)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
