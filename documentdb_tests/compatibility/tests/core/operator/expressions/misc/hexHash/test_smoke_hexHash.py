"""Smoke test for the $hexHash expression (new in 8.3): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.engine_xfail(
    engine="mongodb",
    reason="$hexHash requires MongoDB 8.3; the CI reference server is 8.2.4",
    raises=AssertionError,
)
def test_smoke_hexHash(collection):
    """Test the engine accepts the $hexHash expression."""
    collection.insert_one({"_id": 1, "s": "abc"})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "result": {"$hexHash": {"input": "$s", "algorithm": "sha256"}},
                    }
                }
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $hexHash expression")
