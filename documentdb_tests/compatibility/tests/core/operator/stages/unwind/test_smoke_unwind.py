"""
Smoke test for $unwind stage.

Tests basic $unwind functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_unwind(collection):
    """Test basic $unwind behavior."""
    collection.insert_many([{"_id": 1, "items": ["A", "B"]}, {"_id": 2, "items": ["C"]}])

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$unwind": "$items"}], "cursor": {}},
    )

    expected = [{"_id": 1, "items": "A"}, {"_id": 1, "items": "B"}, {"_id": 2, "items": "C"}]
    assertSuccess(result, expected, msg="Should support $unwind stage")
