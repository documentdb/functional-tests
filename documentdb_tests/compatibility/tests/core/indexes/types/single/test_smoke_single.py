"""
Smoke test for single index type.

Tests basic single field index functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexes_single(collection):
    """Test basic single field index behavior."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"name": 1}, "name": "name_1"}]},
    )

    expected = {
        "numIndexesBefore": 1,
        "numIndexesAfter": 2,
        "createdCollectionAutomatically": True,
        "ok": 1.0,
    }
    assertSuccessPartial(result, expected, msg="Should support single field index type")
