"""
Tests for $switch return type preservation in then and default positions.

Verifies that $switch preserves the BSON type of then/default expressions.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

THEN_CASES: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "then_bool",
        expression={"$switch": {"branches": [{"case": True, "then": True}]}},
        expected="bool",
        msg="then should return bool",
    ),
    ExpressionTestCase(
        "then_int",
        expression={"$switch": {"branches": [{"case": True, "then": 42}]}},
        expected="int",
        msg="then should return int",
    ),
    ExpressionTestCase(
        "then_long",
        expression={"$switch": {"branches": [{"case": True, "then": Int64(42)}]}},
        expected="long",
        msg="then should return long",
    ),
    ExpressionTestCase(
        "then_string",
        expression={"$switch": {"branches": [{"case": True, "then": "hello"}]}},
        expected="string",
        msg="then should return string",
    ),
    ExpressionTestCase(
        "then_null",
        expression={"$switch": {"branches": [{"case": True, "then": None}]}},
        expected="null",
        msg="then should return null",
    ),
    ExpressionTestCase(
        "then_array",
        expression={"$switch": {"branches": [{"case": True, "then": [1, 2, 3]}]}},
        expected="array",
        msg="then should return array",
    ),
    ExpressionTestCase(
        "then_date",
        expression={
            "$switch": {
                "branches": [{"case": True, "then": datetime(2026, 1, 1, tzinfo=timezone.utc)}]
            }
        },
        expected="date",
        msg="then should return date",
    ),
    ExpressionTestCase(
        "then_decimal",
        expression={"$switch": {"branches": [{"case": True, "then": Decimal128("3.14")}]}},
        expected="decimal",
        msg="then should return decimal",
    ),
]

DEFAULT_CASES: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "default_bool",
        expression={"$switch": {"branches": [{"case": False, "then": "unused"}], "default": False}},
        expected="bool",
        msg="default should return bool",
    ),
    ExpressionTestCase(
        "default_int",
        expression={"$switch": {"branches": [{"case": False, "then": "unused"}], "default": 42}},
        expected="int",
        msg="default should return int",
    ),
    ExpressionTestCase(
        "default_long",
        expression={
            "$switch": {"branches": [{"case": False, "then": "unused"}], "default": Int64(42)}
        },
        expected="long",
        msg="default should return long",
    ),
    ExpressionTestCase(
        "default_string",
        expression={
            "$switch": {"branches": [{"case": False, "then": "unused"}], "default": "hello"}
        },
        expected="string",
        msg="default should return string",
    ),
    ExpressionTestCase(
        "default_null",
        expression={"$switch": {"branches": [{"case": False, "then": "unused"}], "default": None}},
        expected="null",
        msg="default should return null",
    ),
    ExpressionTestCase(
        "default_array",
        expression={
            "$switch": {"branches": [{"case": False, "then": "unused"}], "default": [1, 2]}
        },
        expected="array",
        msg="default should return array",
    ),
    ExpressionTestCase(
        "default_date",
        expression={
            "$switch": {
                "branches": [{"case": False, "then": "unused"}],
                "default": datetime(2026, 1, 1, tzinfo=timezone.utc),
            }
        },
        expected="date",
        msg="default should return date",
    ),
    ExpressionTestCase(
        "default_decimal",
        expression={
            "$switch": {
                "branches": [{"case": False, "then": "unused"}],
                "default": Decimal128("3.14"),
            }
        },
        expected="decimal",
        msg="default should return decimal",
    ),
]

ALL_TESTS = THEN_CASES + DEFAULT_CASES


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_switch_return_type(collection, test):
    """Test $switch preserves return type in then and default positions."""
    result = execute_expression(collection, {"$type": test.expression})
    assert_expression_result(result, expected=test.expected, msg=test.msg)
