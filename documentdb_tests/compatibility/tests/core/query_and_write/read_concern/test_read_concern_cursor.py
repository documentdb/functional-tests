"""
readConcern with cursor continuation (getMore) tests.

Verifies that readConcern is applied to the initial query and that getMore
continues correctly after a readConcern query.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_getmore_after_find_with_read_concern_first_batch(collection):
    """Test find with readConcern returns correct first batch with small batchSize."""
    docs = [{"_id": i, "x": i} for i in range(10)]
    collection.insert_many(docs)

    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "batchSize": 3,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
    )
    assertSuccess(
        result,
        [{"_id": 0, "x": 0}, {"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="First batch from find with readConcern should contain 3 documents.",
    )


def test_getmore_after_find_with_read_concern_next_batch(collection):
    """Test getMore after find with readConcern returns next batch correctly."""
    docs = [{"_id": i, "x": i} for i in range(10)]
    collection.insert_many(docs)

    # Get cursor from initial find.
    initial_result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "batchSize": 3,
            "sort": {"_id": 1},
            "readConcern": {"level": "local"},
        },
    )
    cursor_id = initial_result["cursor"]["id"]

    # getMore to fetch next batch.
    getmore_result = execute_command(
        collection,
        {"getMore": cursor_id, "collection": collection.name, "batchSize": 3},
    )
    # nextBatch is the field for getMore results.
    next_batch = getmore_result["cursor"]["nextBatch"]
    expected_next = [{"_id": 3, "x": 3}, {"_id": 4, "x": 4}, {"_id": 5, "x": 5}]
    assertSuccess(
        {"cursor": {"firstBatch": next_batch}},
        expected_next,
        msg="getMore after readConcern find should return next batch correctly.",
    )
