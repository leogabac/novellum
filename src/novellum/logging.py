"""CLI logging helpers with a sysentropy-backed fast path."""

from __future__ import annotations

from contextlib import contextmanager
import logging
import sys
import time
from typing import Iterator

try:
    from sysentropy import get_logger as get_sysentropy_logger
    from sysentropy import time_block as sysentropy_time_block
except ImportError:  # pragma: no cover
    get_sysentropy_logger = None
    sysentropy_time_block = None


def get_cli_logger(name: str = "novellum") -> logging.Logger:
    """Return a logger suitable for user-facing CLI status messages."""

    if get_sysentropy_logger is not None:
        logger = get_sysentropy_logger(name, level=logging.INFO)
        _rebind_stdout_streams(logger)
        return logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    _rebind_stdout_streams(logger)
    return logger


@contextmanager
def time_status(label: str, logger: logging.Logger) -> Iterator[None]:
    """Time a user-facing operation, using sysentropy when available."""

    if sysentropy_time_block is not None:
        with sysentropy_time_block(label, logger=logger):
            yield
        return

    started = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - started
        logger.info("%s completed in %.6fs", label, elapsed)


def _rebind_stdout_streams(logger: logging.Logger) -> None:
    """Point stdout-backed handlers at the current ``sys.stdout``."""

    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            continue
        if isinstance(handler, logging.StreamHandler):
            handler.stream = sys.stdout
