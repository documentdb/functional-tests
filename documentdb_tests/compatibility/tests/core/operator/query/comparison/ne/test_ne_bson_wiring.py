"""
Tests for $ne BSON type wiring.

Covers all major BSON types, numeric cross-type equivalence,
BSON type distinction (bool vs numeric), negative zero handling,
boundary values, special float values (NaN, Infinity), type mismatch,
and result set edge cases.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

BSON_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double",
        filter={"a": {"$ne": 3.14}},
        doc=[{"_id": 1, "a": 3.14}, {"_id": 2, "a": 2.71}],
        expected=[{"_id": 2, "a": 2.71}],
        msg="$ne with double excludes matching document",
    ),
    QueryTestCase(
        id="int32",
        filter={"a": {"$ne": 42}},
        doc=[{"_id": 1, "a": 42}, {"_id": 2, "a": 99}],
        expected=[{"_id": 2, "a": 99}],
        msg="$ne with int32 excludes matching document",
    ),
    QueryTestCase(
        id="string",
        filter={"a": {"$ne": "hello"}},
        doc=[{"_id": 1, "a": "hello"}, {"_id": 2, "a": "world"}],
        expected=[{"_id": 2, "a": "world"}],
        msg="$ne with string excludes matching document",
    ),
    QueryTestCase(
        id="boolean_true",
        filter={"a": {"$ne": True}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": False}],
        expected=[{"_id": 2, "a": False}],
        msg="$ne with boolean true excludes matching document",
    ),
    QueryTestCase(
        id="boolean_false",
        filter={"a": {"$ne": False}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": True}],
        expected=[{"_id": 2, "a": True}],
        msg="$ne with boolean false excludes matching document",
    ),
    QueryTestCase(
        id="null",
        filter={"a": {"$ne": None}},
        doc=[{"_id": 1, "a": None}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$ne with null excludes matching document",
    ),
    QueryTestCase(
        id="missing_field",
        filter={"a": {"$ne": None}},
        doc=[{"_id": 1}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$ne with null excludes document with missing field",
    ),
    QueryTestCase(
        id="object",
        filter={"a": {"$ne": {"x": 1}}},
        doc=[{"_id": 1, "a": {"x": 1}}, {"_id": 2, "a": {"x": 2}}],
        expected=[{"_id": 2, "a": {"x": 2}}],
        msg="$ne with object excludes matching document",
    ),
    QueryTestCase(
        id="array",
        filter={"a": {"$ne": [1, 2]}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [3, 4]}],
        expected=[{"_id": 2, "a": [3, 4]}],
        msg="$ne with array excludes matching document",
    ),
    QueryTestCase(
        id="bindata",
        filter={"a": {"$ne": Binary(b"\x01\x02")}},
        doc=[{"_id": 1, "a": Binary(b"\x01\x02")}, {"_id": 2, "a": Binary(b"\x03")}],
        expected=[{"_id": 2, "a": b"\x03"}],
        msg="$ne with BinData excludes matching document",
    ),
    QueryTestCase(
        id="objectid",
        filter={"a": {"$ne": ObjectId("000000000000000000000001")}},
        doc=[
            {"_id": 1, "a": ObjectId("000000000000000000000001")},
            {"_id": 2, "a": ObjectId("000000000000000000000002")},
        ],
        expected=[{"_id": 2, "a": ObjectId("000000000000000000000002")}],
        msg="$ne with ObjectId excludes matching document",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"a": {"$ne": Timestamp(1000, 1)}},
        doc=[{"_id": 1, "a": Timestamp(1000, 1)}, {"_id": 2, "a": Timestamp(2000, 1)}],
        expected=[{"_id": 2, "a": Timestamp(2000, 1)}],
        msg="$ne with Timestamp excludes matching document",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$ne": Decimal128("1.5")}},
        doc=[{"_id": 1, "a": Decimal128("1.5")}, {"_id": 2, "a": Decimal128("2.5")}],
        expected=[{"_id": 2, "a": Decimal128("2.5")}],
        msg="$ne with Decimal128 excludes matching document",
    ),
    QueryTestCase(
        id="int64",
        filter={"a": {"$ne": Int64(9999999999)}},
        doc=[{"_id": 1, "a": Int64(9999999999)}, {"_id": 2, "a": Int64(1)}],
        expected=[{"_id": 2, "a": Int64(1)}],
        msg="$ne with Int64 excludes matching document",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$ne": MinKey()}},
        doc=[{"_id": 1, "a": MinKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$ne with MinKey excludes matching document",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$ne": MaxKey()}},
        doc=[{"_id": 1, "a": MaxKey()}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$ne with MaxKey excludes matching document",
    ),
    QueryTestCase(
        id="datetime",
        filter={"a": {"$ne": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        doc=[
            {"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 2, "a": datetime(2025, 1, 1, tzinfo=timezone.utc)}],
        msg="$ne with datetime excludes matching document",
    ),
]

NUMERIC_CROSS_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int_eq_long",
        filter={"a": {"$ne": 42}},
        doc=[{"_id": 1, "a": Int64(42)}, {"_id": 2, "a": Int64(99)}],
        expected=[{"_id": 2, "a": Int64(99)}],
        msg="$ne int filters out equivalent long value",
    ),
    QueryTestCase(
        id="int_eq_double",
        filter={"a": {"$ne": 10}},
        doc=[{"_id": 1, "a": 10.0}, {"_id": 2, "a": 11.0}],
        expected=[{"_id": 2, "a": 11.0}],
        msg="$ne int filters out equivalent double value",
    ),
    QueryTestCase(
        id="int_eq_decimal128",
        filter={"a": {"$ne": 5}},
        doc=[{"_id": 1, "a": Decimal128("5")}, {"_id": 2, "a": Decimal128("6")}],
        expected=[{"_id": 2, "a": Decimal128("6")}],
        msg="$ne int filters out equivalent Decimal128 value",
    ),
    QueryTestCase(
        id="long_eq_double",
        filter={"a": {"$ne": Int64(100)}},
        doc=[{"_id": 1, "a": 100.0}, {"_id": 2, "a": 200.0}],
        expected=[{"_id": 2, "a": 200.0}],
        msg="$ne long filters out equivalent double value",
    ),
    QueryTestCase(
        id="long_eq_decimal128",
        filter={"a": {"$ne": Int64(7)}},
        doc=[{"_id": 1, "a": Decimal128("7")}, {"_id": 2, "a": Decimal128("8")}],
        expected=[{"_id": 2, "a": Decimal128("8")}],
        msg="$ne long filters out equivalent Decimal128 value",
    ),
    QueryTestCase(
        id="double_eq_decimal128",
        filter={"a": {"$ne": 3.5}},
        doc=[{"_id": 1, "a": Decimal128("3.5")}, {"_id": 2, "a": Decimal128("4.5")}],
        expected=[{"_id": 2, "a": Decimal128("4.5")}],
        msg="$ne double filters out equivalent Decimal128 value",
    ),
]

TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_ne_zero",
        filter={"a": {"$ne": False}},
        doc=[{"_id": 1, "a": False}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$ne false does not match integer 0 — different BSON types",
    ),
    QueryTestCase(
        id="true_ne_one",
        filter={"a": {"$ne": True}},
        doc=[{"_id": 1, "a": True}, {"_id": 2, "a": 1}],
        expected=[{"_id": 2, "a": 1}],
        msg="$ne true does not match integer 1 — different BSON types",
    ),
]

NEGATIVE_ZERO_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double_neg_zero_eq_zero",
        filter={"a": {"$ne": DOUBLE_NEGATIVE_ZERO}},
        doc=[{"_id": 1, "a": DOUBLE_ZERO}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg="$ne -0.0 filters out 0.0 — negative zero equals positive zero",
    ),
    QueryTestCase(
        id="decimal128_neg_zero_eq_zero",
        filter={"a": {"$ne": DECIMAL128_NEGATIVE_ZERO}},
        doc=[{"_id": 1, "a": DECIMAL128_ZERO}, {"_id": 2, "a": Decimal128("1")}],
        expected=[{"_id": 2, "a": Decimal128("1")}],
        msg="$ne Decimal128('-0') filters out Decimal128('0') — negative zero equals positive zero",
    ),
]

BOUNDARY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_max",
        filter={"a": {"$ne": INT32_MAX}},
        doc=[{"_id": 1, "a": INT32_MAX}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$ne with INT32_MAX excludes matching document",
    ),
    QueryTestCase(
        id="int32_min",
        filter={"a": {"$ne": INT32_MIN}},
        doc=[{"_id": 1, "a": INT32_MIN}, {"_id": 2, "a": 0}],
        expected=[{"_id": 2, "a": 0}],
        msg="$ne with INT32_MIN excludes matching document",
    ),
    QueryTestCase(
        id="int64_max",
        filter={"a": {"$ne": INT64_MAX}},
        doc=[{"_id": 1, "a": INT64_MAX}, {"_id": 2, "a": Int64(0)}],
        expected=[{"_id": 2, "a": Int64(0)}],
        msg="$ne with INT64_MAX excludes matching document",
    ),
    QueryTestCase(
        id="int64_min",
        filter={"a": {"$ne": INT64_MIN}},
        doc=[{"_id": 1, "a": INT64_MIN}, {"_id": 2, "a": Int64(0)}],
        expected=[{"_id": 2, "a": Int64(0)}],
        msg="$ne with INT64_MIN excludes matching document",
    ),
]


SPECIAL_FLOAT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="nan_eq_nan",
        filter={"a": {"$ne": float("nan")}},
        doc=[{"_id": 1, "a": float("nan")}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg=(
            "$ne NaN filters out NaN — database treats NaN == NaN"
            " as true, ignoring IEEE 754 where NaN != NaN"
        ),
    ),
    QueryTestCase(
        id="infinity",
        filter={"a": {"$ne": float("inf")}},
        doc=[{"_id": 1, "a": float("inf")}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg="$ne Infinity excludes matching document",
    ),
    QueryTestCase(
        id="negative_infinity",
        filter={"a": {"$ne": float("-inf")}},
        doc=[{"_id": 1, "a": float("-inf")}, {"_id": 2, "a": 1.0}],
        expected=[{"_id": 2, "a": 1.0}],
        msg="$ne -Infinity excludes matching document",
    ),
]

TYPE_MISMATCH_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_ne_int",
        filter={"a": {"$ne": "1"}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": "1"}],
        expected=[{"_id": 1, "a": 1}],
        msg="$ne string '1' does not match integer 1 — different types are not equal",
    ),
]

RESULT_SET_EDGE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="all_docs_excluded",
        filter={"a": {"$ne": 1}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 1}],
        expected=[],
        msg="$ne excludes all documents when all match",
    ),
    QueryTestCase(
        id="no_docs_excluded",
        filter={"a": {"$ne": 99}},
        doc=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 2}],
        msg="$ne returns all documents when none match the filter value",
    ),
]

ALL_TESTS = (
    BSON_TYPE_TESTS
    + NUMERIC_CROSS_TYPE_TESTS
    + TYPE_DISTINCTION_TESTS
    + NEGATIVE_ZERO_TESTS
    + BOUNDARY_TESTS
    + SPECIAL_FLOAT_TESTS
    + TYPE_MISMATCH_TESTS
    + RESULT_SET_EDGE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_bson_wiring(collection, test):
    """Parametrized test for $ne BSON type wiring."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
