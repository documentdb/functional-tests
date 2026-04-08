"""
Smoke test for $pow expression.

Tests basic $pow expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_pow(collection):
    """Test basic $pow expression behavior."""
    collection.insert_many(
        [{"_id": 1, "base": 2, "exponent": 3}, {"_id": 2, "base": 5, "exponent": 2}]
    )

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"power": {"$pow": ["$base", "$exponent"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "power": 8}, {"_id": 2, "power": 25}]
    assertSuccess(result, expected, msg="Should support $pow expression")
