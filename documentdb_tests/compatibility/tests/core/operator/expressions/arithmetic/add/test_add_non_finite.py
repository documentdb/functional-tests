"""Tests for $add infinity and NaN propagation."""

import math

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Infinity]: $add propagates infinity according to IEEE 754 rules.
ADD_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity",
        doc={"a": FLOAT_INFINITY, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$add should return infinity when adding infinity and a finite number",
    ),
    ExpressionTestCase(
        "negative_infinity",
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$add should return negative infinity when adding negative infinity and a finite number",  # noqa: E501
    ),
    ExpressionTestCase(
        "single_infinity",
        doc={"a": FLOAT_INFINITY},
        expression={"$add": ["$a"]},
        expected=FLOAT_INFINITY,
        msg="$add should return infinity for a single infinity operand",
    ),
    ExpressionTestCase(
        "inf_plus_inf",
        doc={"a": FLOAT_INFINITY, "b": FLOAT_INFINITY},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$add should return infinity when adding two positive infinities",
    ),
    ExpressionTestCase(
        "neg_inf_plus_neg_inf",
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$add should return negative infinity when adding two negative infinities",
    ),
    ExpressionTestCase(
        "inf_plus_zero",
        doc={"a": FLOAT_INFINITY, "b": 0},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_INFINITY,
        msg="$add should return infinity when adding infinity and zero",
    ),
    ExpressionTestCase(
        "neg_inf_plus_zero",
        doc={"a": FLOAT_NEGATIVE_INFINITY, "b": 0},
        expression={"$add": ["$a", "$b"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$add should return negative infinity when adding negative infinity and zero",
    ),
    ExpressionTestCase(
        "decimal_infinity",
        doc={"a": DECIMAL128_INFINITY, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_INFINITY,
        msg="$add should return decimal128 infinity when adding decimal128 infinity and a number",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity",
        doc={"a": DECIMAL128_NEGATIVE_INFINITY, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$add should return decimal128 negative infinity when adding decimal128 negative infinity and a number",  # noqa: E501
    ),
]

# Property [NaN]: $add propagates NaN according to IEEE 754 rules.
ADD_NAN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nan_add_one",
        doc={"a": FLOAT_NAN, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$add should return NaN when adding float NaN and a finite number",
    ),
    ExpressionTestCase(
        "inf_minus_inf",
        doc={"a": FLOAT_INFINITY, "b": FLOAT_NEGATIVE_INFINITY},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$add should return NaN when adding float infinity and negative infinity",
    ),
    ExpressionTestCase(
        "nan_plus_nan",
        doc={"a": FLOAT_NAN, "b": FLOAT_NAN},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$add should return NaN when adding two float NaN values",
    ),
    ExpressionTestCase(
        "nan_plus_inf",
        doc={"a": FLOAT_NAN, "b": FLOAT_INFINITY},
        expression={"$add": ["$a", "$b"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$add should return NaN when adding float NaN and infinity",
    ),
    ExpressionTestCase(
        "decimal_nan",
        doc={"a": DECIMAL128_NAN, "b": 1},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$add should return decimal128 NaN when adding decimal128 NaN and a number",
    ),
    ExpressionTestCase(
        "decimal_nan_plus_nan",
        doc={"a": DECIMAL128_NAN, "b": DECIMAL128_NAN},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$add should return decimal128 NaN when adding two decimal128 NaN values",
    ),
    ExpressionTestCase(
        "decimal_inf_minus_inf",
        doc={"a": DECIMAL128_INFINITY, "b": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_NAN,
        msg="$add should return decimal128 NaN when adding decimal128 infinity and negative infinity",  # noqa: E501
    ),
]

ADD_NON_FINITE_ALL_TESTS = ADD_INFINITY_TESTS + ADD_NAN_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ADD_NON_FINITE_ALL_TESTS))
def test_add_non_finite(collection, test_case: ExpressionTestCase):
    """Test $add infinity and NaN propagation cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
