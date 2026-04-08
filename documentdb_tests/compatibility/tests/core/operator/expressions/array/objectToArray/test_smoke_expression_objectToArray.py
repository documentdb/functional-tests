"""
Smoke test for $objectToArray expression.

Tests basic $objectToArray expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_objectToArray(collection):
    """Test basic $objectToArray expression behavior."""
    collection.insert_many(
        [{"_id": 1, "obj": {"a": 1, "b": 2}}, {"_id": 2, "obj": {"x": 10, "y": 20}}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"array": {"$objectToArray": "$obj"}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "array": [{"k": "a", "v": 1}, {"k": "b", "v": 2}]},
        {"_id": 2, "array": [{"k": "x", "v": 10}, {"k": "y", "v": 20}]},
    ]
    assertSuccess(result, expected, msg="Should support $objectToArray expression")
