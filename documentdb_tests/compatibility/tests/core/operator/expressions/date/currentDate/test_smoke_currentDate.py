"""Smoke test for the $currentDate aggregation expression: the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.engine_xfail(
    engine="mongodb",
    reason="$currentDate expression requires MongoDB 8.3; the CI reference server is 8.2.4",
    raises=AssertionError,
)
def test_smoke_currentDate(collection):
    """Test the engine accepts $currentDate as an aggregation expression."""
    collection.insert_one({"_id": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$currentDate": {}}}}],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $currentDate expression")
