from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
)

# Property [Numeric Comparison]: $max compares numeric values across types
# and returns the numerically larger value.
MAX_NUMERIC_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Same-type comparisons.
    ExpressionTestCase(
        "numeric_int32_same",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 3, "b": 7},
        expected=7,
        msg="$max should return the larger int32 value",
    ),
    ExpressionTestCase(
        "numeric_int32_same_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": -5, "b": -2},
        expected=-2,
        msg="$max should return the larger int32 value among negatives",
    ),
    ExpressionTestCase(
        "numeric_int64_same",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Int64(100), "b": Int64(200)},
        expected=Int64(200),
        msg="$max should return the larger int64 value",
    ),
    ExpressionTestCase(
        "numeric_int64_same_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Int64(-100), "b": Int64(-50)},
        expected=Int64(-50),
        msg="$max should return the larger int64 value among negatives",
    ),
    ExpressionTestCase(
        "numeric_double_same",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 1.5, "b": 3.5},
        expected=3.5,
        msg="$max should return the larger double value",
    ),
    ExpressionTestCase(
        "numeric_double_same_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": -1.5, "b": -0.5},
        expected=-0.5,
        msg="$max should return the larger double value among negatives",
    ),
    ExpressionTestCase(
        "numeric_decimal128_same",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("10"), "b": Decimal128("20")},
        expected=Decimal128("20"),
        msg="$max should return the larger Decimal128 value",
    ),
    ExpressionTestCase(
        "numeric_decimal128_same_negative",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("-10"), "b": Decimal128("-5")},
        expected=Decimal128("-5"),
        msg="$max should return the larger Decimal128 value among negatives",
    ),
    # Cross-type: int32 vs int64.
    ExpressionTestCase(
        "numeric_int32_vs_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 5, "b": Int64(10)},
        expected=Int64(10),
        msg="$max should pick the numerically larger int64 over int32",
    ),
    ExpressionTestCase(
        "numeric_int64_vs_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Int64(3), "b": 10},
        expected=10,
        msg="$max should pick the numerically larger int32 over int64",
    ),
    # Cross-type: int32 vs double.
    ExpressionTestCase(
        "numeric_int32_vs_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 3, "b": 4.5},
        expected=4.5,
        msg="$max should pick the numerically larger double over int32",
    ),
    ExpressionTestCase(
        "numeric_double_vs_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 3.5, "b": 5},
        expected=5,
        msg="$max should pick the numerically larger int32 over double",
    ),
    # Cross-type: int32 vs Decimal128.
    ExpressionTestCase(
        "numeric_int32_vs_decimal128",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 5, "b": Decimal128("10")},
        expected=Decimal128("10"),
        msg="$max should pick the numerically larger Decimal128 over int32",
    ),
    ExpressionTestCase(
        "numeric_decimal128_vs_int32",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("3"), "b": 10},
        expected=10,
        msg="$max should pick the numerically larger int32 over Decimal128",
    ),
    # Cross-type: int64 vs double.
    ExpressionTestCase(
        "numeric_int64_vs_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Int64(3), "b": 4.5},
        expected=4.5,
        msg="$max should pick the numerically larger double over int64",
    ),
    ExpressionTestCase(
        "numeric_double_vs_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 3.5, "b": Int64(10)},
        expected=Int64(10),
        msg="$max should pick the numerically larger int64 over double",
    ),
    # Cross-type: int64 vs Decimal128.
    ExpressionTestCase(
        "numeric_int64_vs_decimal128",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Int64(5), "b": Decimal128("10")},
        expected=Decimal128("10"),
        msg="$max should pick the numerically larger Decimal128 over int64",
    ),
    ExpressionTestCase(
        "numeric_decimal128_vs_int64",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("3"), "b": Int64(10)},
        expected=Int64(10),
        msg="$max should pick the numerically larger int64 over Decimal128",
    ),
    # Cross-type: double vs Decimal128.
    ExpressionTestCase(
        "numeric_double_vs_decimal128",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 1.5, "b": DECIMAL128_TWO_AND_HALF},
        expected=DECIMAL128_TWO_AND_HALF,
        msg="$max should pick the numerically larger Decimal128 over double",
    ),
    ExpressionTestCase(
        "numeric_decimal128_vs_double",
        expression={"$max": ["$a", "$b"]},
        doc={"a": DECIMAL128_ONE_AND_HALF, "b": 5.5},
        expected=5.5,
        msg="$max should pick the numerically larger double over Decimal128",
    ),
    # IEEE 754 rounding: double 3.14 is slightly larger than Decimal128("3.14")
    # because IEEE 754 rounds 3.14 up.
    ExpressionTestCase(
        "numeric_double_ieee754_wins",
        expression={"$max": ["$a", "$b"]},
        doc={"a": 3.14, "b": Decimal128("3.14")},
        expected=3.14,
        msg="$max should pick double 3.14 over Decimal128 3.14 due to IEEE 754 rounding",
    ),
    ExpressionTestCase(
        "numeric_decimal128_ieee754_loses",
        expression={"$max": ["$a", "$b"]},
        doc={"a": Decimal128("3.14"), "b": 3.14},
        expected=3.14,
        msg="$max should pick double 3.14 over Decimal128 3.14 regardless of order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MAX_NUMERIC_COMPARISON_TESTS))
def test_max_numeric_cases(collection, test_case: ExpressionTestCase):
    """Test $max numeric comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
