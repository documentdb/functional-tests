"""
arithmetic $sqrt tests.

Tests for the arithmetic $sqrt operator: negative-input errors (all numeric
types, including boundary and infinity values), non-numeric type-mismatch
errors, and arity errors (empty/multi-element array literals), as both literal
and inserted document field values. Also covers composite-array field
rejection.
"""

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    NON_NUMERIC_TYPE_MISMATCH_ERROR,
    SQRT_NEGATIVE_INPUT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

SQRT_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "negative_one",
        expression={"$sqrt": -1},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative one",
    ),
    ExpressionTestCase(
        "negative_int32_min",
        expression={"$sqrt": INT32_MIN},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int32 min",
    ),
    ExpressionTestCase(
        "negative_int32_min_plus_1",
        expression={"$sqrt": INT32_MIN_PLUS_1},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int32 min plus 1",
    ),
    ExpressionTestCase(
        "negative_int64",
        expression={"$sqrt": Int64(-4)},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative int64",
    ),
    ExpressionTestCase(
        "negative_int64_min",
        expression={"$sqrt": INT64_MIN},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int64 min",
    ),
    ExpressionTestCase(
        "negative_int64_min_plus_1",
        expression={"$sqrt": INT64_MIN_PLUS_1},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int64 min plus 1",
    ),
    ExpressionTestCase(
        "negative_double",
        expression={"$sqrt": -2.5},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative double",
    ),
    ExpressionTestCase(
        "negative_decimal",
        expression={"$sqrt": Decimal128("-1")},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative decimal",
    ),
    ExpressionTestCase(
        "double_negative_half",
        expression={"$sqrt": DOUBLE_NEGATIVE_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject double negative half",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$sqrt": DOUBLE_NEGATIVE_ONE_AND_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject double negative one and half",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$sqrt": DECIMAL128_NEGATIVE_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal negative half",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$sqrt": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal negative one and half",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$sqrt": DECIMAL128_MIN},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal128 min",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$sqrt": FLOAT_NEGATIVE_INFINITY},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject float negative infinity",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$sqrt": DECIMAL128_NEGATIVE_INFINITY},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal128 negative infinity",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$sqrt": {}},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="Should reject empty object",
    ),
    ExpressionTestCase(
        "array_value",
        expression={"$sqrt": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject array value in literal",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$sqrt": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject empty array in literal",
    ),
]


SQRT_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "negative_one",
        expression={"$sqrt": "$value"},
        doc={"value": -1},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative one",
    ),
    ExpressionTestCase(
        "negative_int32_min",
        expression={"$sqrt": "$value"},
        doc={"value": INT32_MIN},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int32 min",
    ),
    ExpressionTestCase(
        "negative_int32_min_plus_1",
        expression={"$sqrt": "$value"},
        doc={"value": INT32_MIN_PLUS_1},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int32 min plus 1",
    ),
    ExpressionTestCase(
        "negative_int64",
        expression={"$sqrt": "$value"},
        doc={"value": Int64(-4)},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative int64",
    ),
    ExpressionTestCase(
        "negative_int64_min",
        expression={"$sqrt": "$value"},
        doc={"value": INT64_MIN},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int64 min",
    ),
    ExpressionTestCase(
        "negative_int64_min_plus_1",
        expression={"$sqrt": "$value"},
        doc={"value": INT64_MIN_PLUS_1},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject int64 min plus 1",
    ),
    ExpressionTestCase(
        "negative_double",
        expression={"$sqrt": "$value"},
        doc={"value": -2.5},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative double",
    ),
    ExpressionTestCase(
        "negative_decimal",
        expression={"$sqrt": "$value"},
        doc={"value": Decimal128("-1")},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject negative decimal",
    ),
    ExpressionTestCase(
        "double_negative_half",
        expression={"$sqrt": "$value"},
        doc={"value": DOUBLE_NEGATIVE_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject double negative half",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half",
        expression={"$sqrt": "$value"},
        doc={"value": DOUBLE_NEGATIVE_ONE_AND_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject double negative one and half",
    ),
    ExpressionTestCase(
        "decimal_negative_half",
        expression={"$sqrt": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal negative half",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half",
        expression={"$sqrt": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal negative one and half",
    ),
    ExpressionTestCase(
        "decimal128_min",
        expression={"$sqrt": "$value"},
        doc={"value": DECIMAL128_MIN},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal128 min",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        expression={"$sqrt": "$value"},
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject float negative infinity",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        expression={"$sqrt": "$value"},
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        error_code=SQRT_NEGATIVE_INPUT_ERROR,
        msg="Should reject decimal128 negative infinity",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$sqrt": "$value"},
        doc={"value": {}},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="Should reject empty object",
    ),
    ExpressionTestCase(
        "empty_array_field",
        expression={"$sqrt": "$value"},
        doc={"value": []},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="Empty-array field value is non-numeric (not an arity error)",
    ),
    ExpressionTestCase(
        "composite_array_field",
        expression={"$sqrt": "$x.y"},
        doc={"x": [{"y": 4}, {"y": 9}]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="Should reject composite array from $x.y on array-of-objects",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SQRT_LITERAL_TESTS))
def test_sqrt_literal(collection, test):
    """Test $sqrt with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(SQRT_INSERT_TESTS))
def test_sqrt_insert(collection, test):
    """Test $sqrt with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
