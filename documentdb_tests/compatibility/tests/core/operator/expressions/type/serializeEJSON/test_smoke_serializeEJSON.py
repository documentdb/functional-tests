"""Smoke test for the $serializeEJSON expression (new in 8.3): the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_serializeEJSON(collection):
    """Test the engine accepts the $serializeEJSON expression."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$serializeEJSON": {"input": "$x"}}}}],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $serializeEJSON expression")
