"""
Smoke test for $lastN expression.

Tests basic $lastN expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_lastN(collection):
    """Test basic $lastN expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [10, 20, 30, 40]}, {"_id": 2, "values": [5, 15, 25, 35]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"lastTwo": {"$lastN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "lastTwo": [30, 40]}, {"_id": 2, "lastTwo": [25, 35]}]
    assertSuccess(result, expected, msg="Should support $lastN expression")
