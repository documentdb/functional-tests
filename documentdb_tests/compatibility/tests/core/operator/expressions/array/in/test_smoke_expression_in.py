"""
Smoke test for $in expression.

Tests basic $in expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_in(collection):
    """Test basic $in expression behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 2, "array": [1, 2, 3]}, {"_id": 2, "value": 5, "array": [1, 2, 3]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"found": {"$in": ["$value", "$array"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "found": True}, {"_id": 2, "found": False}]
    assertSuccess(result, expected, msg="Should support $in expression")
