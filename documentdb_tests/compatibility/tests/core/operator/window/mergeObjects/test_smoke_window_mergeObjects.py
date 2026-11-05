"""Smoke test for $mergeObjects as a window operator (new in 8.3): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.engine_xfail(
    engine="mongodb",
    reason="$mergeObjects as a window operator requires MongoDB 8.3; CI reference is 8.2.4",
    raises=AssertionError,
)
def test_smoke_window_mergeObjects(collection):
    """Test the engine accepts $mergeObjects as a window operator."""
    collection.insert_many([{"_id": 1, "o": {"a": 1}}, {"_id": 2, "o": {"b": 2}}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$mergeObjects": "$o",
                                "window": {"documents": ["unbounded", "current"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $mergeObjects window operator")
