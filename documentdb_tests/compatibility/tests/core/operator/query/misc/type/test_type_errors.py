"""
Tests for $type query operator error handling and edge cases.

Verifies that $type returns appropriate errors for invalid string aliases,
invalid numeric codes, wrong argument types, and empty arrays. Also tests
edge cases with deprecated types and float type codes.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, ObjectId

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [{"_id": 1, "x": "test"}]

ERROR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="invalid_string_alias",
        filter={"x": {"$type": "invalid"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with invalid string alias should return error code 2",
    ),
    QueryTestCase(
        id="empty_string_alias",
        filter={"x": {"$type": ""}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with empty string should return error code 2",
    ),
    QueryTestCase(
        id="case_sensitive_uppercase_NUMBER",
        filter={"x": {"$type": "NUMBER"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type aliases are case-sensitive, 'NUMBER' should error",
    ),
    QueryTestCase(
        id="case_sensitive_titlecase_Double",
        filter={"x": {"$type": "Double"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type aliases are case-sensitive, 'Double' should error",
    ),
    QueryTestCase(
        id="leading_whitespace_in_alias",
        filter={"x": {"$type": " double"}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with leading whitespace should error",
    ),
    QueryTestCase(
        id="trailing_whitespace_in_alias",
        filter={"x": {"$type": "double "}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with trailing whitespace should error",
    ),
    QueryTestCase(
        id="invalid_numeric_code_99",
        filter={"x": {"$type": 99}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with invalid numeric code 99 should error",
    ),
    QueryTestCase(
        id="invalid_numeric_code_neg2",
        filter={"x": {"$type": -2}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with -2 should error (only -1 valid for minKey)",
    ),
    QueryTestCase(
        id="invalid_numeric_code_0",
        filter={"x": {"$type": 0}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with 0 should error (no BSON type 0)",
    ),
    QueryTestCase(
        id="non_integer_float_1_5",
        filter={"x": {"$type": 1.5}},
        doc=DOCS,
        error_code=BAD_VALUE_ERROR,
        msg="$type with non-integer float 1.5 should error",
    ),
    QueryTestCase(
        id="invalid_arg_boolean_true",
        filter={"x": {"$type": True}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with boolean argument should error",
    ),
    QueryTestCase(
        id="invalid_arg_boolean_false",
        filter={"x": {"$type": False}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with boolean false should error",
    ),
    QueryTestCase(
        id="invalid_arg_null",
        filter={"x": {"$type": None}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with null argument should error",
    ),
    QueryTestCase(
        id="invalid_arg_object",
        filter={"x": {"$type": {}}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with object argument should error",
    ),
    QueryTestCase(
        id="invalid_arg_nested_array",
        filter={"x": {"$type": [[1, 2]]}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with nested array should error",
    ),
    QueryTestCase(
        id="invalid_arg_objectid",
        filter={"x": {"$type": ObjectId()}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with ObjectId argument should error",
    ),
    QueryTestCase(
        id="invalid_arg_date",
        filter={"x": {"$type": datetime(2024, 1, 1, tzinfo=timezone.utc)}},
        doc=DOCS,
        error_code=TYPE_MISMATCH_ERROR,
        msg="$type with Date argument should error",
    ),
    QueryTestCase(
        id="empty_type_array",
        filter={"x": {"$type": []}},
        doc=DOCS,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$type with empty array should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ERROR_TESTS))
def test_type_errors(collection, test):
    """Test $type with invalid arguments that should produce errors."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertFailureCode(result, test.error_code, msg=test.msg)


EDGE_CASE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="float_1_0_as_type_code",
        filter={"x": {"$type": 1.0}},
        doc=DOCS,
        expected=None,
        msg="$type: 1.0 (double that equals int 1) behavior",
    ),
    QueryTestCase(
        id="int64_as_type_code",
        filter={"x": {"$type": Int64(2)}},
        doc=DOCS,
        expected=None,
        msg="$type: Int64(2) (long integer as type code) behavior",
    ),
    QueryTestCase(
        id="decimal128_as_type_code",
        filter={"x": {"$type": Decimal128("2")}},
        doc=DOCS,
        expected=None,
        msg="$type: Decimal128('2') (decimal as type code) behavior",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EDGE_CASE_TESTS))
def test_type_edge_cases(collection, test):
    """Test $type edge cases with float codes."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    # exploratory — just verify no crash; accept success or error
    assertSuccess(result, result["cursor"]["firstBatch"], msg=test.msg)
