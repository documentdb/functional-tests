"""
Smoke test for $multiply expression.

Tests basic $multiply expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_multiply(collection):
    """Test basic $multiply expression behavior."""
    collection.insert_many([{"_id": 1, "a": 5, "b": 4}, {"_id": 2, "a": 10, "b": 3}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"product": {"$multiply": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "product": 20}, {"_id": 2, "product": 30}]
    assertSuccess(result, expected, msg="Should support $multiply expression")
