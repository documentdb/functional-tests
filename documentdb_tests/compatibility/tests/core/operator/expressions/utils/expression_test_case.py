"""Shared test case for expression/field path tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ExpressionTestCase(BaseTestCase):
    """Test case for expression and field path tests."""

    expression: Any = None
    doc: dict | None = None
