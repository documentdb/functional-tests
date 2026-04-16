"""
Tests for $mergeObjects invalid inputs and error codes.

Covers per-position invalid type validation and field paths resolving to non-document types.
"""

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import MERGE_OBJECTS_INVALID_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    # Invalid types in second position
    ExpressionTestCase(
        "string_2nd",
        expression={"$mergeObjects": [{"a": 1}, "hello"]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="String literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "int_2nd",
        expression={"$mergeObjects": [{"a": 1}, 1]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Int literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "long_2nd",
        expression={"$mergeObjects": [{"a": 1}, Int64(1)]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Long literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "double_2nd",
        expression={"$mergeObjects": [{"a": 1}, 1.5]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Double literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "decimal128_2nd",
        expression={"$mergeObjects": [{"a": 1}, Decimal128("1")]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Decimal128 literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "bool_2nd",
        expression={"$mergeObjects": [{"a": 1}, True]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Bool literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "date_2nd",
        expression={"$mergeObjects": [{"a": 1}, datetime(2024, 1, 1)]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Date literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "array_2nd",
        expression={"$mergeObjects": [{"a": 1}, [1, 2]]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Array literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "objectId_2nd",
        expression={"$mergeObjects": [{"a": 1}, ObjectId("000000000000000000000000")]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="ObjectId literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "binData_2nd",
        expression={"$mergeObjects": [{"a": 1}, Binary(b"")]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="BinData literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "regex_2nd",
        expression={"$mergeObjects": [{"a": 1}, Regex("pattern")]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Regex literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "javascript_2nd",
        expression={"$mergeObjects": [{"a": 1}, Code("function(){}")]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="JavaScript literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "timestamp_2nd",
        expression={"$mergeObjects": [{"a": 1}, Timestamp(0, 0)]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Timestamp literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "minKey_2nd",
        expression={"$mergeObjects": [{"a": 1}, MinKey()]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="MinKey literal in second position should error with invalid type",
    ),
    ExpressionTestCase(
        "maxKey_2nd",
        expression={"$mergeObjects": [{"a": 1}, MaxKey()]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="MaxKey literal in second position should error with invalid type",
    ),
    # Invalid types in first position
    ExpressionTestCase(
        "string_1st",
        expression={"$mergeObjects": ["hello", {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="String literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "int_1st",
        expression={"$mergeObjects": [1, {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Int literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "long_1st",
        expression={"$mergeObjects": [Int64(1), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Long literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "double_1st",
        expression={"$mergeObjects": [1.5, {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Double literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "decimal128_1st",
        expression={"$mergeObjects": [Decimal128("1"), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Decimal128 literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "bool_1st",
        expression={"$mergeObjects": [True, {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Bool literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "date_1st",
        expression={"$mergeObjects": [datetime(2024, 1, 1), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Date literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "array_1st",
        expression={"$mergeObjects": [[1, 2], {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Array literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "objectId_1st",
        expression={"$mergeObjects": [ObjectId("000000000000000000000000"), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="ObjectId literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "binData_1st",
        expression={"$mergeObjects": [Binary(b""), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="BinData literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "regex_1st",
        expression={"$mergeObjects": [Regex("pattern"), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Regex literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "javascript_1st",
        expression={"$mergeObjects": [Code("function(){}"), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="JavaScript literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "timestamp_1st",
        expression={"$mergeObjects": [Timestamp(0, 0), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Timestamp literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "minKey_1st",
        expression={"$mergeObjects": [MinKey(), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="MinKey literal in first position should error with invalid type",
    ),
    ExpressionTestCase(
        "maxKey_1st",
        expression={"$mergeObjects": [MaxKey(), {"a": 1}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="MaxKey literal in first position should error with invalid type",
    ),
    # Non-array syntax with invalid literal types
    ExpressionTestCase(
        "non_array_string",
        expression={"$mergeObjects": "hello"},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array string literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_int",
        expression={"$mergeObjects": 1},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array int literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_long",
        expression={"$mergeObjects": Int64(1)},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array long literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_double",
        expression={"$mergeObjects": 1.5},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array double literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_decimal128",
        expression={"$mergeObjects": Decimal128("1")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array decimal128 literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_bool",
        expression={"$mergeObjects": True},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array bool literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_date",
        expression={"$mergeObjects": datetime(2024, 1, 1)},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array date literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_objectId",
        expression={"$mergeObjects": ObjectId("000000000000000000000000")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array objectId literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_binData",
        expression={"$mergeObjects": Binary(b"")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array binData literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_regex",
        expression={"$mergeObjects": Regex("pattern")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array regex literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_javascript",
        expression={"$mergeObjects": Code("function(){}")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array javascript literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_timestamp",
        expression={"$mergeObjects": Timestamp(0, 0)},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array timestamp literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_minKey",
        expression={"$mergeObjects": MinKey()},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array minKey literal argument should error with invalid type",
    ),
    ExpressionTestCase(
        "non_array_maxKey",
        expression={"$mergeObjects": MaxKey()},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Non-array maxKey literal argument should error with invalid type",
    ),
    # Invalid type in middle position
    ExpressionTestCase(
        "string_middle",
        expression={"$mergeObjects": [{"a": 1}, "hello", {"b": 2}]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="String literal in middle position should error with invalid type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_mergeObjects_literal(collection, test):
    """Test $mergeObjects literal argument handling and type validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result,
        expected=test.expected if test.error_code is None else None,
        error_code=test.error_code,
        msg=test.msg,
    )


FIELD_REF_INVALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": [1, 2, 3]},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to array should error with invalid type",
    ),
    ExpressionTestCase(
        "string_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": "hello"},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to string should error with invalid type",
    ),
    ExpressionTestCase(
        "number_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": 42},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to number should error with invalid type",
    ),
    ExpressionTestCase(
        "bool_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": True},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to bool should error with invalid type",
    ),
    ExpressionTestCase(
        "long_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": Int64(1)},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to long should error with invalid type",
    ),
    ExpressionTestCase(
        "double_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": 1.5},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to double should error with invalid type",
    ),
    ExpressionTestCase(
        "decimal128_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": Decimal128("1")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to decimal128 should error with invalid type",
    ),
    ExpressionTestCase(
        "date_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": datetime(2024, 1, 1)},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to date should error with invalid type",
    ),
    ExpressionTestCase(
        "objectId_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": ObjectId("000000000000000000000000")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to objectId should error with invalid type",
    ),
    ExpressionTestCase(
        "binData_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": Binary(b"abc")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to binData should error with invalid type",
    ),
    ExpressionTestCase(
        "regex_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": Regex("pattern")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to regex should error with invalid type",
    ),
    ExpressionTestCase(
        "javascript_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": Code("function(){}")},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to javascript should error with invalid type",
    ),
    ExpressionTestCase(
        "timestamp_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": Timestamp(0, 0)},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to timestamp should error with invalid type",
    ),
    ExpressionTestCase(
        "minKey_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": MinKey()},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to minKey should error with invalid type",
    ),
    ExpressionTestCase(
        "maxKey_field_errors",
        expression={"$mergeObjects": ["$x", {"a": 1}]},
        doc={"x": MaxKey()},
        error_code=MERGE_OBJECTS_INVALID_TYPE_ERROR,
        msg="Field ref resolving to maxKey should error with invalid type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_INVALID_TESTS))
def test_mergeObjects_field_ref_invalid(collection, test):
    """Test $mergeObjects with field ref resolving to invalid type."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
