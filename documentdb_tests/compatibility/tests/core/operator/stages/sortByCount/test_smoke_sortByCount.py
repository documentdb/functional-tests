"""
Smoke test for $sortByCount stage.

Tests basic $sortByCount functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_sortByCount(collection):
    """Test basic $sortByCount behavior."""
    collection.insert_many(
        [{"_id": 1, "category": "A"}, {"_id": 2, "category": "B"}, {"_id": 3, "category": "A"}]
    )

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$sortByCount": "$category"}], "cursor": {}},
    )

    expected = [{"_id": "A", "count": 2}, {"_id": "B", "count": 1}]
    assertSuccess(result, expected, msg="Should support $sortByCount stage")
