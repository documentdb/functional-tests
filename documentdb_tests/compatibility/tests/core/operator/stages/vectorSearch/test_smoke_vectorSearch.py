"""
Smoke test for $vectorSearch stage.

Tests basic $vectorSearch stage functionality against a mongot-backed search
target. Gated with requires(search=True) so it is deselected on non-search
targets rather than unconditionally skipped.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

from .utils.vectorSearch_common import wait_for_search_index_ready

pytestmark = [pytest.mark.smoke, pytest.mark.requires(search=True)]


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

    wait_for_search_index_ready(collection)

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
