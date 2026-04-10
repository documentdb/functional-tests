"""
Smoke test for $sqrt expression.

Tests basic $sqrt expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_sqrt(collection):
    """Test basic $sqrt expression behavior."""
    collection.insert_many([{"_id": 1, "value": 16}, {"_id": 2, "value": 25}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"squareRoot": {"$sqrt": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "squareRoot": 4.0}, {"_id": 2, "squareRoot": 5.0}]
    assertSuccess(result, expected, msg="Should support $sqrt expression")
