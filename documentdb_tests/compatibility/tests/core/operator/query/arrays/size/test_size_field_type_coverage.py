"""
Tests for $size field type coverage.

Covers non-array field types (silent skip), null field handling,
and missing field handling.
"""

from datetime import datetime

import pytest
from bson import Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    TS_EPOCH,
)

NON_ARRAY_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="string_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="$size on string field — no match, no error",
    ),
    QueryTestCase(
        id="int_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": 42}],
        expected=[],
        msg="$size on integer field — no match, no error",
    ),
    QueryTestCase(
        id="double_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": 3.14}],
        expected=[],
        msg="$size on double field — no match, no error",
    ),
    QueryTestCase(
        id="bool_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="$size on boolean field — no match, no error",
    ),
    QueryTestCase(
        id="object_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": {"x": 1}}],
        expected=[],
        msg="$size on object field — no match, no error",
    ),
    QueryTestCase(
        id="objectid_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": ObjectId()}],
        expected=[],
        msg="$size on ObjectId field — no match, no error",
    ),
    QueryTestCase(
        id="date_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": datetime(2020, 1, 1)}],
        expected=[],
        msg="$size on date field — no match, no error",
    ),
    QueryTestCase(
        id="bindata_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": Binary(b"\x01\x02")}],
        expected=[],
        msg="$size on BinData field — no match, no error",
    ),
    QueryTestCase(
        id="timestamp_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": TS_EPOCH}],
        expected=[],
        msg="$size on Timestamp field — no match, no error",
    ),
    QueryTestCase(
        id="long_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": Int64(100)}],
        expected=[],
        msg="$size on long field — no match, no error",
    ),
    QueryTestCase(
        id="decimal128_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": Decimal128("1.5")}],
        expected=[],
        msg="$size on Decimal128 field — no match, no error",
    ),
    QueryTestCase(
        id="regex_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": Regex(".*")}],
        expected=[],
        msg="$size on regex field — no match, no error",
    ),
    QueryTestCase(
        id="nan_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": FLOAT_NAN}],
        expected=[],
        msg="$size on NaN field — no match, no error",
    ),
    QueryTestCase(
        id="infinity_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": FLOAT_INFINITY}],
        expected=[],
        msg="$size on Infinity field — no match, no error",
    ),
    QueryTestCase(
        id="neg_infinity_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": FLOAT_NEGATIVE_INFINITY}],
        expected=[],
        msg="$size on -Infinity field — no match, no error",
    ),
    QueryTestCase(
        id="decimal128_nan_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": DECIMAL128_NAN}],
        expected=[],
        msg="$size on Decimal128 NaN field — no match, no error",
    ),
    QueryTestCase(
        id="decimal128_neg_infinity_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": DECIMAL128_NEGATIVE_INFINITY}],
        expected=[],
        msg="$size on Decimal128 -Infinity field — no match, no error",
    ),
    QueryTestCase(
        id="minkey_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": MinKey()}],
        expected=[],
        msg="$size on MinKey field — no match, no error",
    ),
    QueryTestCase(
        id="maxkey_field",
        filter={"a": {"$size": 1}},
        doc=[{"_id": 1, "a": MaxKey()}],
        expected=[],
        msg="$size on MaxKey field — no match, no error",
    ),
]

NULL_MISSING_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="null_field_size_0",
        filter={"a": {"$size": 0}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="$size 0 does NOT match null field",
    ),
    QueryTestCase(
        id="missing_field_size_0",
        filter={"a": {"$size": 0}},
        doc=[{"_id": 1, "b": 1}],
        expected=[],
        msg="$size 0 does NOT match missing field",
    ),
    QueryTestCase(
        id="empty_object_not_empty_array",
        filter={"a": {"$size": 0}},
        doc=[{"_id": 1, "a": {}}],
        expected=[],
        msg="$size 0 does NOT match empty object",
    ),
    QueryTestCase(
        id="empty_string_not_empty_array",
        filter={"a": {"$size": 0}},
        doc=[{"_id": 1, "a": ""}],
        expected=[],
        msg="$size 0 does NOT match empty string",
    ),
]

ALL_TESTS = NON_ARRAY_FIELD_TESTS + NULL_MISSING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_size_field_type_coverage(collection, test):
    """Parametrized test for $size field type coverage."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
