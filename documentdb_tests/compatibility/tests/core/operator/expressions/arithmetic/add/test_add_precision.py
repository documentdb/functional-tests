"""Tests for $add decimal128 precision and boundary value handling."""

import pytest
from bson import Decimal128

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
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
)

# Property [Decimal128 Precision]: $add preserves decimal128 precision, including exact
# representation of values that are inexact in double.
ADD_DECIMAL_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal_precision",
        doc={"a": Decimal128("1.5"), "b": Decimal128("2.5")},
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("4.0"),
        msg="$add should preserve decimal128 precision",
    ),
    ExpressionTestCase(
        "decimal_precision_small",
        doc={"a": Decimal128("0.1"), "b": Decimal128("0.2")},
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("0.3"),
        msg="$add should exactly represent 0.1 + 0.2 with decimal128",
    ),
    ExpressionTestCase(
        "decimal_large_precision",
        doc={
            "a": Decimal128("999999999999999999999999999999999"),
            "b": Decimal128("1"),
        },
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("1000000000000000000000000000000000"),
        msg="$add should handle large decimal128 addition with full precision",
    ),
    ExpressionTestCase(
        "decimal_large_negative_precision",
        doc={
            "a": Decimal128("-999999999999999999999999999999999"),
            "b": Decimal128("-1"),
        },
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("-1000000000000000000000000000000000"),
        msg="$add should handle large negative decimal128 addition with full precision",
    ),
]

# Property [Decimal128 Boundaries]: $add at decimal128 boundary values promotes to infinity when
# the result overflows, and returns zero when max and min cancel.
ADD_DECIMAL_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "decimal128_max_plus_zero",
        doc={"a": DECIMAL128_MAX, "b": Decimal128("0")},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_MAX,
        msg="$add should return decimal128 max when adding zero to decimal128 max",
    ),
    ExpressionTestCase(
        "decimal128_max_plus_max",
        doc={"a": DECIMAL128_MAX, "b": DECIMAL128_MAX},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_INFINITY,
        msg="$add should return decimal128 infinity when adding two decimal128 max values",
    ),
    ExpressionTestCase(
        "decimal128_min_plus_min",
        doc={"a": DECIMAL128_MIN, "b": DECIMAL128_MIN},
        expression={"$add": ["$a", "$b"]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$add should return decimal128 negative infinity when adding two decimal128 min values",
    ),
    ExpressionTestCase(
        "decimal128_max_plus_min",
        doc={"a": DECIMAL128_MAX, "b": DECIMAL128_MIN},
        expression={"$add": ["$a", "$b"]},
        expected=Decimal128("0E+6111"),
        msg="$add should return zero when adding decimal128 max and decimal128 min",
    ),
]

ADD_PRECISION_ALL_TESTS = ADD_DECIMAL_PRECISION_TESTS + ADD_DECIMAL_BOUNDARY_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ADD_PRECISION_ALL_TESTS))
def test_add_precision(collection, test_case: ExpressionTestCase):
    """Test $add decimal128 precision and boundary value cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
