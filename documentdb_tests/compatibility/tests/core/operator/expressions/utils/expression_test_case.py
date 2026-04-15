"""
Shared test case for expression/field path tests.
"""

from dataclasses import dataclass
from typing import Any, Optional

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class ExpressionTestCase(BaseTestCase):
    """Test case for expression and field path tests."""

    expression: Any = None
    doc: Optional[dict] = None
