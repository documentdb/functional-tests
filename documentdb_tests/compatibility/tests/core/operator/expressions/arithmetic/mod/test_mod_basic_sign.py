"""
Basic arithmetic and sign-handling tests for $mod expression.

Covers correct remainder computation across sign combinations of the
dividend and divisor, plus a fractional operand case.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

MOD_BASIC_SIGN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "remainder_two",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": 4},
        expected=2,
        msg="Should return correct remainder",
    ),
    ExpressionTestCase(
        "smaller_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 5, "divisor": 10},
        expected=5,
        msg="Should return dividend when smaller than divisor",
    ),
    ExpressionTestCase(
        "negative_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": -10, "divisor": 3},
        expected=-1,
        msg="Should preserve sign of negative dividend",
    ),
    ExpressionTestCase(
        "negative_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": -3},
        expected=1,
        msg="Should return positive remainder for negative divisor",
    ),
    ExpressionTestCase(
        "both_negative",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": -10, "divisor": -3},
        expected=-1,
        msg="Should preserve dividend sign when both negative",
    ),
    ExpressionTestCase(
        "zero_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 0, "divisor": 5},
        expected=0,
        msg="Should return 0 when dividend is zero",
    ),
    ExpressionTestCase(
        "small_fractional",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 5.5, "divisor": 2.5},
        expected=pytest.approx(0.5),
        msg="Should handle small fractional operands",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_BASIC_SIGN_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_BASIC_SIGN_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
