"""
Smoke test for $log expression.

Tests basic $log expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_log(collection):
    """Test basic $log expression behavior."""
    collection.insert_many(
        [{"_id": 1, "value": 100, "base": 10}, {"_id": 2, "value": 8, "base": 2}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"logarithm": {"$log": ["$value", "$base"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "logarithm": 2.0}, {"_id": 2, "logarithm": 3.0}]
    assertSuccess(result, expected, msg="Should support $log expression")
