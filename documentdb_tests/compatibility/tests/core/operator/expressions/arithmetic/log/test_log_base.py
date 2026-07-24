"""Tests for $log with non-integer bases, including fractional bases and bases near one."""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Fractional Base]: $log with a positive non-integer base returns the correct result,
# negative when the base is below one.
LOG_FRACTIONAL_BASE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base_half",
        doc={"value": 100, "base": 0.5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-6.643856189774725),
        msg="$log should return the base one half log of one hundred",
    ),
    ExpressionTestCase(
        "base_quarter",
        doc={"value": 100, "base": 0.25},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-3.3219280948873626),
        msg="$log should return the base one quarter log of one hundred",
    ),
    ExpressionTestCase(
        "base_1_5",
        doc={"value": 100, "base": 1.5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(11.357747174535147),
        msg="$log should return the base one and a half log of one hundred",
    ),
    ExpressionTestCase(
        "base_0_9",
        doc={"value": 100, "base": 0.9},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-43.708690653565675),
        msg="$log should return the base nine tenths log of one hundred",
    ),
    ExpressionTestCase(
        "base_0_1",
        doc={"value": 100, "base": 0.1},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-2.0),
        msg="$log should return negative two for one hundred in base one tenth",
    ),
    ExpressionTestCase(
        "base_0_01",
        doc={"value": 100, "base": 0.01},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-1.0),
        msg="$log should return negative one for one hundred in base one hundredth",
    ),
]

# Property [Base Near One]: $log with a base just above or below one returns a large-magnitude
# result of the corresponding sign.
LOG_BASE_NEAR_ONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "base_near_one_above",
        doc={"value": 10, "base": 1.0001},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(23027.002203302243),
        msg="$log should return a large positive result for a base just above one",
    ),
    ExpressionTestCase(
        "base_near_one_below",
        doc={"value": 10, "base": 0.9999},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(-23024.699618207327),
        msg="$log should return a large negative result for a base just below one",
    ),
]

# Property [Both Below One]: $log with both value and base below one returns a positive result,
# since value and base lie on the same side of one.
LOG_BOTH_BELOW_ONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "quarter_base_half",
        doc={"value": 0.25, "base": 0.5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(2.0),
        msg="$log should return two for one quarter in base one half",
    ),
    ExpressionTestCase(
        "thousandth_base_tenth",
        doc={"value": 0.001, "base": 0.1},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(3.0),
        msg="$log should return three for one thousandth in base one tenth",
    ),
    ExpressionTestCase(
        "three_tenths_base_half",
        doc={"value": 0.3, "base": 0.5},
        expression={"$log": ["$value", "$base"]},
        expected=pytest.approx(1.7369655941662063),
        msg="$log should return a positive non-integer result for a non-power value and base "
        "both below one",
    ),
]

LOG_BASE_ALL_TESTS = LOG_FRACTIONAL_BASE_TESTS + LOG_BASE_NEAR_ONE_TESTS + LOG_BOTH_BELOW_ONE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(LOG_BASE_ALL_TESTS))
def test_log_base(collection, test_case: ExpressionTestCase):
    """Test $log non-integer base cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
