"""Smoke test for the $similarityEuclidean expression: the engine accepts it."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_similarityEuclidean(collection):
    """Test the engine accepts the $similarityEuclidean expression."""
    collection.insert_one({"_id": 1, "a": [0.0, 0.0], "b": [3.0, 4.0]})

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "result": {"$similarityEuclidean": ["$a", "$b"]}}}
            ],
            "cursor": {},
        },
    )

    assertCommandSupported(result, msg="Should support $similarityEuclidean expression")
