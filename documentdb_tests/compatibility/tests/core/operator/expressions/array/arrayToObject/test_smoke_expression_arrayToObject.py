"""
Smoke test for $arrayToObject expression.

Tests basic $arrayToObject expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_arrayToObject(collection):
    """Test basic $arrayToObject expression behavior."""
    collection.insert_many(
        [
            {"_id": 1, "pairs": [{"k": "a", "v": 1}, {"k": "b", "v": 2}]},
            {"_id": 2, "pairs": [{"k": "x", "v": 10}, {"k": "y", "v": 20}]},
        ]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"obj": {"$arrayToObject": "$pairs"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "obj": {"a": 1, "b": 2}}, {"_id": 2, "obj": {"x": 10, "y": 20}}]
    assertSuccess(result, expected, msg="Should support $arrayToObject expression")
