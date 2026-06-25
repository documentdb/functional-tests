"""Tests for find filter matching across BSON types and numeric equivalence."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_OID = ObjectId()
_DT = datetime(2024, 1, 1, tzinfo=timezone.utc)
_TS = Timestamp(1000, 1)
_CODE = Code("function(){}")


# Property [BSON Type Matching]: find filter matches documents by exact BSON type value
# for all non-deprecated types.
FIND_BSON_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "double",
        docs=[{"_id": 1, "a": 3.14}, {"_id": 2, "a": 2.71}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 3.14}},
        expected=[{"_id": 1, "a": 3.14}],
        msg="find should match double.",
    ),
    CommandTestCase(
        "int32",
        docs=[{"_id": 1, "a": 42}, {"_id": 2, "a": 99}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 42}},
        expected=[{"_id": 1, "a": 42}],
        msg="find should match int32.",
    ),
    CommandTestCase(
        "int64",
        docs=[{"_id": 1, "a": Int64(9_000_000_000)}, {"_id": 2, "a": Int64(1)}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": Int64(9_000_000_000)}},
        expected=[{"_id": 1, "a": Int64(9_000_000_000)}],
        msg="find should match Int64.",
    ),
    CommandTestCase(
        "decimal128",
        docs=[{"_id": 1, "a": Decimal128("1.5")}, {"_id": 2, "a": Decimal128("2.5")}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": Decimal128("1.5")}},
        expected=[{"_id": 1, "a": Decimal128("1.5")}],
        msg="find should match Decimal128.",
    ),
    CommandTestCase(
        "string",
        docs=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": "world"}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": "hello"}},
        expected=[{"_id": 1, "a": "hello"}],
        msg="find should match string.",
    ),
    CommandTestCase(
        "boolean_true",
        docs=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": True}},
        expected=[{"_id": 1, "a": True}],
        msg="find should match boolean true.",
    ),
    CommandTestCase(
        "boolean_false",
        docs=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": False}},
        expected=[{"_id": 2, "a": False}],
        msg="find should match boolean false.",
    ),
    CommandTestCase(
        "embedded_document",
        docs=[{"_id": 1, "a": {"x": 1}}, {"_id": 2, "a": {"x": 2}}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": {"x": 1}}},
        expected=[{"_id": 1, "a": {"x": 1}}],
        msg="find should match embedded doc.",
    ),
    CommandTestCase(
        "array",
        docs=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": [1, 2, 3]}},
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="find should match array exactly.",
    ),
    CommandTestCase(
        "binary",
        docs=[{"_id": 1, "a": Binary(b"data")}, {"_id": 2, "a": Binary(b"other")}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": Binary(b"data")}},
        expected=[{"_id": 1, "a": b"data"}],
        msg="find should match Binary.",
    ),
    CommandTestCase(
        "objectid",
        docs=[{"_id": 1, "a": _OID}, {"_id": 2, "a": ObjectId()}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": _OID}},
        expected=[{"_id": 1, "a": _OID}],
        msg="find should match ObjectId.",
    ),
    CommandTestCase(
        "datetime",
        docs=[{"_id": 1, "a": _DT}, {"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": _DT}},
        expected=[{"_id": 1, "a": _DT}],
        msg="find should match datetime.",
    ),
    CommandTestCase(
        "null",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": None}},
        expected=[{"_id": 1, "a": None}],
        msg="find should match null values.",
    ),
    CommandTestCase(
        "timestamp",
        docs=[{"_id": 1, "a": _TS}, {"_id": 2, "a": Timestamp(2000, 1)}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": _TS}},
        expected=[{"_id": 1, "a": _TS}],
        msg="find should match Timestamp.",
    ),
    CommandTestCase(
        "code",
        docs=[{"_id": 1, "a": _CODE}, {"_id": 2, "a": Code("x")}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": _CODE}},
        expected=[{"_id": 1, "a": _CODE}],
        msg="find should match Code.",
    ),
    CommandTestCase(
        "minkey",
        docs=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 0}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": MinKey()}},
        expected=[{"_id": 1, "a": MinKey()}],
        msg="find should match MinKey.",
    ),
    CommandTestCase(
        "maxkey",
        docs=[{"_id": 1, "a": MaxKey()}, {"_id": 2, "a": 0}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": MaxKey()}},
        expected=[{"_id": 1, "a": MaxKey()}],
        msg="find should match MaxKey.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_BSON_TYPE_TESTS))
def test_find_bson_type_matching(database_client, collection, test):
    """Test find filter matches each BSON type."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
    )


# Property [Null and Missing]: find filter {field: null} matches both null values
# and documents where the field is absent.
FIND_NULL_MISSING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_matches_missing",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}, {"_id": 3}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": None}, "sort": {"_id": 1}},
        expected=[{"_id": 1, "a": None}, {"_id": 3}],
        msg="find should match both null and missing fields with {field: null}.",
    ),
    CommandTestCase(
        "exists_true_excludes_missing",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}, {"_id": 3}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a": {"$exists": True}},
            "sort": {"_id": 1},
        },
        expected=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        msg="find should match null but not missing with $exists: true.",
    ),
    CommandTestCase(
        "exists_false_matches_only_missing",
        docs=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}, {"_id": 3}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": {"$exists": False}}},
        expected=[{"_id": 3}],
        msg="find should match only missing field with $exists: false.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_NULL_MISSING_TESTS))
def test_find_null_missing(database_client, collection, test):
    """Test find filter null and missing field behavior."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg)


# Property [Special Numeric Values]: find filter matches NaN and Infinity values
# across float and Decimal128 types.
FIND_SPECIAL_NUMERIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "float_infinity",
        docs=[{"_id": 1, "a": float("inf")}, {"_id": 2, "a": 1.0}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": float("inf")}},
        expected=[{"_id": 1, "a": float("inf")}],
        msg="find should match float Infinity.",
    ),
    CommandTestCase(
        "float_negative_infinity",
        docs=[{"_id": 1, "a": float("-inf")}, {"_id": 2, "a": 1.0}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": float("-inf")}},
        expected=[{"_id": 1, "a": float("-inf")}],
        msg="find should match float -Infinity.",
    ),
    CommandTestCase(
        "decimal128_nan",
        docs=[{"_id": 1, "a": Decimal128("NaN")}, {"_id": 2, "a": Decimal128("1")}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": Decimal128("NaN")}},
        expected=[{"_id": 1, "a": Decimal128("NaN")}],
        msg="find should match Decimal128 NaN.",
    ),
    CommandTestCase(
        "decimal128_infinity",
        docs=[{"_id": 1, "a": Decimal128("Infinity")}, {"_id": 2, "a": Decimal128("1")}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": Decimal128("Infinity")}},
        expected=[{"_id": 1, "a": Decimal128("Infinity")}],
        msg="find should match Decimal128 Infinity.",
    ),
    CommandTestCase(
        "decimal128_negative_infinity",
        docs=[{"_id": 1, "a": Decimal128("-Infinity")}, {"_id": 2, "a": Decimal128("1")}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": Decimal128("-Infinity")}},
        expected=[{"_id": 1, "a": Decimal128("-Infinity")}],
        msg="find should match Decimal128 -Infinity.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_SPECIAL_NUMERIC_TESTS))
def test_find_special_numeric(database_client, collection, test):
    """Test find filter special numeric value matching."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg)


def test_find_matches_float_nan(collection):
    """Test filter matches float NaN value."""
    collection.insert_many([{"_id": 1, "a": float("nan")}, {"_id": 2, "a": 1.0}])
    result = execute_command(collection, {"find": collection.name, "filter": {"a": float("nan")}})
    assertSuccessNaN(result, [{"_id": 1, "a": float("nan")}], msg="find should match float NaN.")


# Property [Numeric Equivalence]: find filter treats numerically equivalent values
# across int32, int64, double, and Decimal128 as equal, but distinguishes bool from int.
FIND_NUMERIC_EQUIVALENCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "equivalence_one",
        docs=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": Int64(1)},
            {"_id": 3, "a": 1.0},
            {"_id": 4, "a": Decimal128("1")},
            {"_id": 5, "a": 2},
        ],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 1}, "sort": {"_id": 1}},
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 2, "a": Int64(1)},
            {"_id": 3, "a": 1.0},
            {"_id": 4, "a": Decimal128("1")},
        ],
        msg="find should treat numerically equivalent values as equal.",
    ),
    CommandTestCase(
        "equivalence_zero",
        docs=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": Int64(0)},
            {"_id": 3, "a": 0.0},
            {"_id": 4, "a": Decimal128("0")},
            {"_id": 5, "a": 1},
        ],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": 0}, "sort": {"_id": 1}},
        expected=[
            {"_id": 1, "a": 0},
            {"_id": 2, "a": Int64(0)},
            {"_id": 3, "a": 0.0},
            {"_id": 4, "a": Decimal128("0")},
        ],
        msg="find should treat numerically equivalent zero values as equal.",
    ),
    CommandTestCase(
        "boolean_false_not_equal_zero",
        docs=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": False}},
        expected=[{"_id": 1, "a": False}],
        msg="find should not match int 0 with boolean false.",
    ),
    CommandTestCase(
        "boolean_true_not_equal_one",
        docs=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        command=lambda ctx: {"find": ctx.collection, "filter": {"a": True}},
        expected=[{"_id": 1, "a": True}],
        msg="find should not match int 1 with boolean true.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIND_NUMERIC_EQUIVALENCE_TESTS))
def test_find_numeric_equivalence(database_client, collection, test):
    """Test find filter numeric equivalence across BSON types."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, expected=test.build_expected(ctx), msg=test.msg)
