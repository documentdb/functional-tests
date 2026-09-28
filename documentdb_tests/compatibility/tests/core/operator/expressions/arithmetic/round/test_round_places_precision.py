"""
High-precision and place-range tests for $round expression.

Covers decimal128 34-digit place rounding, negative-place range sweeps on
large doubles, and double precision-limit places.
"""

import pytest
from bson import (
    Decimal128,
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

ROUND_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "place_32",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 32]},
        expected=Decimal128("1.12345678901234567890123456789012"),
        msg="decimal128 rounds to 32 places (drops the last of 33 fractional digits)",
    ),
    ExpressionTestCase(
        "place_33",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 33]},
        expected=Decimal128("1.123456789012345678901234567890123"),
        msg="decimal128 rounds to 33 places (all fractional digits retained)",
    ),
    ExpressionTestCase(
        "place_34",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 34]},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="decimal128 rounds to 34 places (pads one trailing zero)",
    ),
    ExpressionTestCase(
        "place_99",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 99]},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="decimal128 place 99 exceeds precision; value retained",
    ),
    ExpressionTestCase(
        "place_100",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 100]},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="decimal128 place 100 (max) exceeds precision; value retained",
    ),
    ExpressionTestCase(
        "neg_place_-1",
        expression={"$round": [123456789012345.12, -1]},
        expected=pytest.approx(123456789012350.0),
        msg="large double at place -1 rounds to the nearest ten",
    ),
    ExpressionTestCase(
        "neg_place_-2",
        expression={"$round": [123456789012345.12, -2]},
        expected=123456789012300.0,
        msg="large double at place -2 rounds to the nearest hundred",
    ),
    ExpressionTestCase(
        "neg_place_-12",
        expression={"$round": [123456789012345.12, -12]},
        expected=123000000000000.0,
        msg="large double at place -12 rounds to the nearest 1e12",
    ),
    ExpressionTestCase(
        "neg_place_-14",
        expression={"$round": [123456789012345.12, -14]},
        expected=100000000000000.0,
        msg="large double at place -14 rounds to the nearest 1e14",
    ),
    ExpressionTestCase(
        "neg_place_-15",
        expression={"$round": [123456789012345.12, -15]},
        expected=0.0,
        msg="large double at place -15 rounds down to 0.0",
    ),
    ExpressionTestCase(
        "neg_place_-19",
        expression={"$round": [123456789012345.12, -19]},
        expected=0.0,
        msg="large double at place -19 rounds down to 0.0",
    ),
    ExpressionTestCase(
        "neg_place_-20",
        expression={"$round": [123456789012345.12, -20]},
        expected=0.0,
        msg="large double at place -20 (min) rounds down to 0.0",
    ),
    ExpressionTestCase(
        "double_place_0",
        expression={"$round": [1.12345678901234, 0]},
        expected=1.0,
        msg="double 1.12345678901234 rounds to 1.0 at place 0",
    ),
    ExpressionTestCase(
        "double_place_2",
        expression={"$round": [1.12345678901234, 2]},
        expected=1.12,
        msg="double 1.12345678901234 rounds to 1.12 at place 2",
    ),
    ExpressionTestCase(
        "double_place_13",
        expression={"$round": [1.12345678901234, 13]},
        expected=1.1234567890123,
        msg="double rounds to 13 places (near double precision limit)",
    ),
    ExpressionTestCase(
        "double_place_14",
        expression={"$round": [1.12345678901234, 14]},
        expected=1.12345678901234,
        msg="double rounds to 14 places (full input precision, unchanged)",
    ),
    ExpressionTestCase(
        "double_place_20",
        expression={"$round": [1.12345678901234, 20]},
        expected=1.12345678901234,
        msg="place 20 exceeds double precision; value returned unchanged",
    ),
    ExpressionTestCase(
        "decimal_place_0",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 0]},
        expected=Decimal128("1"),
        msg="34-digit decimal rounds to 1 at place 0",
    ),
    ExpressionTestCase(
        "decimal_place_2",
        expression={"$round": [Decimal128("1.123456789012345678901234567890123"), 2]},
        expected=Decimal128("1.12"),
        msg="34-digit decimal rounds to 1.12 at place 2",
    ),
]

ROUND_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "place_32",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 32},
        expected=Decimal128("1.12345678901234567890123456789012"),
        msg="decimal128 rounds to 32 places (drops the last of 33 fractional digits)",
    ),
    ExpressionTestCase(
        "place_100",
        expression={"$round": ["$value", "$place"]},
        doc={"value": Decimal128("1.123456789012345678901234567890123"), "place": 100},
        expected=Decimal128("1.1234567890123456789012345678901230"),
        msg="decimal128 place 100 (max) exceeds precision; value retained",
    ),
    ExpressionTestCase(
        "neg_place_-20",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 123456789012345.12, "place": -20},
        expected=0.0,
        msg="large double at place -20 (min) rounds down to 0.0",
    ),
    ExpressionTestCase(
        "double_place_14",
        expression={"$round": ["$value", "$place"]},
        doc={"value": 1.12345678901234, "place": 14},
        expected=1.12345678901234,
        msg="double rounds to 14 places (full input precision, unchanged)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ROUND_LITERAL_TESTS))
def test_round_literal(collection, test):
    """Test $round with literal values"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ROUND_INSERT_TESTS))
def test_round_insert(collection, test):
    """Test $round with inserted document values"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
