"""Smoke test for the $$IDX system variable (new in 8.3): the engine accepts it in $map."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.engine_xfail(
    engine="mongodb",
    reason="$$IDX requires MongoDB 8.3; the CI reference server is 8.2.4",
    raises=AssertionError,
)
def test_smoke_idx(collection):
    """Test the engine accepts $$IDX inside $map."""
    collection.insert_one({"_id": 1, "arr": [10, 20]})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$map": {"input": "$arr", "in": "$$IDX"}}}}
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $$IDX system variable")
