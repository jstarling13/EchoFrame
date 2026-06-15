"""Centralized structured logging for Shift Lens."""

import logging
import sys

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging once with a consistent structured format."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger("shift_lens")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced child logger (auto-configures on first use)."""
    setup_logging()
    return logging.getLogger(f"shift_lens.{name}")
