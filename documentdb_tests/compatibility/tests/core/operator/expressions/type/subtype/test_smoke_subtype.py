"""Smoke test for the $subtype expression (new in 8.3): the engine accepts it."""

import pytest
from bson import Binary

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.engine_xfail(
    engine="mongodb",
    reason="$subtype requires MongoDB 8.3; the CI reference server is 8.2.4",
    raises=AssertionError,
)
def test_smoke_subtype(collection):
    """Test the engine accepts the $subtype expression."""
    collection.insert_one({"_id": 1, "b": Binary(b"\x01\x02", 0)})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$subtype": "$b"}}}],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $subtype expression")
