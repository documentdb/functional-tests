"""
Smoke test for $vectorSearch stage.

Tests basic $vectorSearch stage functionality against a mongot-backed search
target. Gated with requires(search=True) so it is deselected on non-search
targets rather than unconditionally skipped.
"""

import time

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.smoke, pytest.mark.requires(search=True)]

_INDEX_READY_TIMEOUT_SECONDS = 120


@pytest.mark.aggregate
def test_smoke_vectorSearch(collection):
    """Test basic $vectorSearch stage behavior."""
    collection.insert_many([{"_id": 1, "name": "test", "embedding": [0.1, 0.2, 0.3]}])

    execute_command(
        collection,
        {
            "createSearchIndexes": collection.name,
            "indexes": [
                {
                    "name": "embedding_vector",
                    "type": "vectorSearch",
                    "definition": {
                        "fields": [
                            {
                                "type": "vector",
                                "path": "embedding",
                                "numDimensions": 3,
                                "similarity": "euclidean",
                            }
                        ]
                    },
                }
            ],
        },
    )

    deadline = time.monotonic() + _INDEX_READY_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        indexes = list(collection.aggregate([{"$listSearchIndexes": {}}]))
        if indexes and indexes[0].get("status") == "READY":
            break
        time.sleep(2)
    else:
        raise TimeoutError("vectorSearch index did not reach READY state")

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$vectorSearch": {
                        "index": "embedding_vector",
                        "path": "embedding",
                        "queryVector": [0.1, 0.2, 0.3],
                        "numCandidates": 10,
                        "limit": 5,
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "name": "test", "embedding": [0.1, 0.2, 0.3]}]
    assertSuccess(result, expected, msg="Should support $vectorSearch stage")
