"""Shared test case for update operator tests."""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class UpdateTestCase(BaseTestCase):
    """Test case for update operator tests."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None
    upsert: bool = False
