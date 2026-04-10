"""
Smoke test for $abs expression.

Tests basic $abs expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_abs(collection):
    """Test basic $abs expression behavior."""
    collection.insert_many([{"_id": 1, "value": -10}, {"_id": 2, "value": 20}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"absolute": {"$abs": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "absolute": 10}, {"_id": 2, "absolute": 20}]
    assertSuccess(result, expected, msg="Should support $abs expression")
