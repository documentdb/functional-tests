"""
Smoke test for $mod expression.

Tests basic $mod expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_mod(collection):
    """Test basic $mod expression behavior."""
    collection.insert_many([{"_id": 1, "a": 10, "b": 3}, {"_id": 2, "a": 20, "b": 6}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"remainder": {"$mod": ["$a", "$b"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "remainder": 1}, {"_id": 2, "remainder": 2}]
    assertSuccess(result, expected, msg="Should support $mod expression")
