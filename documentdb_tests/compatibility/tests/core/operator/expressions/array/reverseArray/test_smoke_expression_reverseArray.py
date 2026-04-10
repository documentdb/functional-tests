"""
Smoke test for $reverseArray expression.

Tests basic $reverseArray expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_reverseArray(collection):
    """Test basic $reverseArray expression behavior."""
    collection.insert_many([{"_id": 1, "values": [1, 2, 3]}, {"_id": 2, "values": [10, 20, 30]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"reversed": {"$reverseArray": "$values"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "reversed": [3, 2, 1]}, {"_id": 2, "reversed": [30, 20, 10]}]
    assertSuccess(result, expected, msg="Should support $reverseArray expression")
