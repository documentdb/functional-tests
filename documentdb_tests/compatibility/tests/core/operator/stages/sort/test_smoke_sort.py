"""
Smoke test for $sort stage.

Tests basic $sort functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_sort(collection):
    """Test basic $sort behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 30}, {"_id": 2, "value": 10}, {"_id": 3, "value": 20}]
    )

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$sort": {"value": 1}}], "cursor": {}},
    )

    expected = [{"_id": 2, "value": 10}, {"_id": 3, "value": 20}, {"_id": 1, "value": 30}]
    assertSuccess(result, expected, msg="Should support $sort stage")
