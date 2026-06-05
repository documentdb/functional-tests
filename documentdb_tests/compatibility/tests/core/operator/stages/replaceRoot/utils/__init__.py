"""Shared utilities for $replaceRoot stage tests."""

from __future__ import annotations

from .shared_limits import (
    BIG_STORED_STRING_BYTES,
    BOUNDARY_PAD_BYTES,
    MAX_OUTPUT_DOC_SIZE,
    MAX_STORED_NESTING_DEPTH,
    OVER_LIMIT_PAD_BYTES,
)

__all__ = [
    "BIG_STORED_STRING_BYTES",
    "BOUNDARY_PAD_BYTES",
    "MAX_OUTPUT_DOC_SIZE",
    "MAX_STORED_NESTING_DEPTH",
    "OVER_LIMIT_PAD_BYTES",
]
