"""
Smoke test for $trunc expression.

Tests basic $trunc expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_trunc(collection):
    """Test basic $trunc expression behavior."""
    collection.insert_many([{"_id": 1, "value": 10.7}, {"_id": 2, "value": -10.7}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"truncated": {"$trunc": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "truncated": 10.0}, {"_id": 2, "truncated": -10.0}]
    assertSuccess(result, expected, msg="Should support $trunc expression")
