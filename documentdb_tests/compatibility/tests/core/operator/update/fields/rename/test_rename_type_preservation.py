"""
BSON type preservation tests for $rename update operator.

Tests that $rename preserves all BSON types when renaming fields.
"""

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
    OID_EPOCH,
    TS_EPOCH,
)

TYPE_PRESERVATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32",
        setup_docs=[{"_id": 1, "old": 42}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": 42},
        msg="$rename should preserve int32 value",
    ),
    UpdateTestCase(
        "int64",
        setup_docs=[{"_id": 1, "old": INT64_MAX}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": INT64_MAX},
        msg="$rename should preserve int64 value",
    ),
    UpdateTestCase(
        "double",
        setup_docs=[{"_id": 1, "old": 3.14}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": 3.14},
        msg="$rename should preserve double value",
    ),
    UpdateTestCase(
        "decimal128",
        setup_docs=[{"_id": 1, "old": Decimal128("123.456")}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": Decimal128("123.456")},
        msg="$rename should preserve decimal128 value",
    ),
    UpdateTestCase(
        "string",
        setup_docs=[{"_id": 1, "old": "hello world"}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": "hello world"},
        msg="$rename should preserve string value",
    ),
    UpdateTestCase(
        "bool_true",
        setup_docs=[{"_id": 1, "old": True}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": True},
        msg="$rename should preserve bool true",
    ),
    UpdateTestCase(
        "bool_false",
        setup_docs=[{"_id": 1, "old": False}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": False},
        msg="$rename should preserve bool false",
    ),
    UpdateTestCase(
        "date",
        setup_docs=[{"_id": 1, "old": DATE_EPOCH}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": DATE_EPOCH},
        msg="$rename should preserve date value",
    ),
    UpdateTestCase(
        "null",
        setup_docs=[{"_id": 1, "old": None}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": None},
        msg="$rename should preserve null value",
    ),
    UpdateTestCase(
        "object",
        setup_docs=[{"_id": 1, "old": {"nested": {"deep": 1}}}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": {"nested": {"deep": 1}}},
        msg="$rename should preserve nested object structure",
    ),
    UpdateTestCase(
        "array",
        setup_docs=[{"_id": 1, "old": [1, "two", {"three": 3}]}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": [1, "two", {"three": 3}]},
        msg="$rename should preserve array elements and order",
    ),
    UpdateTestCase(
        "bindata",
        setup_docs=[{"_id": 1, "old": Binary(b"\x00\x01\x02")}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": b"\x00\x01\x02"},
        msg="$rename should preserve binData value",
    ),
    UpdateTestCase(
        "objectid",
        setup_docs=[{"_id": 1, "old": OID_EPOCH}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": OID_EPOCH},
        msg="$rename should preserve ObjectId value",
    ),
    UpdateTestCase(
        "regex",
        setup_docs=[{"_id": 1, "old": Regex("^abc", "i")}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": Regex("^abc", "i")},
        msg="$rename should preserve regex pattern and flags",
    ),
    UpdateTestCase(
        "javascript",
        setup_docs=[{"_id": 1, "old": Code("function(){}")}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": Code("function(){}")},
        msg="$rename should preserve JavaScript code",
    ),
    UpdateTestCase(
        "timestamp",
        setup_docs=[{"_id": 1, "old": TS_EPOCH}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": TS_EPOCH},
        msg="$rename should preserve Timestamp value",
    ),
    UpdateTestCase(
        "minkey",
        setup_docs=[{"_id": 1, "old": MinKey()}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": MinKey()},
        msg="$rename should preserve MinKey value",
    ),
    UpdateTestCase(
        "maxkey",
        setup_docs=[{"_id": 1, "old": MaxKey()}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": MaxKey()},
        msg="$rename should preserve MaxKey value",
    ),
]

SPECIAL_VALUE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "double_negative_zero",
        setup_docs=[{"_id": 1, "old": DOUBLE_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": DOUBLE_NEGATIVE_ZERO},
        msg="$rename should preserve double -0.0",
    ),
    UpdateTestCase(
        "decimal128_negative_zero",
        setup_docs=[{"_id": 1, "old": DECIMAL128_NEGATIVE_ZERO}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": DECIMAL128_NEGATIVE_ZERO},
        msg="$rename should preserve Decimal128 -0",
    ),
    UpdateTestCase(
        "decimal128_trailing_zeros",
        setup_docs=[{"_id": 1, "old": DECIMAL128_MANY_TRAILING_ZEROS}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": DECIMAL128_MANY_TRAILING_ZEROS},
        msg="$rename should preserve Decimal128 trailing zeros",
    ),
    UpdateTestCase(
        "float_infinity",
        setup_docs=[{"_id": 1, "old": FLOAT_INFINITY}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": FLOAT_INFINITY},
        msg="$rename should preserve Infinity",
    ),
    UpdateTestCase(
        "float_negative_infinity",
        setup_docs=[{"_id": 1, "old": FLOAT_NEGATIVE_INFINITY}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": FLOAT_NEGATIVE_INFINITY},
        msg="$rename should preserve negative Infinity",
    ),
    UpdateTestCase(
        "code_with_scope",
        setup_docs=[{"_id": 1, "old": Code("function(){}", {"x": 1})}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": Code("function(){}", {"x": 1})},
        msg="$rename should preserve Code with scope",
    ),
    UpdateTestCase(
        "empty_string_value",
        setup_docs=[{"_id": 1, "old": ""}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": ""},
        msg="$rename should preserve empty string value",
    ),
    UpdateTestCase(
        "empty_array_value",
        setup_docs=[{"_id": 1, "old": []}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": []},
        msg="$rename should preserve empty array value",
    ),
    UpdateTestCase(
        "empty_object_value",
        setup_docs=[{"_id": 1, "old": {}}],
        query={"_id": 1},
        update={"$rename": {"old": "new"}},
        expected={"_id": 1, "new": {}},
        msg="$rename should preserve empty object value",
    ),
]


ALL_TESTS = TYPE_PRESERVATION_TESTS + SPECIAL_VALUE_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_rename_type_preservation(collection, test: UpdateTestCase):
    """Test $rename preserves BSON types."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [test.expected], msg=test.msg)


def test_rename_preserves_nan(collection):
    """Test $rename preserves NaN value."""
    collection.insert_one({"_id": 1, "old": FLOAT_NAN})

    update = {"$rename": {"old": "new"}}
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccessNaN(result, [{"_id": 1, "new": FLOAT_NAN}], msg="$rename should preserve NaN")
