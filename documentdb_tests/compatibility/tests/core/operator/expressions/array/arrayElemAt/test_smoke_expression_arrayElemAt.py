"""
Smoke test for $arrayElemAt expression.

Tests basic $arrayElemAt expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_arrayElemAt(collection):
    """Test basic $arrayElemAt expression behavior."""
    collection.insert_many([{"_id": 1, "values": [10, 20, 30]}, {"_id": 2, "values": [5, 15, 25]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"element": {"$arrayElemAt": ["$values", 1]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "element": 20}, {"_id": 2, "element": 15}]
    assertSuccess(result, expected, msg="Should support $arrayElemAt expression")
