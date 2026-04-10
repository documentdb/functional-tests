"""
Smoke test for $ne expression.

Tests basic $ne expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_ne(collection):
    """Test basic $ne expression behavior."""
    collection.insert_many([{"_id": 1, "qty": 250}, {"_id": 2, "qty": 200}, {"_id": 3, "qty": 250}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"isNotEqual": {"$ne": ["$qty", 250]}}}],
            "cursor": {},
        },
    )

    expected = [
        {"_id": 1, "isNotEqual": False},
        {"_id": 2, "isNotEqual": True},
        {"_id": 3, "isNotEqual": False},
    ]
    assertSuccess(result, expected, msg="Should support $ne expression")
