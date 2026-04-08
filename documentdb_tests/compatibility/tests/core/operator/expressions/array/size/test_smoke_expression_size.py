"""
Smoke test for $size expression.

Tests basic $size expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_size(collection):
    """Test basic $size expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [1, 2, 3]}, {"_id": 2, "values": [10, 20, 30, 40, 50]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"arraySize": {"$size": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "arraySize": 3}, {"_id": 2, "arraySize": 5}]
    assertSuccess(result, expected, msg="Should support $size expression")
