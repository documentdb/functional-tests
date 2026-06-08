"""Shared test case for BSON type round-trip tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class RoundTripTestCase(BaseTestCase):
    """Test case for BSON type storage and retrieval.

    Attributes:
        value: The value to insert and retrieve.
    """

    value: Any = None
