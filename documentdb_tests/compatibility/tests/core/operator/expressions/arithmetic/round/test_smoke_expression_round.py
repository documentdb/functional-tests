"""
Smoke test for $round expression.

Tests basic $round expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_round(collection):
    """Test basic $round expression behavior."""
    collection.insert_many([{"_id": 1, "value": 10.3}, {"_id": 2, "value": 20.7}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"rounded": {"$round": "$value"}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "rounded": 10.0}, {"_id": 2, "rounded": 21.0}]
    assertSuccess(result, expected, msg="Should support $round expression")
