import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_JUST_ABOVE_HALF,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_HALF,
    DOUBLE_JUST_ABOVE_HALF,
    DOUBLE_JUST_BELOW_HALF,
    DOUBLE_NEGATIVE_HALF,
    DOUBLE_NEGATIVE_ONE_AND_HALF,
    DOUBLE_ONE_AND_HALF,
)

MULTIPLY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_half_times_two",
        expression={"$multiply": [DOUBLE_HALF, 2]},
        expected=1.0,
        msg="Should handle double half times two",
    ),
    ExpressionTestCase(
        "double_one_and_half_times_two",
        expression={"$multiply": [DOUBLE_ONE_AND_HALF, 2]},
        expected=3.0,
        msg="Should handle double one and half times two",
    ),
    ExpressionTestCase(
        "double_negative_half_times_two",
        expression={"$multiply": [DOUBLE_NEGATIVE_HALF, 2]},
        expected=-1.0,
        msg="Should handle double negative half times two",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half_times_two",
        expression={"$multiply": [DOUBLE_NEGATIVE_ONE_AND_HALF, 2]},
        expected=-3.0,
        msg="Should handle double negative one and half times two",
    ),
    ExpressionTestCase(
        "double_just_below_half_times_two",
        expression={"$multiply": [DOUBLE_JUST_BELOW_HALF, 2]},
        expected=pytest.approx(0.9999999999999988),
        msg="Should handle double just below half times two",
    ),
    ExpressionTestCase(
        "double_just_above_half_times_two",
        expression={"$multiply": [DOUBLE_JUST_ABOVE_HALF, 2]},
        expected=pytest.approx(1.000000002),
        msg="Should handle double just above half times two",
    ),
    ExpressionTestCase(
        "double_half_times_half",
        expression={"$multiply": [DOUBLE_HALF, DOUBLE_HALF]},
        expected=0.25,
        msg="Should handle double half times half",
    ),
    ExpressionTestCase(
        "double_one_and_half_times_one_and_half",
        expression={"$multiply": [DOUBLE_ONE_AND_HALF, DOUBLE_ONE_AND_HALF]},
        expected=2.25,
        msg="Should handle double one and half times one and half",
    ),
    ExpressionTestCase(
        "decimal_half_times_two",
        expression={"$multiply": [DECIMAL128_HALF, 2]},
        expected=Decimal128("1.0"),
        msg="Should return correct result for decimal half times two",
    ),
    ExpressionTestCase(
        "decimal_one_and_half_times_two",
        expression={"$multiply": [DECIMAL128_ONE_AND_HALF, 2]},
        expected=Decimal128("3.0"),
        msg="Should return correct result for decimal one and half times two",
    ),
    ExpressionTestCase(
        "decimal_two_and_half_times_two",
        expression={"$multiply": [DECIMAL128_TWO_AND_HALF, 2]},
        expected=Decimal128("5.0"),
        msg="Should return correct result for decimal two and half times two",
    ),
    ExpressionTestCase(
        "decimal_negative_half_times_two",
        expression={"$multiply": [DECIMAL128_NEGATIVE_HALF, 2]},
        expected=Decimal128("-1.0"),
        msg="Should handle decimal negative half times two",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half_times_two",
        expression={"$multiply": [DECIMAL128_NEGATIVE_ONE_AND_HALF, 2]},
        expected=Decimal128("-3.0"),
        msg="Should handle decimal negative one and half times two",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_times_two",
        expression={"$multiply": [DECIMAL128_JUST_BELOW_HALF, 2]},
        expected=Decimal128("0.9999999999999999999999999999999998"),
        msg="Should return correct result for decimal just below half times two",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_times_two",
        expression={"$multiply": [DECIMAL128_JUST_ABOVE_HALF, 2]},
        expected=Decimal128("1.000000000000000000000000000000000"),
        msg="Should return correct result for decimal just above half times two",
    ),
    ExpressionTestCase(
        "decimal_half_times_half",
        expression={"$multiply": [DECIMAL128_HALF, DECIMAL128_HALF]},
        expected=Decimal128("0.25"),
        msg="Should return correct result for decimal half times half",
    ),
]


MULTIPLY_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_HALF, "val1": 2},
        expected=1.0,
        msg="Should handle double half times two",
    ),
    ExpressionTestCase(
        "double_one_and_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_ONE_AND_HALF, "val1": 2},
        expected=3.0,
        msg="Should handle double one and half times two",
    ),
    ExpressionTestCase(
        "double_negative_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_NEGATIVE_HALF, "val1": 2},
        expected=-1.0,
        msg="Should handle double negative half times two",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_NEGATIVE_ONE_AND_HALF, "val1": 2},
        expected=-3.0,
        msg="Should handle double negative one and half times two",
    ),
    ExpressionTestCase(
        "double_just_below_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_JUST_BELOW_HALF, "val1": 2},
        expected=pytest.approx(0.9999999999999988),
        msg="Should handle double just below half times two",
    ),
    ExpressionTestCase(
        "double_just_above_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_JUST_ABOVE_HALF, "val1": 2},
        expected=pytest.approx(1.000000002),
        msg="Should handle double just above half times two",
    ),
    ExpressionTestCase(
        "double_half_times_half",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_HALF, "val1": DOUBLE_HALF},
        expected=0.25,
        msg="Should handle double half times half",
    ),
    ExpressionTestCase(
        "double_one_and_half_times_one_and_half",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DOUBLE_ONE_AND_HALF, "val1": DOUBLE_ONE_AND_HALF},
        expected=2.25,
        msg="Should handle double one and half times one and half",
    ),
    ExpressionTestCase(
        "decimal_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_HALF, "val1": 2},
        expected=Decimal128("1.0"),
        msg="Should return correct result for decimal half times two",
    ),
    ExpressionTestCase(
        "decimal_one_and_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_ONE_AND_HALF, "val1": 2},
        expected=Decimal128("3.0"),
        msg="Should return correct result for decimal one and half times two",
    ),
    ExpressionTestCase(
        "decimal_two_and_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_TWO_AND_HALF, "val1": 2},
        expected=Decimal128("5.0"),
        msg="Should return correct result for decimal two and half times two",
    ),
    ExpressionTestCase(
        "decimal_negative_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_NEGATIVE_HALF, "val1": 2},
        expected=Decimal128("-1.0"),
        msg="Should handle decimal negative half times two",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_NEGATIVE_ONE_AND_HALF, "val1": 2},
        expected=Decimal128("-3.0"),
        msg="Should handle decimal negative one and half times two",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_JUST_BELOW_HALF, "val1": 2},
        expected=Decimal128("0.9999999999999999999999999999999998"),
        msg="Should return correct result for decimal just below half times two",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_times_two",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_JUST_ABOVE_HALF, "val1": 2},
        expected=Decimal128("1.000000000000000000000000000000000"),
        msg="Should return correct result for decimal just above half times two",
    ),
    ExpressionTestCase(
        "decimal_half_times_half",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": DECIMAL128_HALF, "val1": DECIMAL128_HALF},
        expected=Decimal128("0.25"),
        msg="Should return correct result for decimal half times half",
    ),
]


MULTIPLY_MIXED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DOUBLE_HALF},
        expected=1.0,
        msg="Should handle double half times two",
    ),
    ExpressionTestCase(
        "double_one_and_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DOUBLE_ONE_AND_HALF},
        expected=3.0,
        msg="Should handle double one and half times two",
    ),
    ExpressionTestCase(
        "double_negative_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DOUBLE_NEGATIVE_HALF},
        expected=-1.0,
        msg="Should handle double negative half times two",
    ),
    ExpressionTestCase(
        "double_negative_one_and_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DOUBLE_NEGATIVE_ONE_AND_HALF},
        expected=-3.0,
        msg="Should handle double negative one and half times two",
    ),
    ExpressionTestCase(
        "double_just_below_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DOUBLE_JUST_BELOW_HALF},
        expected=pytest.approx(0.9999999999999988),
        msg="Should handle double just below half times two",
    ),
    ExpressionTestCase(
        "double_just_above_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DOUBLE_JUST_ABOVE_HALF},
        expected=pytest.approx(1.000000002),
        msg="Should handle double just above half times two",
    ),
    ExpressionTestCase(
        "double_half_times_half",
        expression={"$multiply": ["$val0", DOUBLE_HALF]},
        doc={"val0": DOUBLE_HALF},
        expected=0.25,
        msg="Should handle double half times half",
    ),
    ExpressionTestCase(
        "double_one_and_half_times_one_and_half",
        expression={"$multiply": ["$val0", DOUBLE_ONE_AND_HALF]},
        doc={"val0": DOUBLE_ONE_AND_HALF},
        expected=2.25,
        msg="Should handle double one and half times one and half",
    ),
    ExpressionTestCase(
        "decimal_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_HALF},
        expected=Decimal128("1.0"),
        msg="Should return correct result for decimal half times two",
    ),
    ExpressionTestCase(
        "decimal_one_and_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_ONE_AND_HALF},
        expected=Decimal128("3.0"),
        msg="Should return correct result for decimal one and half times two",
    ),
    ExpressionTestCase(
        "decimal_two_and_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("5.0"),
        msg="Should return correct result for decimal two and half times two",
    ),
    ExpressionTestCase(
        "decimal_negative_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_NEGATIVE_HALF},
        expected=Decimal128("-1.0"),
        msg="Should handle decimal negative half times two",
    ),
    ExpressionTestCase(
        "decimal_negative_one_and_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_NEGATIVE_ONE_AND_HALF},
        expected=Decimal128("-3.0"),
        msg="Should handle decimal negative one and half times two",
    ),
    ExpressionTestCase(
        "decimal_just_below_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_JUST_BELOW_HALF},
        expected=Decimal128("0.9999999999999999999999999999999998"),
        msg="Should return correct result for decimal just below half times two",
    ),
    ExpressionTestCase(
        "decimal_just_above_half_times_two",
        expression={"$multiply": ["$val0", 2]},
        doc={"val0": DECIMAL128_JUST_ABOVE_HALF},
        expected=Decimal128("1.000000000000000000000000000000000"),
        msg="Should return correct result for decimal just above half times two",
    ),
    ExpressionTestCase(
        "decimal_half_times_half",
        expression={"$multiply": ["$val0", DECIMAL128_HALF]},
        doc={"val0": DECIMAL128_HALF},
        expected=Decimal128("0.25"),
        msg="Should return correct result for decimal half times half",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_LITERAL_TESTS))
def test_multiply_literal(collection, test):
    """Test $multiply from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_INSERT_TESTS))
def test_multiply_insert(collection, test):
    """Test $multiply from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_MIXED_TESTS))
def test_multiply_mixed(collection, test):
    """Test $multiply mixed literal and document"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
