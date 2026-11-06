"""Smoke test for the $similarityDotProduct expression: the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_similarityDotProduct(collection):
    """Test the engine accepts the $similarityDotProduct expression."""
    collection.insert_one({"_id": 1, "a": [1.0, 2.0], "b": [3.0, 4.0]})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$similarityDotProduct": ["$a", "$b"]}}}
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $similarityDotProduct expression")
