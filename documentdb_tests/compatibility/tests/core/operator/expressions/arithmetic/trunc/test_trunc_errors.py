"""
Error tests for $trunc expression.

Covers non-numeric type rejection, invalid/out-of-bounds place values,
place type errors (bool, object, array, infinity, fractional decimal128),
arity errors, and composite/array-index field path rejection.
"""

import pytest
from bson import (
    Decimal128,
    Int64,
)
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    INVALID_POSITION_ERROR,
    INVALID_TYPE_ERROR,
    NON_INTEGRAL_POSITION_ERROR,
    NON_NUMERIC_TYPE_ERROR,
    OUT_OF_RANGE_CONVERSION_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

TRUNC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_object",
        expression={"$trunc": {}},
        error_code=NON_NUMERIC_TYPE_ERROR,
        msg="Should reject non-numeric object input",
    ),
    ExpressionTestCase(
        "invalid_positive_place_101",
        expression={"$trunc": [123456789012345.123, 101]},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject place value 101 (out of bounds)",
    ),
    ExpressionTestCase(
        "invalid_negative_place_21",
        expression={"$trunc": [123456789012345.123, -21]},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject place value -21 (out of bounds)",
    ),
    ExpressionTestCase(
        "place_non_integral",
        expression={"$trunc": [1, 10.5]},
        error_code=NON_INTEGRAL_POSITION_ERROR,
        msg="Should reject non-integral double place",
    ),
    ExpressionTestCase(
        "place_nan",
        expression={"$trunc": [1, FLOAT_NAN]},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="Should reject NaN place",
    ),
    ExpressionTestCase(
        "place_decimal_nan",
        expression={"$trunc": [1, DECIMAL128_NAN]},
        error_code=NON_INTEGRAL_POSITION_ERROR,
        msg="Should reject Decimal128 NaN place",
    ),
    ExpressionTestCase(
        "place_string",
        expression={"$trunc": [1, "2"]},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject string place",
    ),
    ExpressionTestCase(
        "place_binary",
        expression={"$trunc": [1, Binary(b"", 0)]},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject binary place",
    ),
    ExpressionTestCase(
        "place_int64_out_of_bounds",
        expression={"$trunc": [1, Int64(101)]},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject Int64 place out of bounds",
    ),
    ExpressionTestCase(
        "place_decimal_out_of_bounds",
        expression={"$trunc": [1, Decimal128("-21")]},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject Decimal128 place out of bounds",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$trunc": [1, 2, 3]},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="Should reject 3-argument arity",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$trunc": []},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="Should reject empty array arity",
    ),
    ExpressionTestCase(
        "place_infinity",
        expression={"$trunc": [1.5, FLOAT_INFINITY]},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="Should reject infinity place",
    ),
    ExpressionTestCase(
        "place_negative_infinity",
        expression={"$trunc": [1.5, FLOAT_NEGATIVE_INFINITY]},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="Should reject negative infinity place",
    ),
    ExpressionTestCase(
        "place_bool",
        expression={"$trunc": [1.5, True]},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject boolean place",
    ),
    ExpressionTestCase(
        "place_object",
        expression={"$trunc": [1.5, {"a": 1}]},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject object place",
    ),
    ExpressionTestCase(
        "place_array_value",
        expression={"$trunc": [1.5, [2]]},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject array place",
    ),
    ExpressionTestCase(
        "place_decimal_fractional",
        expression={"$trunc": [1.5, Decimal128("0.5")]},
        error_code=NON_INTEGRAL_POSITION_ERROR,
        msg="Should reject fractional decimal128 place",
    ),
]


TRUNC_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_object",
        expression={"$trunc": "$value"},
        doc={"value": {}},
        error_code=NON_NUMERIC_TYPE_ERROR,
        msg="Should reject non-numeric object input",
    ),
    ExpressionTestCase(
        "invalid_positive_place_101",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": 101},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject place value 101 (out of bounds)",
    ),
    ExpressionTestCase(
        "invalid_negative_place_21",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 123456789012345.123, "place": -21},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject place value -21 (out of bounds)",
    ),
    ExpressionTestCase(
        "place_non_integral",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": 10.5},
        error_code=NON_INTEGRAL_POSITION_ERROR,
        msg="Should reject non-integral double place",
    ),
    ExpressionTestCase(
        "place_nan",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": FLOAT_NAN},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="Should reject NaN place",
    ),
    ExpressionTestCase(
        "place_decimal_nan",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": DECIMAL128_NAN},
        error_code=NON_INTEGRAL_POSITION_ERROR,
        msg="Should reject Decimal128 NaN place",
    ),
    ExpressionTestCase(
        "place_string",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": "2"},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject string place",
    ),
    ExpressionTestCase(
        "place_binary",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": Binary(b"", 0)},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject binary place",
    ),
    ExpressionTestCase(
        "place_int64_out_of_bounds",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": Int64(101)},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject Int64 place out of bounds",
    ),
    ExpressionTestCase(
        "place_decimal_out_of_bounds",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1, "place": Decimal128("-21")},
        error_code=INVALID_POSITION_ERROR,
        msg="Should reject Decimal128 place out of bounds",
    ),
    ExpressionTestCase(
        "empty_array_value",
        expression={"$trunc": "$value"},
        doc={"value": []},
        error_code=NON_NUMERIC_TYPE_ERROR,
        msg="Should reject non-numeric empty array input",
    ),
    ExpressionTestCase(
        "place_infinity",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.5, "place": FLOAT_INFINITY},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="Should reject infinity place",
    ),
    ExpressionTestCase(
        "place_negative_infinity",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.5, "place": FLOAT_NEGATIVE_INFINITY},
        error_code=OUT_OF_RANGE_CONVERSION_ERROR,
        msg="Should reject negative infinity place",
    ),
    ExpressionTestCase(
        "place_bool",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.5, "place": True},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject boolean place",
    ),
    ExpressionTestCase(
        "place_object",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.5, "place": {"a": 1}},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject object place",
    ),
    ExpressionTestCase(
        "place_array_value",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.5, "place": [2]},
        error_code=INVALID_TYPE_ERROR,
        msg="Should reject array place",
    ),
    ExpressionTestCase(
        "place_decimal_fractional",
        expression={"$trunc": ["$value", "$place"]},
        doc={"value": 1.5, "place": Decimal128("0.5")},
        error_code=NON_INTEGRAL_POSITION_ERROR,
        msg="Should reject fractional decimal128 place",
    ),
    ExpressionTestCase(
        "composite_array_field",
        expression={"$trunc": "$x.y"},
        doc={"x": [{"y": 9.876}, {"y": 2}]},
        error_code=NON_NUMERIC_TYPE_ERROR,
        msg="Should reject composite array from $x.y on array-of-objects",
    ),
    ExpressionTestCase(
        "array_index_path",
        expression={"$trunc": ["$arr.0", 1]},
        doc={"arr": [1.567, 2.345]},
        error_code=NON_NUMERIC_TYPE_ERROR,
        msg="Should reject $arr.0 on an array (no positional indexing)",
    ),
    ExpressionTestCase(
        "array_index_on_object_key",
        expression={"$trunc": ["$a.0.b", 1]},
        doc={"a": [{"b": 1.567}, {"b": 2.345}]},
        error_code=NON_NUMERIC_TYPE_ERROR,
        msg="Should reject $a.0.b on array-of-objects (no positional indexing)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TRUNC_LITERAL_TESTS))
def test_trunc_literal(collection, test):
    """Test $trunc with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(TRUNC_INSERT_TESTS))
def test_trunc_insert(collection, test):
    """Test $trunc with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
