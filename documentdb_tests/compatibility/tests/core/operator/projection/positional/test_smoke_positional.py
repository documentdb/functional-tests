"""
Smoke test for positional projection operator.

Tests basic positional projection functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_positional(collection):
    """Test basic positional projection behavior."""
    collection.insert_many([{"_id": 1, "grades": [80, 85, 90]}, {"_id": 2, "grades": [88, 92, 77]}])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"grades": {"$gte": 85}},
            "projection": {"grades.$": 1},
        },
    )

    expected = [{"_id": 1, "grades": [85]}, {"_id": 2, "grades": [88]}]
    assertSuccess(result, expected, msg="Should support positional projection")
