"""
Smoke test for $eq expression.

Tests basic $eq expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_eq(collection):
    """Test basic $eq expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 200}, {"_id": 3, "qty": 250}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isMatch": {"$eq": ["$qty", 250]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "isMatch": True},
        {"_id": 2, "isMatch": False},
        {"_id": 3, "isMatch": True},
    ]
    assertSuccess(result, expected, msg="Should support $eq expression")
