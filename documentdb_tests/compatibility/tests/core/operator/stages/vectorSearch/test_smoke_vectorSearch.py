"""
Smoke test for $vectorSearch stage.

Tests basic $vectorSearch stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


@pytest.mark.skip(reason="Requires Atlas Search configuration - not available on standard MongoDB")
def test_smoke_vectorSearch(collection):
    """Test basic $vectorSearch stage behavior."""
    # Create vector index with vectorOptions
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {
                    "key": {"embedding": "vector"},
                    "name": "embedding_vector",
                    "vectorOptions": {"type": "hnsw", "dimensions": 3.0, "similarity": "euclidean"},
                }
            ],
        },
    )

    collection.insert_many([{"_id": 1, "name": "test", "embedding": [0.1, 0.2, 0.3]}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$vectorSearch": {
                        "queryVector": [0.1, 0.2, 0.3],
                        "path": "embedding",
                        "numCandidates": 10.0,
                        "limit": 5.0,
                        "index": "embedding_vector",
                    }
                }
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "name": "test", "embedding": [0.1, 0.2, 0.3]}]
    assertSuccess(result, expected, msg="Should support $vectorSearch stage")
