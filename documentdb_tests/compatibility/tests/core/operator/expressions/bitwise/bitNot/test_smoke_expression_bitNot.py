"""
Smoke test for $bitNot expression.

Tests basic $bitNot expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_bitNot(collection):
    """Test basic $bitNot expression behavior."""
    collection.insert_many([{"_id": 1, "value": 5}, {"_id": 2, "value": 10}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"result": {"$bitNot": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "result": -6}, {"_id": 2, "result": -11}]
    assertSuccess(result, expected, msg="Should support $bitNot expression")
