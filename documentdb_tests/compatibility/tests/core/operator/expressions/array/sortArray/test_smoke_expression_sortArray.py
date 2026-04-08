"""
Smoke test for $sortArray expression.

Tests basic $sortArray expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_expression_sortArray(collection):
    """Test basic $sortArray expression behavior."""
    collection.insert_many([{"_id": 1, "values": [3, 1, 2]}, {"_id": 2, "values": [30, 10, 20]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"sorted": {"$sortArray": {"input": "$values", "sortBy": 1}}}}
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "sorted": [1, 2, 3]}, {"_id": 2, "sorted": [10, 20, 30]}]
    assertSuccess(result, expected, msg="Should support $sortArray expression")
