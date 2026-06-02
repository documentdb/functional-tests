"""Tests for $[] positional-all with data type coverage.

Covers: all BSON types, numeric equivalence, BSON type distinction,
and mixed type arrays.
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
class PositionalAllTypeTest(BaseTestCase):
    """Test case for $[] with data types."""

    setup_docs: Any = None
    query: Any = None
    update: Any = None


DATA_TYPE_TESTS: list[PositionalAllTypeTest] = [
    PositionalAllTypeTest(
        "double",
        setup_docs=[{"_id": 1, "arr": [1.1, 2.2, 3.3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0.0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all double elements",
    ),
    PositionalAllTypeTest(
        "int32",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all int32 elements",
    ),
    PositionalAllTypeTest(
        "int64",
        setup_docs=[{"_id": 1, "arr": [Int64(10), Int64(20)]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": Int64(0)}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all int64 elements",
    ),
    PositionalAllTypeTest(
        "decimal128",
        setup_docs=[{"_id": 1, "arr": [Decimal128("1.1"), Decimal128("2.2")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": Decimal128("0")}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all decimal128 elements",
    ),
    PositionalAllTypeTest(
        "string",
        setup_docs=[{"_id": 1, "arr": ["a", "b", "c"]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "x"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all string elements",
    ),
    PositionalAllTypeTest(
        "bool",
        setup_docs=[{"_id": 1, "arr": [True, False, True]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": False}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all bool elements",
    ),
    PositionalAllTypeTest(
        "date",
        setup_docs=[{"_id": 1, "arr": [DATE_EPOCH, DATE_EPOCH]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all date elements",
    ),
    PositionalAllTypeTest(
        "null",
        setup_docs=[{"_id": 1, "arr": [None, None]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all null elements",
    ),
    PositionalAllTypeTest(
        "object",
        setup_docs=[{"_id": 1, "arr": [{"k": 1}, {"k": 2}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": {"k": 0}}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all object elements",
    ),
    PositionalAllTypeTest(
        "objectid",
        setup_docs=[{"_id": 1, "arr": [OID_EPOCH, ObjectId("111111111111111111111111")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all ObjectId elements",
    ),
    PositionalAllTypeTest(
        "bindata",
        setup_docs=[{"_id": 1, "arr": [Binary(b"\x01"), Binary(b"\x02")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": Binary(b"\x00")}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all binary data elements",
    ),
    PositionalAllTypeTest(
        "timestamp",
        setup_docs=[{"_id": 1, "arr": [TS_EPOCH, Timestamp(100, 1)]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": Timestamp(999, 1)}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all timestamp elements",
    ),
    PositionalAllTypeTest(
        "minkey",
        setup_docs=[{"_id": 1, "arr": [MinKey(), MinKey()]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all MinKey elements",
    ),
    PositionalAllTypeTest(
        "maxkey",
        setup_docs=[{"_id": 1, "arr": [MaxKey(), MaxKey()]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all MaxKey elements",
    ),
    PositionalAllTypeTest(
        "regex",
        setup_docs=[{"_id": 1, "arr": [Regex("^a", "i"), Regex("^b", "")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all regex elements",
    ),
    PositionalAllTypeTest(
        "javascript",
        setup_docs=[{"_id": 1, "arr": [Code("function(){}"), Code("var x=1")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": "replaced"}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all javascript elements",
    ),
]


# --- Numeric Equivalence ---

NUMERIC_EQUIVALENCE_TESTS: list[PositionalAllTypeTest] = [
    PositionalAllTypeTest(
        "mixed_numeric_types_all_updated",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0, Decimal128("4")]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": 0}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] should update all elements regardless of numeric subtype",
    ),
    PositionalAllTypeTest(
        "inc_mixed_numeric",
        setup_docs=[{"_id": 1, "arr": [1, Int64(2), 3.0]}],
        query={"_id": 1},
        update={"$inc": {"arr.$[]": 10}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $inc on mixed numeric types should increment all",
    ),
]


# --- Set all to null ---

SET_NULL_TESTS: list[PositionalAllTypeTest] = [
    PositionalAllTypeTest(
        "set_all_to_null",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$set": {"arr.$[]": None}},
        expected={"n": 1, "nModified": 1, "ok": 1.0},
        msg="$[] with $set value of null should update all elements to null",
    ),
]


ALL_TESTS = DATA_TYPE_TESTS + NUMERIC_EQUIVALENCE_TESTS + SET_NULL_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_positional_all_data_types(collection, test: PositionalAllTypeTest):
    """Test $[] positional-all with various BSON data types."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    command = {
        "update": collection.name,
        "updates": [{"q": test.query, "u": test.update}],
    }
    result = execute_command(collection, command)
    assertSuccess(result, test.expected, msg=test.msg, raw_res=True)
