"""Tests for $[<identifier>] with data type coverage.

Covers: arrayFilters matching each BSON type, and type coercion behavior.
"""

from dataclasses import dataclass
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase
from documentdb_tests.framework.test_constants import DATE_EPOCH, OID_EPOCH, TS_EPOCH


@dataclass(frozen=True)
class FilteredTypeTest(BaseTestCase):
    """Test case for $[<identifier>] with data types."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None
    array_filters: Any = None


DATA_TYPE_FILTER_TESTS: list[FilteredTypeTest] = [
    FilteredTypeTest(
        "double",
        setup_docs=[{"_id": 1, "arr": [1.5, 2.5, 3.5]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99.9}},
        array_filters=[{"elem": {"$gt": 2.0}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update double elements",
    ),
    FilteredTypeTest(
        "int32",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3, 4]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gte": 3}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update int32 elements",
    ),
    FilteredTypeTest(
        "int64",
        setup_docs=[{"_id": 1, "arr": [Int64(10), Int64(20), Int64(30)]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": Int64(99)}},
        array_filters=[{"elem": {"$gt": Int64(15)}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update int64 elements",
    ),
    FilteredTypeTest(
        "decimal128",
        setup_docs=[{"_id": 1, "arr": [Decimal128("1"), Decimal128("2"), Decimal128("3")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": Decimal128("99")}},
        array_filters=[{"elem": {"$gte": Decimal128("2")}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update decimal128 elements",
    ),
    FilteredTypeTest(
        "string",
        setup_docs=[{"_id": 1, "arr": ["apple", "banana", "cherry"]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": "banana"}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update string elements",
    ),
    FilteredTypeTest(
        "bool",
        setup_docs=[{"_id": 1, "arr": [True, False, True]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": False}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update bool elements",
    ),
    FilteredTypeTest(
        "null",
        setup_docs=[{"_id": 1, "arr": [1, None, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": None}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update null elements",
    ),
    FilteredTypeTest(
        "objectid",
        setup_docs=[{"_id": 1, "arr": [OID_EPOCH, ObjectId("111111111111111111111111")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": OID_EPOCH}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update ObjectId elements",
    ),
    FilteredTypeTest(
        "date",
        setup_docs=[{"_id": 1, "arr": [DATE_EPOCH, DATE_EPOCH]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": DATE_EPOCH}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update date elements",
    ),
    FilteredTypeTest(
        "object",
        setup_docs=[{"_id": 1, "arr": [{"k": 1}, {"k": 2}, {"k": 3}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem].k": 99}},
        array_filters=[{"elem.k": {"$gte": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update object elements",
    ),
    FilteredTypeTest(
        "bindata",
        setup_docs=[{"_id": 1, "arr": [Binary(b"\x01"), Binary(b"\x02"), Binary(b"\x03")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": Binary(b"\xff")}},
        array_filters=[{"elem": Binary(b"\x02")}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update binary data elements",
    ),
    FilteredTypeTest(
        "timestamp",
        setup_docs=[{"_id": 1, "arr": [TS_EPOCH, Timestamp(100, 1), Timestamp(200, 1)]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": Timestamp(999, 1)}},
        array_filters=[{"elem": {"$gt": TS_EPOCH}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update timestamp elements",
    ),
    FilteredTypeTest(
        "minkey",
        setup_docs=[{"_id": 1, "arr": [MinKey(), 1, 2]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": MinKey()}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update MinKey elements",
    ),
    FilteredTypeTest(
        "maxkey",
        setup_docs=[{"_id": 1, "arr": [1, 2, MaxKey()]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": MaxKey()}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update MaxKey elements",
    ),
    FilteredTypeTest(
        "regex",
        setup_docs=[{"_id": 1, "arr": [Regex("^a", "i"), Regex("^b", "")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": Regex("^a", "i")}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update regex elements",
    ),
    FilteredTypeTest(
        "javascript",
        setup_docs=[{"_id": 1, "arr": [Code("function(){}"), Code("var x=1")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": "replaced"}},
        array_filters=[{"elem": Code("var x=1")}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] should filter and update javascript elements",
    ),
]


# --- Type Coercion in arrayFilters ---

TYPE_COERCION_TESTS: list[FilteredTypeTest] = [
    FilteredTypeTest(
        "mixed_numeric_gt",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0, Decimal128("4")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": {"$gt": 2}}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with $gt on mixed numeric types should compare correctly",
    ),
    FilteredTypeTest(
        "string_does_not_match_numeric",
        setup_docs=[{"_id": 1, "arr": [5, "5", 10]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": "5"}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with string '5' should match string not numeric 5 (type matters)",
    ),
    FilteredTypeTest(
        "numeric_does_not_match_string",
        setup_docs=[{"_id": 1, "arr": [5, "5", 10]}],
        query={"_id": 1},
        update={"$set": {"arr.$[elem]": 99}},
        array_filters=[{"elem": 5}],
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[<id>] with numeric 5 should match numeric not string '5' (type matters)",
    ),
]


ALL_TESTS = DATA_TYPE_FILTER_TESTS + TYPE_COERCION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_filtered_data_types(collection, test: FilteredTypeTest):
    """Test $[<identifier>] with various BSON data types in arrayFilters."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update, "arrayFilters": test.array_filters}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
