"""Smoke test for the $toObject expression (new in 8.3): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_toObject(collection):
    """Test the engine accepts the $toObject expression."""
    collection.insert_one({"_id": 1, "s": '{"a": 1}'})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$toObject": "$s"}}}],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $toObject expression")
