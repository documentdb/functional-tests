"""
Tests for $unsetField invalid inputs and error codes.

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
    SET_FIELD_NON_CONST_FIELD_ERROR,
    SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
    SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
    UNRECOGNIZED_EXPRESSION_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    # Missing/Extra Arguments
    ExpressionTestCase(
        "empty_object",
        expression={"$unsetField": {}},
        error_code=SET_FIELD_MISSING_FIELD_ERROR,
        msg="Empty object argument should error with missing field",
    ),
    ExpressionTestCase(
        "only_field",
        expression={"$unsetField": {"field": "a"}},
        error_code=SET_FIELD_MISSING_INPUT_ERROR,
        msg="Only field argument without input should error with missing input",
    ),
    ExpressionTestCase(
        "only_input",
        expression={"$unsetField": {"input": {"a": 1}}},
        error_code=SET_FIELD_MISSING_FIELD_ERROR,
        msg="Only input argument without field should error with missing field",
    ),
    ExpressionTestCase(
        "with_value",
        expression={"$unsetField": {"field": "x", "input": {}, "value": 1}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="$unsetField with value argument should error with unknown argument",
    ),
    ExpressionTestCase(
        "with_value_null",
        expression={"$unsetField": {"field": None, "input": {}, "value": None}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="$unsetField with null value argument should error with unknown argument",
    ),
    ExpressionTestCase(
        "extra_unknown_field",
        expression={"$unsetField": {"field": "a", "input": {}, "extra": 1}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="Extra unknown argument should error with unknown argument",
    ),
    ExpressionTestCase(
        "null_top_level",
        expression={"$unsetField": None},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Null as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "array_top_level",
        expression={"$unsetField": ["a", "$$ROOT"]},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Array as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "int_top_level",
        expression={"$unsetField": 1},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Integer as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "string_top_level",
        expression={"$unsetField": "hello"},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="String as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "bool_top_level",
        expression={"$unsetField": True},
        error_code=SET_FIELD_NON_OBJECT_ARGUMENT_ERROR,
        msg="Boolean as top-level argument should error with non-object argument",
    ),
    ExpressionTestCase(
        "expression_top_level",
        expression={"$unsetField": {"$add": [1, 2]}},
        error_code=SET_FIELD_UNKNOWN_ARGUMENT_ERROR,
        msg="Expression as top-level argument should error with unknown argument",
    ),
    ExpressionTestCase(
        "missing_input_null_field",
        expression={"$unsetField": {"field": None}},
        error_code=SET_FIELD_MISSING_INPUT_ERROR,
        msg="Missing input with null field should error with missing input",
    ),
    # Invalid field parameter types
    ExpressionTestCase(
        "field_int",
        expression={"$unsetField": {"field": 1, "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Integer as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_long",
        expression={"$unsetField": {"field": Int64(1), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Long as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_double",
        expression={"$unsetField": {"field": 1.5, "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Double as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_decimal128",
        expression={"$unsetField": {"field": Decimal128("1"), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Decimal128 as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_bool",
        expression={"$unsetField": {"field": True, "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Boolean as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_null",
        expression={"$unsetField": {"field": None, "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Null as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_object",
        expression={"$unsetField": {"field": {"a": 1}, "input": {}}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="Non-const object as field parameter should error",
    ),
    ExpressionTestCase(
        "field_empty_object",
        expression={"$unsetField": {"field": {}, "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Empty object as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_array",
        expression={"$unsetField": {"field": ["x"], "input": {}}},
        error_code=SET_FIELD_NON_CONST_FIELD_ERROR,
        msg="Non-const array as field parameter should error",
    ),
    ExpressionTestCase(
        "field_date",
        expression={"$unsetField": {"field": datetime(2024, 1, 1), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Date as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_objectid",
        expression={"$unsetField": {"field": ObjectId(), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="ObjectId as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_regex",
        expression={"$unsetField": {"field": Regex("abc"), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Regex as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_bindata",
        expression={"$unsetField": {"field": Binary(b""), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="BinData as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_timestamp",
        expression={"$unsetField": {"field": Timestamp(0, 0), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="Timestamp as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_minkey",
        expression={"$unsetField": {"field": MinKey(), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="MinKey as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_maxkey",
        expression={"$unsetField": {"field": MaxKey(), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="MaxKey as field parameter should error with invalid field type",
    ),
    ExpressionTestCase(
        "field_javascript",
        expression={"$unsetField": {"field": Code("return 1"), "input": {}}},
        error_code=SET_FIELD_INVALID_FIELD_TYPE_ERROR,
        msg="JavaScript as field parameter should error with invalid field type",
    ),
    # Non-constant field expressions
    ExpressionTestCase(
        "field_path_ref",
        expression={"$unsetField": {"field": "$x", "input": {}}},
        error_code=SET_FIELD_FIELD_PATH_ERROR,
        msg="Field path reference as field parameter should error",
    ),
    ExpressionTestCase(
        "field_dollar_no_literal",
        expression={"$unsetField": {"field": "$price", "input": {"$price": 1}}},
        error_code=UNRECOGNIZED_EXPRESSION_ERROR,
        msg="Dollar-prefixed field without $literal should error with invalid field path",
    ),
    # Invalid input parameter types
    ExpressionTestCase(
        "input_string",
        expression={"$unsetField": {"field": "x", "input": "hello"}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="String as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_int",
        expression={"$unsetField": {"field": "x", "input": 1}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Integer as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_long",
        expression={"$unsetField": {"field": "x", "input": Int64(1)}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Long as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_double",
        expression={"$unsetField": {"field": "x", "input": 1.5}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Double as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_decimal128",
        expression={"$unsetField": {"field": "x", "input": Decimal128("1")}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Decimal128 as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_bool",
        expression={"$unsetField": {"field": "x", "input": True}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Boolean as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_array",
        expression={"$unsetField": {"field": "x", "input": [1, 2]}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Array as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_date",
        expression={"$unsetField": {"field": "x", "input": datetime(2024, 1, 1)}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Date as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_objectid",
        expression={"$unsetField": {"field": "x", "input": ObjectId()}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="ObjectId as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_regex",
        expression={"$unsetField": {"field": "x", "input": Regex("abc")}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Regex as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_bindata",
        expression={"$unsetField": {"field": "x", "input": Binary(b"")}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="BinData as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_timestamp",
        expression={"$unsetField": {"field": "x", "input": Timestamp(0, 0)}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Timestamp as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_minkey",
        expression={"$unsetField": {"field": "x", "input": MinKey()}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="MinKey as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_maxkey",
        expression={"$unsetField": {"field": "x", "input": MaxKey()}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="MaxKey as input parameter should error with invalid input type",
    ),
    ExpressionTestCase(
        "input_javascript",
        expression={"$unsetField": {"field": "x", "input": Code("return 1")}},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="JavaScript as input parameter should error with invalid input type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_unsetField_literal(collection, test):
    """Test $unsetField literal argument handling and type validation."""
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
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": "hello"},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to string should error with invalid input type",
    ),
    ExpressionTestCase(
        "int_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": 42},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to int should error with invalid input type",
    ),
    ExpressionTestCase(
        "long_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": Int64(1)},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to long should error with invalid input type",
    ),
    ExpressionTestCase(
        "double_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": 1.5},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to double should error with invalid input type",
    ),
    ExpressionTestCase(
        "decimal128_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": Decimal128("1")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to decimal128 should error with invalid input type",
    ),
    ExpressionTestCase(
        "bool_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": True},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to bool should error with invalid input type",
    ),
    ExpressionTestCase(
        "array_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": [1, 2, 3]},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to array should error with invalid input type",
    ),
    ExpressionTestCase(
        "date_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": datetime(2024, 1, 1)},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to date should error with invalid input type",
    ),
    ExpressionTestCase(
        "objectId_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": ObjectId("000000000000000000000000")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to objectId should error with invalid input type",
    ),
    ExpressionTestCase(
        "binData_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": Binary(b"abc")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to binData should error with invalid input type",
    ),
    ExpressionTestCase(
        "regex_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": Regex("pattern")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to regex should error with invalid input type",
    ),
    ExpressionTestCase(
        "javascript_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": Code("function(){}")},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to javascript should error with invalid input type",
    ),
    ExpressionTestCase(
        "timestamp_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": Timestamp(0, 0)},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to timestamp should error with invalid input type",
    ),
    ExpressionTestCase(
        "minKey_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": MinKey()},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to minKey should error with invalid input type",
    ),
    ExpressionTestCase(
        "maxKey_input_errors",
        expression={"$unsetField": {"field": "x", "input": "$v"}},
        doc={"v": MaxKey()},
        error_code=SET_FIELD_INVALID_INPUT_TYPE_ERROR,
        msg="Field ref resolving to maxKey should error with invalid input type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FIELD_REF_INVALID_TESTS))
def test_unsetField_field_ref_invalid(collection, test):
    """Test $unsetField with field ref resolving to invalid input type."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
