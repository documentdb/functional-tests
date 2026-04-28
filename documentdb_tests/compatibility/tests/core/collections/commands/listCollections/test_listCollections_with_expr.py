"""
Tests for $expr in listCollections command contexts.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_expr_in_list_collections(collection):
    """Test $expr in listCollections filter."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "listCollections": 1,
            "filter": {"$expr": {"$eq": ["$name", collection.name]}},
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: collection.name
        in [c["name"] for c in r.get("cursor", {}).get("firstBatch", [])],
    )
