"""
Invalid input tests for $getField expression.

Tests missing/extra arguments, invalid field types (BSON types, dynamic
expressions, system variables, field references), and non-string field errors.
"""

from datetime import datetime

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    GETFIELD_FIELD_NOT_STRING_ERROR,
    GETFIELD_MISSING_FIELD_ERROR,
    GETFIELD_MISSING_INPUT_ERROR,
    GETFIELD_UNKNOWN_ARG_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Literal error cases
# ---------------------------------------------------------------------------
LITERAL_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_object",
        expression={"$getField": {}},
        error_code=GETFIELD_MISSING_FIELD_ERROR,
        msg="Should error on empty object argument",
    ),
    ExpressionTestCase(
        "missing_field_param",
        expression={"$getField": {"input": {"a": 1}}},
        error_code=GETFIELD_MISSING_FIELD_ERROR,
        msg="Should error when field parameter is missing",
    ),
    ExpressionTestCase(
        "full_syntax_field_only",
        expression={"$getField": {"field": "a"}},
        error_code=GETFIELD_MISSING_INPUT_ERROR,
        msg="Should error when input is missing in full syntax",
    ),
    ExpressionTestCase(
        "extra_argument",
        expression={"$getField": {"field": "a", "input": {"a": 1}, "extra": 1}},
        error_code=GETFIELD_UNKNOWN_ARG_ERROR,
        msg="Should error on unrecognized argument",
    ),
    ExpressionTestCase(
        "null_shorthand",
        expression={"$getField": None},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when shorthand field is null",
    ),
    ExpressionTestCase(
        "null_full_syntax",
        expression={"$getField": {"field": None, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is null in full syntax",
    ),
    ExpressionTestCase(
        "numeric_shorthand",
        expression={"$getField": 1},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when shorthand field is numeric",
    ),
    ExpressionTestCase(
        "bool_shorthand",
        expression={"$getField": True},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when shorthand field is boolean",
    ),
    ExpressionTestCase(
        "bool_full_syntax",
        expression={"$getField": {"field": True, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is boolean in full syntax",
    ),
    ExpressionTestCase(
        "array_field",
        expression={"$getField": {"field": [1, 2], "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is array",
    ),
    ExpressionTestCase(
        "arithmetic_expr_as_field",
        expression={"$getField": {"$add": [1, 2]}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field resolves to non-string via $add",
    ),
    ExpressionTestCase(
        "const_bool_as_field",
        expression={"$getField": {"$const": True}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is $const boolean",
    ),
    ExpressionTestCase(
        "const_object_as_field",
        expression={"$getField": {"$const": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is $const object",
    ),
    ExpressionTestCase(
        "const_array_as_field_full_syntax",
        expression={"$getField": {"field": {"$const": [1, 2]}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is $const array",
    ),
    ExpressionTestCase(
        "empty_object_as_field",
        expression={"$getField": {"field": {}, "input": "$$ROOT"}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field is empty object",
    ),
    ExpressionTestCase(
        "int_field",
        expression={"$getField": {"field": 1, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject int field",
    ),
    ExpressionTestCase(
        "long_field",
        expression={"$getField": {"field": Int64(1), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject long field",
    ),
    ExpressionTestCase(
        "double_field",
        expression={"$getField": {"field": 1.5, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject double field",
    ),
    ExpressionTestCase(
        "decimal128_field",
        expression={"$getField": {"field": Decimal128("1"), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject decimal128 field",
    ),
    ExpressionTestCase(
        "date_field",
        expression={"$getField": {"field": datetime(2024, 1, 1), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject date field",
    ),
    ExpressionTestCase(
        "objectid_field",
        expression={"$getField": {"field": ObjectId(), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject objectId field",
    ),
    ExpressionTestCase(
        "bindata_field",
        expression={"$getField": {"field": Binary(b""), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject binData field",
    ),
    ExpressionTestCase(
        "regex_field",
        expression={"$getField": {"field": Regex("abc"), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject regex field",
    ),
    ExpressionTestCase(
        "timestamp_field",
        expression={"$getField": {"field": Timestamp(0, 1), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject timestamp field",
    ),
    ExpressionTestCase(
        "minkey_field",
        expression={"$getField": {"field": MinKey(), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject minKey field",
    ),
    ExpressionTestCase(
        "maxkey_field",
        expression={"$getField": {"field": MaxKey(), "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should reject maxKey field",
    ),
    ExpressionTestCase(
        "add_expr",
        expression={"$getField": {"field": {"$add": [1, 2]}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $add resolves to int",
    ),
    ExpressionTestCase(
        "mod_expr",
        expression={"$getField": {"field": {"$mod": [10, 3]}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $mod resolves to int",
    ),
    ExpressionTestCase(
        "ne_expr",
        expression={"$getField": {"field": {"$ne": [1, 2]}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $ne resolves to bool",
    ),
    ExpressionTestCase(
        "toDouble_expr",
        expression={"$getField": {"field": {"$toDouble": "1.5"}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $toDouble resolves to double",
    ),
    ExpressionTestCase(
        "mergeObjects_expr",
        expression={"$getField": {"field": {"$mergeObjects": [{"a": 1}]}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $mergeObjects resolves to object",
    ),
    ExpressionTestCase(
        "mergeObjects_nulls",
        expression={"$getField": {"field": {"$mergeObjects": [None, None]}, "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $mergeObjects of nulls resolves to object",
    ),
    ExpressionTestCase(
        "now_as_field",
        expression={"$getField": {"field": "$$NOW", "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $$NOW used as field (date type)",
    ),
    ExpressionTestCase(
        "remove_as_field",
        expression={"$getField": {"field": "$$REMOVE", "input": {"a": 1}}},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when $$REMOVE used as field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_ERROR_TESTS))
def test_getField_invalid_literal(collection, test):
    """Test $getField error cases with literal inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Insert-based error cases
# ---------------------------------------------------------------------------
INSERT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_getfield_nonstring",
        expression={"$getField": {"$getField": "val"}},
        doc={"val": 123},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when nested $getField resolves to non-string",
    ),
    ExpressionTestCase(
        "missing_field_ref",
        expression={"$getField": {"field": "$nonexistent", "input": {"a": 1}}},
        doc={"a": 1},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field resolves to missing",
    ),
    ExpressionTestCase(
        "ref_to_int",
        expression={"$getField": {"field": "$f", "input": {"a": 1}}},
        doc={"f": 123},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field ref resolves to int",
    ),
    ExpressionTestCase(
        "ref_to_array",
        expression={"$getField": {"field": "$f", "input": {"a": 1}}},
        doc={"f": ["a"]},
        error_code=GETFIELD_FIELD_NOT_STRING_ERROR,
        msg="Should error when field ref resolves to array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_ERROR_TESTS))
def test_getField_invalid_insert(collection, test):
    """Test $getField error cases with inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, error_code=test.error_code, msg=test.msg)
