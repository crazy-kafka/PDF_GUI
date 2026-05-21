"""Centralized logging for PDF_GUI. Prints to the terminal where GUI is launched."""

import logging
import os
import sys

_logger = None


def get_logger(name: str = "pdf_gui") -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    level = logging.DEBUG if os.environ.get("PDF_GUI_DEBUG") else logging.INFO

    _logger = logging.getLogger(name)
    _logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(fmt)
    _logger.addHandler(handler)

    return _logger
