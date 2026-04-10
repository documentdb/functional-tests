"""
Smoke test for $firstN expression.

Tests basic $firstN expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_firstN(collection):
    """Test basic $firstN expression behavior."""
    collection.insert_many(
        [{"_id": 1, "values": [10, 20, 30, 40]}, {"_id": 2, "values": [5, 15, 25, 35]}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"firstTwo": {"$firstN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "firstTwo": [10, 20]}, {"_id": 2, "firstTwo": [5, 15]}]
    assertSuccess(result, expected, msg="Should support $firstN expression")
