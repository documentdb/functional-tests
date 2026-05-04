"""
Tests for listIndexes command — cursor batching, getMore, and large index counts.

Covers batchSize behavior, getMore iteration, killCursors, and collections with many indexes.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


@pytest.fixture
def collection_with_3_indexes(collection):
    """Collection with 3 indexes (_id + 2 secondary)."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    return collection


@pytest.fixture
def collection_with_64_indexes(collection):
    """Collection with 64 indexes (_id + 63 secondary)."""
    doc = {"_id": 1}
    for i in range(63):
        doc[f"f{i}"] = 1
    collection.insert_one(doc)
    indexes = [{"key": {f"f{i}": 1}, "name": f"f{i}_1"} for i in range(63)]
    execute_command(collection, {"createIndexes": collection.name, "indexes": indexes})
    return collection


def test_listIndexes_batchSize_0_empty_firstBatch(collection_with_3_indexes):
    """Test batchSize: 0 returns empty firstBatch with non-zero cursor ID."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 0}},
    )

    assertSuccess(result, [])


def test_listIndexes_batchSize_1_returns_one(collection_with_3_indexes):
    """Test batchSize: 1 returns exactly 1 index in firstBatch."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 1}},
    )

    assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])


def test_listIndexes_batchSize_equal_to_total(collection_with_3_indexes):
    """Test batchSize equal to total index count returns all in firstBatch with cursor.id 0."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 3}},
    )

    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
            {"v": 2, "key": {"b": 1}, "name": "b_1"},
        ],
    )


def test_listIndexes_batchSize_greater_than_total(collection_with_3_indexes):
    """Test batchSize greater than total returns all in firstBatch with cursor.id 0."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 100}},
    )

    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
            {"v": 2, "key": {"b": 1}, "name": "b_1"},
        ],
    )


def test_listIndexes_getMore_retrieves_remaining(collection_with_3_indexes):
    """Test getMore on listIndexes cursor retrieves remaining indexes."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 1}},
    )
    cursor_id = result["cursor"]["id"]

    get_more_result = execute_command(
        collection_with_3_indexes,
        {"getMore": cursor_id, "collection": collection_with_3_indexes.name},
    )

    assertSuccess(
        {"cursor": {"firstBatch": get_more_result["cursor"]["nextBatch"]}, "ok": 1.0},
        [{"v": 2, "key": {"a": 1}, "name": "a_1"}, {"v": 2, "key": {"b": 1}, "name": "b_1"}],
    )


def test_listIndexes_killCursors_succeeds(collection_with_3_indexes):
    """Test killCursors on listIndexes cursor succeeds."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 1}},
    )
    cursor_id = result["cursor"]["id"]

    kill_result = execute_command(
        collection_with_3_indexes,
        {"killCursors": collection_with_3_indexes.name, "cursors": [cursor_id]},
    )

    assertSuccess(
        kill_result,
        {
            "cursorsKilled": [cursor_id],
            "cursorsNotFound": [],
            "cursorsAlive": [],
            "cursorsUnknown": [],
            "ok": 1.0,
        },
        raw_res=True,
    )


def test_listIndexes_batchSize_1_iterate_all(collection_with_3_indexes):
    """Test listIndexes with batchSize 1 then getMore to retrieve all indexes."""
    result = execute_command(
        collection_with_3_indexes,
        {"listIndexes": collection_with_3_indexes.name, "cursor": {"batchSize": 1}},
    )
    all_indexes = list(result["cursor"]["firstBatch"])
    cursor_id = result["cursor"]["id"]

    while cursor_id != 0:
        get_more_result = execute_command(
            collection_with_3_indexes,
            {"getMore": cursor_id, "collection": collection_with_3_indexes.name, "batchSize": 1},
        )
        all_indexes.extend(get_more_result["cursor"]["nextBatch"])
        cursor_id = get_more_result["cursor"]["id"]

    assertSuccess(
        {"cursor": {"firstBatch": all_indexes}, "ok": 1.0},
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
            {"v": 2, "key": {"b": 1}, "name": "b_1"},
        ],
    )


def test_listIndexes_64_indexes(collection_with_64_indexes):
    """Test listIndexes returns all 64 indexes on a collection with 64 indexes."""
    result = execute_command(
        collection_with_64_indexes, {"listIndexes": collection_with_64_indexes.name}
    )

    expected = [{"v": 2, "key": {"_id": 1}, "name": "_id_"}]
    for i in range(63):
        expected.append({"v": 2, "key": {f"f{i}": 1}, "name": f"f{i}_1"})
    assertSuccess(result, expected)


def test_listIndexes_batchSize_10_with_64_indexes(collection_with_64_indexes):
    """Test batchSize: 10 with 64 indexes iterates via getMore, total equals 64."""
    result = execute_command(
        collection_with_64_indexes,
        {"listIndexes": collection_with_64_indexes.name, "cursor": {"batchSize": 10}},
    )
    all_indexes = list(result["cursor"]["firstBatch"])
    cursor_id = result["cursor"]["id"]

    while cursor_id != 0:
        get_more_result = execute_command(
            collection_with_64_indexes,
            {"getMore": cursor_id, "collection": collection_with_64_indexes.name, "batchSize": 10},
        )
        all_indexes.extend(get_more_result["cursor"]["nextBatch"])
        cursor_id = get_more_result["cursor"]["id"]

    expected = [{"v": 2, "key": {"_id": 1}, "name": "_id_"}]
    for i in range(63):
        expected.append({"v": 2, "key": {f"f{i}": 1}, "name": f"f{i}_1"})
    assertSuccess(
        {"cursor": {"firstBatch": all_indexes}, "ok": 1.0},
        expected,
        msg="Total indexes across all batches should equal 64",
    )
