"""
Tests for findAndModify data type coverage: BSON types, null semantics,
numeric equivalence.
"""

import pytest
from bson import Binary, Decimal128, Int64

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import BSON_TYPE_SAMPLES, BsonType

NULL_SEMANTICS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query-null-matches-null-and-missing",
        docs=[{"_id": 1, "f": None}, {"_id": 2, "f": 10}, {"_id": 3}],
        command={
            "query": {"f": None},
            "update": {"$set": {"matched": True}},
            "sort": {"_id": 1},
        },
        expected={"value": Eq({"_id": 1, "f": None})},
        msg="query {f:null} matches docs where f is null AND where f is missing",
    ),
    CommandTestCase(
        "set-null-distinct-from-unset",
        docs=[{"_id": 1, "x": 10}],
        command={
            "query": {"_id": 1},
            "update": {"$set": {"x": None}},
            "new": True,
        },
        expected={"value": Eq({"_id": 1, "x": None})},
        msg="$set:{f:null} stores null (distinct from removing field)",
    ),
    CommandTestCase(
        "query-false-does-not-match-zero",
        docs=[{"_id": 1, "f": 0}, {"_id": 2, "f": False}],
        command={
            "query": {"f": False},
            "update": {"$set": {"matched": True}},
            "sort": {"_id": 1},
        },
        expected={"value": Eq({"_id": 2, "f": False})},
        msg="query {f:false} does NOT match document with f:0",
    ),
    CommandTestCase(
        "query-empty-string-does-not-match-null",
        docs=[{"_id": 1, "f": None}, {"_id": 2, "f": ""}],
        command={
            "query": {"f": ""},
            "update": {"$set": {"matched": True}},
            "sort": {"_id": 1},
        },
        expected={"value": Eq({"_id": 2, "f": ""})},
        msg='query {f:""} does NOT match document with f:null',
    ),
    CommandTestCase(
        "decimal128-query-match-and-roundtrip",
        docs=[{"_id": 1, "f": Decimal128("123.456")}],
        command={
            "query": {"f": Decimal128("123.456")},
            "update": {"$set": {"matched": True}},
        },
        expected={"value": Eq({"_id": 1, "f": Decimal128("123.456")})},
        msg="Decimal128 query matches and preserves type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_SEMANTICS_TESTS))
def test_findAndModify_data_types(database_client, collection, test):
    """Test findAndModify data type semantics."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = {"findAndModify": collection.name, **test.build_command(ctx)}
    result = execute_command(collection, command)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


@pytest.mark.parametrize(
    "stored,query_value",
    [
        pytest.param(1, 1, id="int32_matches_1"),
        pytest.param(1, Int64(1), id="int64_matches_1"),
        pytest.param(1, 1.0, id="double_matches_1"),
        pytest.param(1, Decimal128("1"), id="decimal_matches_1"),
        pytest.param(0, 0, id="int32_matches_0"),
        pytest.param(0, Int64(0), id="int64_matches_0"),
        pytest.param(0, 0.0, id="double_matches_0"),
        pytest.param(0, Decimal128("0"), id="decimal_matches_0"),
    ],
)
def test_findAndModify_numeric_equivalence(collection, stored, query_value):
    """Test numeric equivalence: different numeric types match the same stored value."""
    collection.insert_one({"_id": 1, "f": stored})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"f": query_value},
            "update": {"$set": {"matched": True}},
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "f": stored}, "lastErrorObject": {"n": 1}})


BSON_TYPE_VALUES = [
    pytest.param(BSON_TYPE_SAMPLES[BsonType.DOUBLE], id="double"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.STRING], id="string"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.OBJECT], id="object"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.ARRAY], id="array"),
    pytest.param(Binary(b"\x00\x01\x02", 128), id="binary"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.OBJECT_ID], id="objectid"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.BOOL], id="bool"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.DATE], id="date"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.NULL], id="null"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.REGEX], id="regex"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.INT], id="int32"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.TIMESTAMP], id="timestamp"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.LONG], id="int64"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.DECIMAL], id="decimal128"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.MIN_KEY], id="minkey"),
    pytest.param(BSON_TYPE_SAMPLES[BsonType.MAX_KEY], id="maxkey"),
]


@pytest.mark.parametrize("value", BSON_TYPE_VALUES)
def test_findAndModify_bson_type_query_match(collection, value):
    """Test findAndModify query equality match works for each BSON type."""
    collection.insert_one({"_id": 1, "f": value})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"f": value},
            "update": {"$set": {"matched": True}},
        },
    )
    assertSuccessPartial(result, {"value": {"_id": 1, "f": value}, "lastErrorObject": {"n": 1}})


@pytest.mark.parametrize("value", BSON_TYPE_VALUES)
def test_findAndModify_bson_type_set_roundtrip(collection, value):
    """Test findAndModify $set stores BSON type and round-trips it."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$set": {"f": value}},
            "new": True,
        },
    )
    assertSuccessPartial(
        result, {"value": {"_id": 1, "f": value}, "lastErrorObject": {"updatedExisting": True}}
    )


@pytest.mark.parametrize("value", BSON_TYPE_VALUES)
def test_findAndModify_bson_type_replacement_roundtrip(collection, value):
    """Test findAndModify replacement document preserves BSON type on round-trip."""
    collection.insert_one({"_id": 1, "f": "original"})
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"_id": 1, "f": value},
            "new": True,
        },
    )
    assertSuccessPartial(
        result, {"value": {"_id": 1, "f": value}, "lastErrorObject": {"updatedExisting": True}}
    )
