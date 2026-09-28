"""
Basic truncation tests for $trunc expression.

Covers zero/positive/negative values for all numeric types and
truncate-toward-zero behavior (as opposed to rounding).
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
from documentdb_tests.framework.parametrize import pytest_params

TRUNC_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        expression={"$trunc": 0},
        expected=0,
        msg="Should truncate int32 zero to itself",
    ),
    ExpressionTestCase(
        "int64_zero",
        expression={"$trunc": Int64(0)},
        expected=Int64(0),
        msg="Should truncate int64 zero to itself",
    ),
    ExpressionTestCase(
        "double_zero",
        expression={"$trunc": 0.0},
        expected=0.0,
        msg="Should truncate double zero to itself",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        expression={"$trunc": -0.0},
        expected=-0.0,
        msg="Should preserve the sign of double negative zero",
    ),
    ExpressionTestCase(
        "decimal_zero",
        expression={"$trunc": Decimal128("0")},
        expected=Decimal128("0"),
        msg="Should truncate Decimal128 zero to itself",
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        expression={"$trunc": Decimal128("-0")},
        expected=Decimal128("-0"),
        msg="Should preserve the sign of Decimal128 negative zero",
    ),
    ExpressionTestCase(
        "int32_positive",
        expression={"$trunc": 1},
        expected=1,
        msg="Should truncate positive int32 to itself",
    ),
    ExpressionTestCase(
        "int64_positive",
        expression={"$trunc": Int64(1)},
        expected=Int64(1),
        msg="Should truncate positive int64 to itself",
    ),
    ExpressionTestCase(
        "int32_negative",
        expression={"$trunc": -1},
        expected=-1,
        msg="Should truncate negative int32 to itself",
    ),
    ExpressionTestCase(
        "int64_negative",
        expression={"$trunc": Int64(-1)},
        expected=Int64(-1),
        msg="Should truncate negative int64 to itself",
    ),
    ExpressionTestCase(
        "double_positive",
        expression={"$trunc": 1.9},
        expected=1.0,
        msg="Should truncate positive double toward zero",
    ),
    ExpressionTestCase(
        "double_negative",
        expression={"$trunc": -1.9},
        expected=-1.0,
        msg="Should truncate negative double toward zero",
    ),
    ExpressionTestCase(
        "double_trunc_down",
        expression={"$trunc": 1.4},
        expected=1.0,
        msg="Should truncate (not round) 1.4 down to 1.0",
    ),
    ExpressionTestCase(
        "double_trunc_up",
        expression={"$trunc": 1.6},
        expected=1.0,
        msg="Should truncate (not round) 1.6 down to 1.0",
    ),
    ExpressionTestCase(
        "double_neg_trunc",
        expression={"$trunc": -1.4},
        expected=-1.0,
        msg="Should truncate (not round) -1.4 toward zero to -1.0",
    ),
    ExpressionTestCase(
        "decimal_positive",
        expression={"$trunc": Decimal128("1.9")},
        expected=Decimal128("1"),
        msg="Should truncate positive Decimal128 toward zero",
    ),
    ExpressionTestCase(
        "decimal_negative",
        expression={"$trunc": Decimal128("-1.9")},
        expected=Decimal128("-1"),
        msg="Should truncate negative Decimal128 toward zero",
    ),
    ExpressionTestCase(
        "trunc_positive_large",
        expression={"$trunc": 99.99},
        expected=99.0,
        msg="Should truncate 99.99 down to 99.0",
    ),
    ExpressionTestCase(
        "trunc_negative_large",
        expression={"$trunc": -99.99},
        expected=-99.0,
        msg="Should truncate -99.99 toward zero to -99.0",
    ),
]

TRUNC_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_zero",
        expression={"$trunc": "$value"},
        doc={"value": 0},
        expected=0,
        msg="Should truncate int32 zero to itself",
    ),
    ExpressionTestCase(
        "int64_zero",
        expression={"$trunc": "$value"},
        doc={"value": Int64(0)},
        expected=Int64(0),
        msg="Should truncate int64 zero to itself",
    ),
    ExpressionTestCase(
        "double_zero",
        expression={"$trunc": "$value"},
        doc={"value": 0.0},
        expected=0.0,
        msg="Should truncate double zero to itself",
    ),
    ExpressionTestCase(
        "double_negative_zero",
        expression={"$trunc": "$value"},
        doc={"value": -0.0},
        expected=-0.0,
        msg="Should preserve the sign of double negative zero",
    ),
    ExpressionTestCase(
        "decimal_zero",
        expression={"$trunc": "$value"},
        doc={"value": Decimal128("0")},
        expected=Decimal128("0"),
        msg="Should truncate Decimal128 zero to itself",
    ),
    ExpressionTestCase(
        "decimal_negative_zero",
        expression={"$trunc": "$value"},
        doc={"value": Decimal128("-0")},
        expected=Decimal128("-0"),
        msg="Should preserve the sign of Decimal128 negative zero",
    ),
    ExpressionTestCase(
        "int32_positive",
        expression={"$trunc": "$value"},
        doc={"value": 1},
        expected=1,
        msg="Should truncate positive int32 to itself",
    ),
    ExpressionTestCase(
        "int64_positive",
        expression={"$trunc": "$value"},
        doc={"value": Int64(1)},
        expected=Int64(1),
        msg="Should truncate positive int64 to itself",
    ),
    ExpressionTestCase(
        "int32_negative",
        expression={"$trunc": "$value"},
        doc={"value": -1},
        expected=-1,
        msg="Should truncate negative int32 to itself",
    ),
    ExpressionTestCase(
        "int64_negative",
        expression={"$trunc": "$value"},
        doc={"value": Int64(-1)},
        expected=Int64(-1),
        msg="Should truncate negative int64 to itself",
    ),
    ExpressionTestCase(
        "double_positive",
        expression={"$trunc": "$value"},
        doc={"value": 1.9},
        expected=1.0,
        msg="Should truncate positive double toward zero",
    ),
    ExpressionTestCase(
        "double_negative",
        expression={"$trunc": "$value"},
        doc={"value": -1.9},
        expected=-1.0,
        msg="Should truncate negative double toward zero",
    ),
    ExpressionTestCase(
        "double_trunc_down",
        expression={"$trunc": "$value"},
        doc={"value": 1.4},
        expected=1.0,
        msg="Should truncate (not round) 1.4 down to 1.0",
    ),
    ExpressionTestCase(
        "double_trunc_up",
        expression={"$trunc": "$value"},
        doc={"value": 1.6},
        expected=1.0,
        msg="Should truncate (not round) 1.6 down to 1.0",
    ),
    ExpressionTestCase(
        "double_neg_trunc",
        expression={"$trunc": "$value"},
        doc={"value": -1.4},
        expected=-1.0,
        msg="Should truncate (not round) -1.4 toward zero to -1.0",
    ),
    ExpressionTestCase(
        "decimal_positive",
        expression={"$trunc": "$value"},
        doc={"value": Decimal128("1.9")},
        expected=Decimal128("1"),
        msg="Should truncate positive Decimal128 toward zero",
    ),
    ExpressionTestCase(
        "decimal_negative",
        expression={"$trunc": "$value"},
        doc={"value": Decimal128("-1.9")},
        expected=Decimal128("-1"),
        msg="Should truncate negative Decimal128 toward zero",
    ),
    ExpressionTestCase(
        "trunc_positive_large",
        expression={"$trunc": "$value"},
        doc={"value": 99.99},
        expected=99.0,
        msg="Should truncate 99.99 down to 99.0",
    ),
    ExpressionTestCase(
        "trunc_negative_large",
        expression={"$trunc": "$value"},
        doc={"value": -99.99},
        expected=-99.0,
        msg="Should truncate -99.99 toward zero to -99.0",
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
