"""Tests for $floor preserving the input numeric type in its result."""

from __future__ import annotations

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ONE_AND_HALF

# Property [Return Type]: floor preserves the input's numeric type, and a whole-number double
# stays a double rather than being coerced to an integer.
FLOOR_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_int32",
        doc={"value": 5},
        expression={"$type": {"$floor": ["$value"]}},
        expected="int",
        msg="$floor should return an int for an int32 input",
    ),
    ExpressionTestCase(
        "return_type_int64",
        doc={"value": Int64(5)},
        expression={"$type": {"$floor": ["$value"]}},
        expected="long",
        msg="$floor should return a long for an int64 input",
    ),
    ExpressionTestCase(
        "return_type_double_fraction",
        doc={"value": 1.5},
        expression={"$type": {"$floor": ["$value"]}},
        expected="double",
        msg="$floor should return a double for a fractional double input",
    ),
    ExpressionTestCase(
        "return_type_double_whole",
        doc={"value": 3.0},
        expression={"$type": {"$floor": ["$value"]}},
        expected="double",
        msg="$floor should keep a whole-number double as a double, not coerce it to an int",
    ),
    ExpressionTestCase(
        "return_type_decimal",
        doc={"value": DECIMAL128_ONE_AND_HALF},
        expression={"$type": {"$floor": ["$value"]}},
        expected="decimal",
        msg="$floor should return a decimal for a decimal128 input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(FLOOR_RETURN_TYPE_TESTS))
def test_floor_return_type(collection, test):
    """Test $floor preserves the input numeric type."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
