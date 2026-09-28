"""
Error tests for $mod expression.

Covers non-numeric operand rejection (array/object), zero-divisor rejection
(int, double, int64, Decimal128, including negative zero), and
argument-count/argument-shape errors.
"""

import pytest
from bson import Decimal128, Int64

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
    MODULO_DECIMAL128_ZERO_REMAINDER_ERROR,
    MODULO_NON_NUMERIC_ERROR,
    MODULO_ZERO_REMAINDER_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
)

MOD_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": [], "divisor": 3},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="Should reject empty array dividend",
    ),
    ExpressionTestCase(
        "empty_object_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": {}, "divisor": 3},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="Should reject empty object dividend",
    ),
    ExpressionTestCase(
        "empty_array_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": []},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="Should reject empty array divisor",
    ),
    ExpressionTestCase(
        "empty_object_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": {}},
        error_code=MODULO_NON_NUMERIC_ERROR,
        msg="Should reject empty object divisor",
    ),
    ExpressionTestCase(
        "zero_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": 0},
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="Should reject modulo by zero int",
    ),
    ExpressionTestCase(
        "zero_divisor_double",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": 0.0},
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="Should reject modulo by zero double",
    ),
    ExpressionTestCase(
        "zero_divisor_int64",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": Int64(0)},
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="Should reject modulo by zero int64",
    ),
    ExpressionTestCase(
        "zero_dividend_zero_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 0, "divisor": 0},
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="Should reject 0 mod 0",
    ),
    ExpressionTestCase(
        "decimal_zero_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": Decimal128("0")},
        error_code=MODULO_DECIMAL128_ZERO_REMAINDER_ERROR,
        msg="Should reject modulo by zero decimal128",
    ),
    ExpressionTestCase(
        "decimal_zero_dividend_zero_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": Decimal128("0"), "divisor": Decimal128("0")},
        error_code=MODULO_DECIMAL128_ZERO_REMAINDER_ERROR,
        msg="Should reject decimal 0 mod 0",
    ),
    ExpressionTestCase(
        "negative_zero_double_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": DOUBLE_NEGATIVE_ZERO},
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="Should reject modulo by negative zero double",
    ),
    ExpressionTestCase(
        "negative_zero_decimal_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": DECIMAL128_NEGATIVE_ZERO},
        error_code=MODULO_DECIMAL128_ZERO_REMAINDER_ERROR,
        msg="Should reject modulo by negative zero decimal128",
    ),
]


# Arity/argument-shape errors have no fixed dividend/divisor pair and are
# literal-only; there is no meaningful field-path/insert variant for these.
MOD_ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero_args",
        expression={"$mod": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $mod with zero arguments",
    ),
    ExpressionTestCase(
        "arity_one_arg",
        expression={"$mod": [5]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $mod with a single argument",
    ),
    ExpressionTestCase(
        "arity_three_args",
        expression={"$mod": [10, 3, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $mod with three arguments",
    ),
    ExpressionTestCase(
        "arity_non_array",
        expression={"$mod": 5},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $mod with a non-array operand",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_ERROR_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_ERROR_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_ARITY_TESTS))
def test_mod_arity(collection, test):
    """Test $mod argument-count and argument-shape errors"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
