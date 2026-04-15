"""Shared test case class and helpers for $toDate tests."""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ToDateTest(BaseTestCase):
    """Test case for $toDate operator."""

    value: Any = None
