"""
Tests for $nor query operator data type coverage.

Covers BSON type matching, numeric equivalence across types,
and BSON type distinction (false vs 0, true vs 1, null vs missing).
"""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

BSON_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="double",
        filter={"$nor": [{"val": 3.14}]},
        doc=[{"_id": 1, "val": 3.14}, {"_id": 2, "val": 2.0}],
        expected=[{"_id": 2, "val": 2.0}],
        msg="$nor should exclude docs matching double value",
    ),
    QueryTestCase(
        id="string",
        filter={"$nor": [{"val": "hello"}]},
        doc=[{"_id": 1, "val": "hello"}, {"_id": 2, "val": "world"}],
        expected=[{"_id": 2, "val": "world"}],
        msg="$nor should exclude docs matching string value",
    ),
    QueryTestCase(
        id="object",
        filter={"$nor": [{"val": {"nested": 1}}]},
        doc=[{"_id": 1, "val": {"nested": 1}}, {"_id": 2, "val": {"nested": 2}}],
        expected=[{"_id": 2, "val": {"nested": 2}}],
        msg="$nor should exclude docs matching object value",
    ),
    QueryTestCase(
        id="array",
        filter={"$nor": [{"val": [1, 2, 3]}]},
        doc=[{"_id": 1, "val": [1, 2, 3]}, {"_id": 2, "val": [4, 5]}],
        expected=[{"_id": 2, "val": [4, 5]}],
        msg="$nor should exclude docs matching array value",
    ),
    QueryTestCase(
        id="objectid",
        filter={"$nor": [{"val": ObjectId("507f1f77bcf86cd799439011")}]},
        doc=[
            {"_id": 1, "val": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "val": ObjectId("507f1f77bcf86cd799439012")},
        ],
        expected=[{"_id": 2, "val": ObjectId("507f1f77bcf86cd799439012")}],
        msg="$nor should exclude docs matching ObjectId value",
    ),
    QueryTestCase(
        id="boolean_true",
        filter={"$nor": [{"val": True}]},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": False}],
        expected=[{"_id": 2, "val": False}],
        msg="$nor should exclude docs matching boolean true",
    ),
    QueryTestCase(
        id="boolean_false",
        filter={"$nor": [{"val": False}]},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": False}],
        expected=[{"_id": 1, "val": True}],
        msg="$nor should exclude docs matching boolean false",
    ),
    QueryTestCase(
        id="date",
        filter={"$nor": [{"val": datetime(2024, 1, 1, tzinfo=timezone.utc)}]},
        doc=[
            {"_id": 1, "val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "val": datetime(2024, 6, 1, tzinfo=timezone.utc)},
        ],
        expected=[{"_id": 2, "val": datetime(2024, 6, 1, tzinfo=timezone.utc)}],
        msg="$nor should exclude docs matching date value",
    ),
    QueryTestCase(
        id="null",
        filter={"$nor": [{"val": None}]},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "val": 5}],
        expected=[{"_id": 2, "val": 5}],
        msg="$nor should exclude docs matching null value",
    ),
    QueryTestCase(
        id="int32",
        filter={"$nor": [{"val": 42}]},
        doc=[{"_id": 1, "val": 42}, {"_id": 2, "val": 99}],
        expected=[{"_id": 2, "val": 99}],
        msg="$nor should exclude docs matching int32 value",
    ),
    QueryTestCase(
        id="int64",
        filter={"$nor": [{"val": Int64(42)}]},
        doc=[{"_id": 1, "val": Int64(42)}, {"_id": 2, "val": Int64(99)}],
        expected=[{"_id": 2, "val": Int64(99)}],
        msg="$nor should exclude docs matching int64 value",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"$nor": [{"val": Decimal128("42.0")}]},
        doc=[{"_id": 1, "val": Decimal128("42.0")}, {"_id": 2, "val": Decimal128("99.0")}],
        expected=[{"_id": 2, "val": Decimal128("99.0")}],
        msg="$nor should exclude docs matching decimal128 value",
    ),
    QueryTestCase(
        id="timestamp",
        filter={"$nor": [{"val": Timestamp(1, 1)}]},
        doc=[{"_id": 1, "val": Timestamp(1, 1)}, {"_id": 2, "val": Timestamp(2, 1)}],
        expected=[{"_id": 2, "val": Timestamp(2, 1)}],
        msg="$nor should exclude docs matching timestamp value",
    ),
    QueryTestCase(
        id="minkey",
        filter={"$nor": [{"val": MinKey()}]},
        doc=[{"_id": 1, "val": MinKey()}, {"_id": 2, "val": 1}],
        expected=[{"_id": 2, "val": 1}],
        msg="$nor should exclude docs matching MinKey value",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"$nor": [{"val": MaxKey()}]},
        doc=[{"_id": 1, "val": MaxKey()}, {"_id": 2, "val": 1}],
        expected=[{"_id": 2, "val": 1}],
        msg="$nor should exclude docs matching MaxKey value",
    ),
]

BSON_TYPE_CODE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="javascript_code",
        filter={"$nor": [{"val": Code("function() { return 1; }")}]},
        doc=[
            {"_id": 1, "val": Code("function() { return 1; }")},
            {"_id": 2, "val": Code("function() { return 2; }")},
        ],
        expected=[{"_id": 2, "val": Code("function() { return 2; }")}],
        msg="$nor should exclude docs matching JavaScript Code value",
    ),
]

BSON_TYPE_BINARY_REGEX_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="binary",
        filter={"$nor": [{"val": b"\x01\x02\x03"}]},
        doc=[{"_id": 1, "val": b"\x01\x02\x03"}, {"_id": 2, "val": b"\x04\x05"}],
        expected=[{"_id": 2, "val": b"\x04\x05"}],
        msg="$nor should exclude docs matching binary value",
    ),
    QueryTestCase(
        id="regex",
        filter={"$nor": [{"val": Regex("^hello")}]},
        doc=[{"_id": 1, "val": "hello world"}, {"_id": 2, "val": "goodbye"}],
        expected=[{"_id": 2, "val": "goodbye"}],
        msg="$nor should exclude docs matching regex value",
    ),
]

NUMERIC_EQUIVALENCE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="int32_matches_int64",
        filter={"$nor": [{"val": 1}]},
        doc=[{"_id": 1, "val": Int64(1)}, {"_id": 2, "val": Int64(2)}],
        expected=[{"_id": 2, "val": Int64(2)}],
        msg="$nor int32 condition should match equivalent int64 value",
    ),
    QueryTestCase(
        id="int32_matches_double",
        filter={"$nor": [{"val": 1}]},
        doc=[{"_id": 1, "val": 1.0}, {"_id": 2, "val": 2.0}],
        expected=[{"_id": 2, "val": 2.0}],
        msg="$nor int32 condition should match equivalent double value",
    ),
    QueryTestCase(
        id="int32_matches_decimal128",
        filter={"$nor": [{"val": 1}]},
        doc=[{"_id": 1, "val": Decimal128("1")}, {"_id": 2, "val": Decimal128("2")}],
        expected=[{"_id": 2, "val": Decimal128("2")}],
        msg="$nor int32 condition should match equivalent decimal128 value",
    ),
    QueryTestCase(
        id="in_across_numeric_types",
        filter={"$nor": [{"val": {"$in": [1, Int64(1), 1.0, Decimal128("1")]}}]},
        doc=[
            {"_id": 1, "val": 1},
            {"_id": 2, "val": Int64(1)},
            {"_id": 3, "val": 1.0},
            {"_id": 4, "val": Decimal128("1")},
            {"_id": 5, "val": 2},
        ],
        expected=[{"_id": 5, "val": 2}],
        msg="$nor with $in across numeric types should exclude all numerically equivalent values",
    ),
]

BSON_TYPE_DISTINCTION_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="false_not_equal_to_zero",
        filter={"$nor": [{"val": False}]},
        doc=[{"_id": 1, "val": False}, {"_id": 2, "val": 0}],
        expected=[{"_id": 2, "val": 0}],
        msg="$nor with false should NOT exclude docs with val=0 (type distinction)",
    ),
    QueryTestCase(
        id="true_not_equal_to_one",
        filter={"$nor": [{"val": True}]},
        doc=[{"_id": 1, "val": True}, {"_id": 2, "val": 1}],
        expected=[{"_id": 2, "val": 1}],
        msg="$nor with true should NOT exclude docs with val=1 (type distinction)",
    ),
    QueryTestCase(
        id="null_matches_missing",
        filter={"$nor": [{"val": None}]},
        doc=[{"_id": 1, "val": None}, {"_id": 2, "other": 1}, {"_id": 3, "val": 5}],
        expected=[{"_id": 3, "val": 5}],
        msg="$nor with null excludes both null and missing field docs",
    ),
    QueryTestCase(
        id="empty_string_not_equal_to_null",
        filter={"$nor": [{"val": ""}]},
        doc=[{"_id": 1, "val": ""}, {"_id": 2, "val": None}],
        expected=[{"_id": 2, "val": None}],
        msg="$nor with empty string should NOT exclude docs with val=null",
    ),
]

MIXED_TYPE_CLAUSE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="mixed_types_in_clauses",
        filter={"$nor": [{"val": 1}, {"val": "hello"}]},
        doc=[
            {"_id": 1, "val": 1},
            {"_id": 2, "val": "hello"},
            {"_id": 3, "val": True},
        ],
        expected=[{"_id": 3, "val": True}],
        msg="$nor with mixed types in clauses should exclude each matching type",
    ),
]

ALL_TESTS = (
    BSON_TYPE_TESTS
    + BSON_TYPE_CODE_TESTS
    + BSON_TYPE_BINARY_REGEX_TESTS
    + NUMERIC_EQUIVALENCE_TESTS
    + BSON_TYPE_DISTINCTION_TESTS
    + MIXED_TYPE_CLAUSE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_nor_data_types(collection, test):
    """Test $nor query operator data type coverage."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        ignore_doc_order=True,
        msg=test.msg,
    )
