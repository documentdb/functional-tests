"""
Smoke test for $allElementsTrue expression.

Tests basic $allElementsTrue expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_allElementsTrue(collection):
    """Test basic $allElementsTrue expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [True, True, True]}, {"_id": 2, "values": [True, False, True]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"allTrue": {"$allElementsTrue": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "allTrue": True}, {"_id": 2, "allTrue": False}]
    assertSuccess(result, expected, msg="Should support $allElementsTrue expression")
