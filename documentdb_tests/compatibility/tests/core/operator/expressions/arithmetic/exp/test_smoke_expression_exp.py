"""
Smoke test for $exp expression.

Tests basic $exp expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_exp(collection):
    """Test basic $exp expression behavior."""
    collection.insert_many([{"_id": 1, "value": 0}, {"_id": 2, "value": 1}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"exponential": {"$exp": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "exponential": 1.0}, {"_id": 2, "exponential": 2.718281828459045}]
    assertSuccess(result, expected, msg="Should support $exp expression")
