"""Smoke test for the $meta projection operator: the engine accepts it in a find projection."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_projection_meta(collection):
    """Test the engine accepts {$meta: "textScore"} in a find projection."""
    collection.insert_one({"_id": 1, "t": "hello world"})
    collection.create_index([("t", "text")])

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "hello"}},
            "projection": {"score": {"$meta": "textScore"}},
        },
    )

    assertCommandSupported(result, msg="Should support $meta projection")
