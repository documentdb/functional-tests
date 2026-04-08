"""
Smoke test for $range expression.

Tests basic $range expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_range(collection):
    """Test basic $range expression behavior."""
    collection.insert_many([{"_id": 1, "start": 0, "end": 5}, {"_id": 2, "start": 10, "end": 13}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"sequence": {"$range": ["$start", "$end"]}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "sequence": [0, 1, 2, 3, 4]}, {"_id": 2, "sequence": [10, 11, 12]}]
    assertSuccess(result, expected, msg="Should support $range expression")
