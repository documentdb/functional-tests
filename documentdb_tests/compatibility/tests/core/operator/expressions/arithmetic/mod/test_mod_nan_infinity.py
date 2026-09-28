"""
NaN and Infinity tests for $mod expression.

Covers every combination of NaN, Infinity, and -Infinity as the dividend
and/or divisor, for both double and Decimal128.
"""

import math

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
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

MOD_NAN_INFINITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_inf_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": FLOAT_NEGATIVE_INFINITY},
        expected=10.0,
        msg="Should return dividend when divisor is -infinity",
    ),
    ExpressionTestCase(
        "decimal_neg_inf_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": DECIMAL128_NEGATIVE_INFINITY},
        expected=Decimal128("10"),
        msg="Should return dividend when divisor is decimal -infinity",
    ),
    ExpressionTestCase(
        "nan_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_NAN, "divisor": 3},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when dividend is NaN",
    ),
    ExpressionTestCase(
        "nan_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when divisor is NaN",
    ),
    ExpressionTestCase(
        "both_nan",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_NAN, "divisor": FLOAT_NAN},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN when both are NaN",
    ),
    ExpressionTestCase(
        "inf_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_INFINITY, "divisor": 3},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity mod finite",
    ),
    ExpressionTestCase(
        "neg_inf_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_NEGATIVE_INFINITY, "divisor": 3},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for -infinity mod finite",
    ),
    ExpressionTestCase(
        "decimal_nan_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_NAN, "divisor": 3},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when dividend is decimal NaN",
    ),
    ExpressionTestCase(
        "decimal_nan_divisor",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": 10, "divisor": DECIMAL128_NAN},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN when divisor is decimal NaN",
    ),
    ExpressionTestCase(
        "decimal_inf_dividend",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_INFINITY, "divisor": 3},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity mod finite",
    ),
    ExpressionTestCase(
        "inf_mod_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_INFINITY, "divisor": FLOAT_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity mod infinity",
    ),
    ExpressionTestCase(
        "neg_inf_mod_neg_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_NEGATIVE_INFINITY, "divisor": FLOAT_NEGATIVE_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for -infinity mod -infinity",
    ),
    ExpressionTestCase(
        "inf_mod_neg_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_INFINITY, "divisor": FLOAT_NEGATIVE_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for infinity mod -infinity",
    ),
    ExpressionTestCase(
        "neg_inf_mod_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": FLOAT_NEGATIVE_INFINITY, "divisor": FLOAT_INFINITY},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="Should return NaN for -infinity mod infinity",
    ),
    ExpressionTestCase(
        "decimal_inf_mod_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_INFINITY, "divisor": DECIMAL128_INFINITY},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity mod decimal infinity",
    ),
    ExpressionTestCase(
        "decimal_neg_inf_mod_neg_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={
            "dividend": DECIMAL128_NEGATIVE_INFINITY,
            "divisor": DECIMAL128_NEGATIVE_INFINITY,
        },
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal -infinity mod decimal -infinity",
    ),
    ExpressionTestCase(
        "decimal_inf_mod_neg_inf",
        expression={"$mod": ["$dividend", "$divisor"]},
        doc={"dividend": DECIMAL128_INFINITY, "divisor": DECIMAL128_NEGATIVE_INFINITY},
        expected=DECIMAL128_NAN,
        msg="Should return decimal NaN for decimal infinity mod decimal -infinity",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MOD_NAN_INFINITY_TESTS))
def test_mod_literal(collection, test):
    """Test $mod from literals"""
    result = execute_expression(collection, {"$mod": [test.doc["dividend"], test.doc["divisor"]]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MOD_NAN_INFINITY_TESTS))
def test_mod_insert(collection, test):
    """Test $mod from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
