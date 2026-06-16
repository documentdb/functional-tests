"""Shared test case for $[<identifier>] positional-filtered update operator tests."""

from dataclasses import dataclass
from typing import Any

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)


@dataclass(frozen=True)
class FilteredUpdateTestCase(UpdateTestCase):
    """Test case for $[<identifier>] positional-filtered update operator tests."""

    array_filters: Any = None
