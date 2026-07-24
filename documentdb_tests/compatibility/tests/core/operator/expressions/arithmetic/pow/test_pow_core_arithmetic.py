"""
Core arithmetic tests for $pow expression.

Covers $pow across every same-type and cross-type pairing of the four
numeric BSON types (int32, int64, double, decimal128).
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
)
from documentdb_tests.framework.parametrize import pytest_params

POW_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        expression={"$pow": [2, 3]},
        expected=8,
        msg="Should handle same type int32",
    ),
    ExpressionTestCase(
        "same_type_int64",
        expression={"$pow": [Int64(2), Int64(10)]},
        expected=Int64(1024),
        msg="Should handle same type int64",
    ),
    ExpressionTestCase(
        "same_type_double",
        expression={"$pow": [2.0, 3.0]},
        expected=8.0,
        msg="Should handle same type double",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        expression={"$pow": [Decimal128("2"), Decimal128("3")]},
        expected=Decimal128("8.000000000000000000000000000000000"),
        msg="Should compute $pow of decimal values",
    ),
    ExpressionTestCase(
        "int32_int64",
        expression={"$pow": [2, Int64(10)]},
        expected=Int64(1024),
        msg="Should handle int32 int64",
    ),
    ExpressionTestCase(
        "int32_double",
        expression={"$pow": [2, 3.0]},
        expected=8.0,
        msg="Should handle int32 double",
    ),
    ExpressionTestCase(
        "int32_decimal",
        expression={"$pow": [2, Decimal128("3")]},
        expected=Decimal128("8.000000000000000000000000000000000"),
        msg="Should handle int32 decimal",
    ),
    ExpressionTestCase(
        "int64_double",
        expression={"$pow": [Int64(2), 10.0]},
        expected=1024.0,
        msg="Should handle int64 double",
    ),
    ExpressionTestCase(
        "int64_decimal",
        expression={"$pow": [Int64(2), Decimal128("10")]},
        expected=Decimal128("1024.000000000000000000000000000000"),
        msg="Should handle int64 decimal",
    ),
    ExpressionTestCase(
        "double_decimal",
        expression={"$pow": [2.0, Decimal128("3")]},
        expected=Decimal128("8.000000000000000000000000000000000"),
        msg="Should handle double decimal",
    ),
    ExpressionTestCase(
        "power_zero",
        expression={"$pow": [10, 0]},
        expected=1,
        msg="Should handle power zero",
    ),
    ExpressionTestCase(
        "power_one",
        expression={"$pow": [10, 1]},
        expected=10,
        msg="Should return correct result for power one",
    ),
    ExpressionTestCase(
        "power_two",
        expression={"$pow": [10, 2]},
        expected=100,
        msg="Should return correct result for power two",
    ),
    ExpressionTestCase(
        "two_to_ten",
        expression={"$pow": [2, 10]},
        expected=1024,
        msg="Should return correct result for two to ten",
    ),
    ExpressionTestCase(
        "three_to_four",
        expression={"$pow": [3, 4]},
        expected=81,
        msg="Should return correct result for three to four",
    ),
    ExpressionTestCase(
        "five_to_three",
        expression={"$pow": [5, 3]},
        expected=125,
        msg="Should return correct result for five to three",
    ),
    ExpressionTestCase(
        "square_root",
        expression={"$pow": [4, 0.5]},
        expected=2.0,
        msg="Should return correct result for square root",
    ),
    ExpressionTestCase(
        "cube_root",
        expression={"$pow": [8, 1.0 / 3.0]},
        expected=pytest.approx(2.0),
        msg="Should return correct result for cube root",
    ),
    ExpressionTestCase(
        "fourth_root",
        expression={"$pow": [16, 0.25]},
        expected=2.0,
        msg="Should return correct result for fourth root",
    ),
    ExpressionTestCase(
        "fractional_both",
        expression={"$pow": [2.5, 2.5]},
        expected=pytest.approx(9.882117688026186),
        msg="Should handle fractional both",
    ),
    ExpressionTestCase(
        "negative_exponent",
        expression={"$pow": [2, -1]},
        expected=0.5,
        msg="Should handle negative exponent",
    ),
    ExpressionTestCase(
        "negative_exponent_ten",
        expression={"$pow": [10, -2]},
        expected=0.01,
        msg="Should handle negative exponent ten",
    ),
    ExpressionTestCase(
        "negative_exponent_five",
        expression={"$pow": [5, -3]},
        expected=0.008,
        msg="Should handle negative exponent five",
    ),
    ExpressionTestCase(
        "negative_base_odd",
        expression={"$pow": [-2, 3]},
        expected=-8,
        msg="Should handle negative base odd",
    ),
    ExpressionTestCase(
        "negative_base_even",
        expression={"$pow": [-2, 4]},
        expected=16,
        msg="Should handle negative base even",
    ),
    ExpressionTestCase(
        "negative_one_even",
        expression={"$pow": [-1, 100]},
        expected=1,
        msg="Should handle negative one even",
    ),
    ExpressionTestCase(
        "negative_one_odd",
        expression={"$pow": [-1, 101]},
        expected=-1,
        msg="Should handle negative one odd",
    ),
    ExpressionTestCase(
        "zero_base",
        expression={"$pow": [0, 5]},
        expected=0,
        msg="Should handle zero base",
    ),
    ExpressionTestCase(
        "zero_to_zero",
        expression={"$pow": [0, 0]},
        expected=1,
        msg="Should handle zero to zero",
    ),
    ExpressionTestCase(
        "zero_double_to_zero",
        expression={"$pow": [0.0, 0.0]},
        expected=1.0,
        msg="Should handle zero double to zero",
    ),
    ExpressionTestCase(
        "one_base",
        expression={"$pow": [1, 1000]},
        expected=1,
        msg="Should return correct result for one base",
    ),
    ExpressionTestCase(
        "one_base_negative_exp",
        expression={"$pow": [1, -1000]},
        expected=1,
        msg="Should handle one base negative exp",
    ),
    ExpressionTestCase(
        "negative_one_base_negative_one_exp",
        expression={"$pow": [-1, -1]},
        expected=-1,
        msg="Should handle negative base with negative integer exponent (reciprocal, odd)",
    ),
    ExpressionTestCase(
        "negative_one_base_negative_two_exp",
        expression={"$pow": [-1, -2]},
        expected=1,
        msg="Should handle negative base with negative integer exponent (reciprocal, even)",
    ),
    ExpressionTestCase(
        "zero_base_fractional_positive_exp",
        expression={"$pow": [0, 0.5]},
        expected=0.0,
        msg="Should handle zero base with fractional positive exponent",
    ),
    ExpressionTestCase(
        "expression_operator_inputs",
        expression={"$pow": [{"$add": [1, 1]}, {"$subtract": [4, 2]}]},
        expected=4,
        msg="Should handle expression-operator inputs for base and exponent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POW_LITERAL_TESTS))
def test_pow_literal(collection, test):
    """Test $pow from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
