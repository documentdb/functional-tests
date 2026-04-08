"""
Smoke test for $elemMatch query operator.

Tests basic $elemMatch query operator functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_query_elemMatch(collection):
    """Test basic $elemMatch query operator behavior."""
    collection.insert_many(
        [
            {"_id": 1, "scores": [82, 85, 88]},
            {"_id": 2, "scores": [75, 88, 89]},
            {"_id": 3, "scores": [90, 95, 100]},
        ]
    )

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"scores": {"$elemMatch": {"$gte": 80, "$lt": 85}}}},
    )

    expected = [{"_id": 1, "scores": [82, 85, 88]}]
    assertSuccess(result, expected, msg="Should support $elemMatch query operator")
