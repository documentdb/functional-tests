"""
Smoke test for $slice expression.

Tests basic $slice expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_slice(collection):
    """Test basic $slice expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [1, 2, 3, 4, 5]}, {"_id": 2, "values": [10, 20, 30, 40, 50]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"sliced": {"$slice": ["$values", 2]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "sliced": [1, 2]}, {"_id": 2, "sliced": [10, 20]}]
    assertSuccess(result, expected, msg="Should support $slice expression")
