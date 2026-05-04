"""
Tests for listIndexes command — core behavior, response structure, and valid options.

Covers basic listIndexes functionality, index lifecycle, empty collections,
index document fields, includeIndexBuildInfo output, and valid option types.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


def test_listIndexes_default_id_index(collection):
    """Test listIndexes returns _id index with v, key, and name fields."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])


def test_listIndexes_multiple_secondary_indexes(collection):
    """Test listIndexes returns all indexes including secondary indexes."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
            {"v": 2, "key": {"b": 1}, "name": "b_1"},
        ],
    )


def test_listIndexes_explicit_empty_collection(database_client):
    """Test listIndexes on explicitly created empty collection returns _id index."""
    coll_name = "test_explicit_empty_coll"
    database_client.create_collection(coll_name)
    coll = database_client[coll_name]
    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
    finally:
        coll.drop()


def test_listIndexes_implicit_empty_collection(collection):
    """Test listIndexes on implicit empty collection (insert then delete all) returns _id."""
    collection.insert_one({"_id": 1})
    collection.delete_many({})
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])


def test_listIndexes_after_createIndex(collection):
    """Test listIndexes after createIndex returns 2 indexes."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
        ],
    )


def test_listIndexes_after_dropIndex(collection):
    """Test listIndexes after dropIndex returns decremented count."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    collection.drop_index("a_1")
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"b": 1}, "name": "b_1"},
        ],
    )


def test_listIndexes_after_dropIndexes_star(collection):
    """Test listIndexes after dropIndexes '*' returns only _id index."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    execute_command(collection, {"dropIndexes": collection.name, "index": "*"})
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])


def test_listIndexes_index_custom_name(collection):
    """Test listIndexes index created with custom name shows that name."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="my_custom_index")
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "my_custom_index"},
        ],
    )


def test_listIndexes_index_default_name(collection):
    """Test listIndexes auto-generated index name format field1_dir_field2_dir."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    collection.create_index([("a", 1), ("b", -1)])
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1, "b": -1}, "name": "a_1_b_-1"},
        ],
    )


def test_listIndexes_includeIndexBuildInfo_wraps_in_spec(collection):
    """Test listIndexes with includeIndexBuildInfo: true wraps index specs in spec subdocument."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection, {"listIndexes": collection.name, "includeIndexBuildInfo": True}
    )
    assertSuccess(result, [{"spec": {"v": 2, "key": {"_id": 1}, "name": "_id_"}}])


VALID_OPTIONS: list[IndexTestCase] = [
    IndexTestCase(
        "batchSize_positive_int",
        command_options={"cursor": {"batchSize": 10}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Positive int batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_long",
        command_options={"cursor": {"batchSize": Int64(10)}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Long batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_whole_double",
        command_options={"cursor": {"batchSize": 10.0}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Whole double batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_whole_decimal128",
        command_options={"cursor": {"batchSize": Decimal128("10")}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Whole Decimal128 batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_fractional_double",
        command_options={"cursor": {"batchSize": 1.5}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Fractional double batchSize should succeed (truncated)",
    ),
    IndexTestCase(
        "batchSize_infinity",
        command_options={"cursor": {"batchSize": float("inf")}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Infinity batchSize should return all indexes",
    ),
    IndexTestCase(
        "batchSize_INT32_MAX",
        command_options={"cursor": {"batchSize": 2147483647}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="INT32_MAX batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_INT64_MAX",
        command_options={"cursor": {"batchSize": Int64(9223372036854775807)}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="INT64_MAX batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_zero",
        command_options={"cursor": {"batchSize": 0}},
        expected=[],
        msg="Zero batchSize should return empty firstBatch",
    ),
    IndexTestCase(
        "batchSize_nan",
        command_options={"cursor": {"batchSize": float("nan")}},
        expected=[],
        msg="NaN batchSize should return empty firstBatch",
    ),
    IndexTestCase(
        "buildInfo_true",
        command_options={"includeIndexBuildInfo": True},
        expected=[{"spec": {"v": 2, "key": {"_id": 1}, "name": "_id_"}}],
        msg="includeIndexBuildInfo true should wrap in spec",
    ),
    IndexTestCase(
        "buildInfo_false",
        command_options={"includeIndexBuildInfo": False},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="includeIndexBuildInfo false should return default",
    ),
    IndexTestCase(
        "buildUUIDs_true",
        command_options={"includeBuildUUIDs": True},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="includeBuildUUIDs true should succeed",
    ),
    IndexTestCase(
        "buildUUIDs_false",
        command_options={"includeBuildUUIDs": False},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="includeBuildUUIDs false should succeed",
    ),
    IndexTestCase(
        "buildUUIDs_true_buildInfo_false",
        command_options={"includeBuildUUIDs": True, "includeIndexBuildInfo": False},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="includeBuildUUIDs true with includeIndexBuildInfo false should succeed",
    ),
    IndexTestCase(
        "both_false",
        command_options={"includeBuildUUIDs": False, "includeIndexBuildInfo": False},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Both false should succeed",
    ),
    IndexTestCase(
        "buildInfo_true_buildUUIDs_false",
        command_options={"includeIndexBuildInfo": True, "includeBuildUUIDs": False},
        expected=[{"spec": {"v": 2, "key": {"_id": 1}, "name": "_id_"}}],
        msg="includeIndexBuildInfo true with includeBuildUUIDs false should succeed",
    ),
    IndexTestCase(
        "cursor_null",
        command_options={"cursor": None},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Null cursor should return all indexes",
    ),
    IndexTestCase(
        "cursor_empty",
        command_options={"cursor": {}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Empty cursor object should return all indexes",
    ),
    IndexTestCase(
        "cursor_batchSize",
        command_options={"cursor": {"batchSize": 1}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="cursor with batchSize should succeed",
    ),
    IndexTestCase(
        "batchSize_null",
        command_options={"cursor": {"batchSize": None}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Null batchSize should return all indexes",
    ),
    IndexTestCase(
        "comment_string",
        command_options={"comment": "test comment"},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="String comment should succeed",
    ),
    IndexTestCase(
        "comment_int",
        command_options={"comment": 42},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Int comment should succeed",
    ),
    IndexTestCase(
        "comment_object",
        command_options={"comment": {"key": "value"}},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Object comment should succeed",
    ),
    IndexTestCase(
        "comment_array",
        command_options={"comment": [1, 2, 3]},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Array comment should succeed",
    ),
    IndexTestCase(
        "comment_bool",
        command_options={"comment": True},
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Bool comment should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_OPTIONS))
def test_listIndexes_valid_option(collection, test):
    """Test listIndexes accepts valid batchSize types, option combinations, and comment types."""
    collection.insert_one({"_id": 1})
    cmd = {"listIndexes": collection.name}
    cmd.update(test.command_options)
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, msg=test.msg)


BATCH_SIZE_NUMERIC_EQUIVALENCE: list[IndexTestCase] = [
    IndexTestCase(
        "int",
        invalid_input=2,
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
        ],
        msg="int batchSize=2 should return 2 indexes",
    ),
    IndexTestCase(
        "long",
        invalid_input=Int64(2),
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
        ],
        msg="NumberLong batchSize=2 should return 2 indexes",
    ),
    IndexTestCase(
        "double",
        invalid_input=2.0,
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
        ],
        msg="double batchSize=2.0 should return 2 indexes",
    ),
    IndexTestCase(
        "decimal128",
        invalid_input=Decimal128("2"),
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
        ],
        msg="Decimal128 batchSize=2 should return 2 indexes",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BATCH_SIZE_NUMERIC_EQUIVALENCE))
def test_listIndexes_batchSize_numeric_equivalence(collection, test):
    """Test batchSize as int, NumberLong, double, NumberDecimal all return identical firstBatch."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    result = execute_command(
        collection,
        {"listIndexes": collection.name, "cursor": {"batchSize": test.invalid_input}},
    )
    assertSuccess(result, test.expected, msg=test.msg)
