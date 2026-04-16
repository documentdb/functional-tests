"""
Tests for $setField invalid inputs and error codes.

Covers missing/extra arguments, invalid types per parameter position,
and field paths resolving to non-document types.
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
from documentdb_tests.framework.error_codes import (
    SET_FIELD_FIELD_PATH_ERROR,
    SET_FIELD_INVALID_FIELD_TYPE_ERROR,
    SET_FIELD_INVALID_INPUT_TYPE_ERROR,
    SET_FIELD_MISSING_FIELD_ERROR,
    SET_FIELD_MISSING_INPUT_ERROR,
    SET_FIELD_MISSING_VALUE_ERROR,
    SET_FIELD_NON_CONST_FIELD_ERROR,
    SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
    SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    # Missing/Extra Arguments
    ExpressionTestCase(
        "empty_object",
        expression={"$setField": {}},
        error_code=SET_FIELD_MISSING_FIELD_ERROR,
        msg="Empty object argument should error with missing field",
    ),
    ExpressionTestCase(
        "only_field",
        expression={"$setField": {"field": "x"}},
        error_code=SET_FIELD_MISSING_VALUE_ERROR,
        msg="Only field argument without input/value should error with missing value",
    ),
    ExpressionTestCase(
        "only_input",
        expression={"$setField": {"input": {"a": 1}}},
        error_code=SET_FIELD_MISSING_FIELD_ERROR,
        msg="Only input argument without field/value should error with missing field",
    ),
    ExpressionTestCase(
        "only_value",
        expression={"$setField": {"value": 1}},
        error_code=SET_FIELD_MISSING_FIELD_ERROR,
        msg="Only value argument without field/input should error with missing field",
    ),
    ExpressionTestCase(
        "field_and_input_only",
        expression={"$setField": {"field": "x", "input": {"a": 1}}},
        error_code=SET_FIELD_MISSING_VALUE_ERROR,
        msg="Field and input without value should error with missing value",
    ),
    ExpressionTestCase(
        "field_and_value_only",
        expression={"$setField": {"field": "x", "value": 1}},
        error_code=SET_FIELD_MISSING_INPUT_ERROR,
        msg="Field and value without input should error with missing input",
    ),
    ExpressionTestCase(
        "input_and_value_only",
        expression={"$setField": {"input": {"a": 1}, "value": 1}},
        error_code=SET_FIELD_MISSING_FIELD_ERROR,
        msg="Input and value without field should error with missing field",
    ),
    ExpressionTestCase(
        "extra_unknown_field",
        expression={"$setField": {"field": "x", "input": {}, "value": 1, "extra": 1}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="Extra unknown argument should error with unknown argument",
    ),
    ExpressionTestCase(
        "null_top_level",
        expression={"$setField": None},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Null as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "array_top_level",
        expression={"$setField": []},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Array as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "int_top_level",
        expression={"$setField": 1},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Integer as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "string_top_level",
        expression={"$setField": "hello"},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="String as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "bool_top_level",
        expression={"$setField": True},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Boolean as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "expression_top_level",
        expression={"$setField": {"$add": [1, 2]}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="Expression as top-level argument should error with unknown argument",
    ),
    ExpressionTestCase(
        "all_valid_plus_extra",
        expression={"$setField": {"field": "x", "input": {}, "value": 1, "unknown": 2}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="All valid args plus unknown extra should error with unknown argument",
    ),
    ExpressionTestCase(
        "field_int",
        expression={"$setField": {"field": 1, "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Integer as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_long",
        expression={"$setField": {"field": Int64(1), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Long as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_double",
        expression={"$setField": {"field": 1.5, "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Double as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_decimal128",
        expression={"$setField": {"field": Decimal128("1"), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Decimal128 as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_bool",
        expression={"$setField": {"field": True, "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Boolean as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_null",
        expression={"$setField": {"field": None, "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Null as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_object",
        expression={"$setField": {"field": {"a": 1}, "input": {}, "value": 1}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="Non-const object as field parameter should error",
    ),
    ExpressionTestCase(
        "field_empty_object",
        expression={"$setField": {"field": {}, "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Empty object as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_array",
        expression={"$setField": {"field": ["x"], "input": {}, "value": 1}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="Non-const array as field parameter should error",
    ),
    ExpressionTestCase(
        "field_date",
        expression={"$setField": {"field": datetime(2024, 1, 1), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Date as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_objectid",
        expression={"$setField": {"field": ObjectId(), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="ObjectId as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_regex",
        expression={"$setField": {"field": Regex("abc"), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Regex as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_bindata",
        expression={"$setField": {"field": Binary(b""), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="BinData as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_timestamp",
        expression={"$setField": {"field": Timestamp(0, 0), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Timestamp as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_minkey",
        expression={"$setField": {"field": MinKey(), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="MinKey as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_maxkey",
        expression={"$setField": {"field": MaxKey(), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="MaxKey as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_javascript",
        expression={"$setField": {"field": Code("return 1"), "input": {}, "value": 1}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="JavaScript as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_path_ref",
        expression={"$setField": {"field": "$x", "input": {}, "value": 1}},
        error_code=SET_FIELD_FIELD_PATH_ERROR,
        msg="Field path reference as field parameter should error",
    ),
    # Invalid input parameter types
    ExpressionTestCase(
        "input_string",
        expression={"$setField": {"field": "x", "input": "hello", "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="String as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_int",
        expression={"$setField": {"field": "x", "input": 1, "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Integer as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_long",
        expression={"$setField": {"field": "x", "input": Int64(1), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Long as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_double",
        expression={"$setField": {"field": "x", "input": 1.5, "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Double as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_decimal128",
        expression={"$setField": {"field": "x", "input": Decimal128("1"), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Decimal128 as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_bool",
        expression={"$setField": {"field": "x", "input": True, "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Boolean as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_array",
        expression={"$setField": {"field": "x", "input": [1, 2], "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Array as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_date",
        expression={"$setField": {"field": "x", "input": datetime(2024, 1, 1), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Date as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_objectid",
        expression={"$setField": {"field": "x", "input": ObjectId(), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="ObjectId as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_regex",
        expression={"$setField": {"field": "x", "input": Regex("abc"), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Regex as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_bindata",
        expression={"$setField": {"field": "x", "input": Binary(b""), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="BinData as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_timestamp",
        expression={"$setField": {"field": "x", "input": Timestamp(0, 0), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Timestamp as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_minkey",
        expression={"$setField": {"field": "x", "input": MinKey(), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="MinKey as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_maxkey",
        expression={"$setField": {"field": "x", "input": MaxKey(), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="MaxKey as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_javascript",
        expression={"$setField": {"field": "x", "input": Code("return 1"), "value": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="JavaScript as input parameter should error with invalid input type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_setField_literal(collection, test):
    """Test $setField literal argument handling and type validation."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result,
        expected=test.expected if test.error_code is None else None,
        error_code=test.error_code,
        msg=test.msg,
    )


FIELD_REF_INVALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": "hello"},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to string should error with invalid input type",
    ),
    ExpressionTestCase(
        "int_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": 42},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to int should error with invalid input type",
    ),
    ExpressionTestCase(
        "long_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": Int64(1)},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to long should error with invalid input type",
    ),
    ExpressionTestCase(
        "double_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": 1.5},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to double should error with invalid input type",
    ),
    ExpressionTestCase(
        "decimal128_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": Decimal128("1")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to decimal128 should error with invalid input type",
    ),
    ExpressionTestCase(
        "bool_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": True},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to bool should error with invalid input type",
    ),
    ExpressionTestCase(
        "array_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": [1, 2, 3]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to array should error with invalid input type",
    ),
    ExpressionTestCase(
        "date_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": datetime(2024, 1, 1)},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to date should error with invalid input type",
    ),
    ExpressionTestCase(
        "objectId_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": ObjectId("000000000000000000000000")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to objectId should error with invalid input type",
    ),
    ExpressionTestCase(
        "binData_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": Binary(b"abc")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to binData should error with invalid input type",
    ),
    ExpressionTestCase(
        "regex_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": Regex("pattern")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to regex should error with invalid input type",
    ),
    ExpressionTestCase(
        "javascript_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": Code("function(){}")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to javascript should error with invalid input type",
    ),
    ExpressionTestCase(
        "timestamp_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": Timestamp(0, 0)},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to timestamp should error with invalid input type",
    ),
    ExpressionTestCase(
        "minKey_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": MinKey()},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to minKey should error with invalid input type",
    ),
    ExpressionTestCase(
        "maxKey_input_errors",
        expression={"$setField": {"field": "x", "input": "$v", "value": 1}},
        doc={"v": MaxKey()},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to maxKey should error with invalid input type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_INVALID_TESTS))
def test_setField_field_ref_invalid(collection, test):
    """Test $setField with field ref resolving to invalid input type."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
