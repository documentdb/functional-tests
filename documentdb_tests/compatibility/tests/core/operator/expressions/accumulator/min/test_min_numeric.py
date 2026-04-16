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

# Property [Numeric Comparison]: $min compares numeric values across types
# and returns the numerically smaller value.
MIN_NUMERIC_COMPARISON_TESTS: list[ExpressionTestCase] = [
    # Same-type comparisons.
    ExpressionTestCase(
        "numeric_int32_same",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 3, "b": 7},
        expected=3,
        msg="$min should return the smaller int32 value",
    ),
    ExpressionTestCase(
        "numeric_int32_same_negative",
        expression={"$min": ["$a", "$b"]},
        doc={"a": -5, "b": -2},
        expected=-5,
        msg="$min should return the smaller int32 value among negatives",
    ),
    ExpressionTestCase(
        "numeric_int64_same",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Int64(100), "b": Int64(200)},
        expected=Int64(100),
        msg="$min should return the smaller int64 value",
    ),
    ExpressionTestCase(
        "numeric_int64_same_negative",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Int64(-100), "b": Int64(-50)},
        expected=Int64(-100),
        msg="$min should return the smaller int64 value among negatives",
    ),
    ExpressionTestCase(
        "numeric_double_same",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 1.5, "b": 3.5},
        expected=1.5,
        msg="$min should return the smaller double value",
    ),
    ExpressionTestCase(
        "numeric_double_same_negative",
        expression={"$min": ["$a", "$b"]},
        doc={"a": -1.5, "b": -0.5},
        expected=-1.5,
        msg="$min should return the smaller double value among negatives",
    ),
    ExpressionTestCase(
        "numeric_decimal128_same",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("10"), "b": Decimal128("20")},
        expected=Decimal128("10"),
        msg="$min should return the smaller Decimal128 value",
    ),
    ExpressionTestCase(
        "numeric_decimal128_same_negative",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("-10"), "b": Decimal128("-5")},
        expected=Decimal128("-10"),
        msg="$min should return the smaller Decimal128 value among negatives",
    ),
    # Cross-type: int32 vs int64.
    ExpressionTestCase(
        "numeric_int32_vs_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 5, "b": Int64(10)},
        expected=5,
        msg="$min should pick the numerically smaller int32 over int64",
    ),
    ExpressionTestCase(
        "numeric_int64_vs_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Int64(3), "b": 10},
        expected=Int64(3),
        msg="$min should pick the numerically smaller int64 over int32",
    ),
    # Cross-type: int32 vs double.
    ExpressionTestCase(
        "numeric_int32_vs_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 3, "b": 4.5},
        expected=3,
        msg="$min should pick the numerically smaller int32 over double",
    ),
    ExpressionTestCase(
        "numeric_double_vs_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 3.5, "b": 5},
        expected=3.5,
        msg="$min should pick the numerically smaller double over int32",
    ),
    # Cross-type: int32 vs Decimal128.
    ExpressionTestCase(
        "numeric_int32_vs_decimal128",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 5, "b": Decimal128("10")},
        expected=5,
        msg="$min should pick the numerically smaller int32 over Decimal128",
    ),
    ExpressionTestCase(
        "numeric_decimal128_vs_int32",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("3"), "b": 10},
        expected=Decimal128("3"),
        msg="$min should pick the numerically smaller Decimal128 over int32",
    ),
    # Cross-type: int64 vs double.
    ExpressionTestCase(
        "numeric_int64_vs_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Int64(3), "b": 4.5},
        expected=Int64(3),
        msg="$min should pick the numerically smaller int64 over double",
    ),
    ExpressionTestCase(
        "numeric_double_vs_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 3.5, "b": Int64(10)},
        expected=3.5,
        msg="$min should pick the numerically smaller double over int64",
    ),
    # Cross-type: int64 vs Decimal128.
    ExpressionTestCase(
        "numeric_int64_vs_decimal128",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Int64(5), "b": Decimal128("10")},
        expected=Int64(5),
        msg="$min should pick the numerically smaller int64 over Decimal128",
    ),
    ExpressionTestCase(
        "numeric_decimal128_vs_int64",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("3"), "b": Int64(10)},
        expected=Decimal128("3"),
        msg="$min should pick the numerically smaller Decimal128 over int64",
    ),
    # Cross-type: double vs Decimal128.
    ExpressionTestCase(
        "numeric_double_vs_decimal128",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 1.5, "b": DECIMAL128_TWO_AND_HALF},
        expected=1.5,
        msg="$min should pick the numerically smaller double over Decimal128",
    ),
    ExpressionTestCase(
        "numeric_decimal128_vs_double",
        expression={"$min": ["$a", "$b"]},
        doc={"a": DECIMAL128_ONE_AND_HALF, "b": 5.5},
        expected=DECIMAL128_ONE_AND_HALF,
        msg="$min should pick the numerically smaller Decimal128 over double",
    ),
    # IEEE 754 rounding: double 3.14 is slightly larger than Decimal128("3.14")
    # because IEEE 754 rounds 3.14 up. So $min picks the Decimal128.
    ExpressionTestCase(
        "numeric_decimal128_ieee754_wins",
        expression={"$min": ["$a", "$b"]},
        doc={"a": 3.14, "b": Decimal128("3.14")},
        expected=Decimal128("3.14"),
        msg="$min should pick Decimal128 3.14 over double 3.14 due to IEEE 754 rounding",
    ),
    ExpressionTestCase(
        "numeric_double_ieee754_loses",
        expression={"$min": ["$a", "$b"]},
        doc={"a": Decimal128("3.14"), "b": 3.14},
        expected=Decimal128("3.14"),
        msg="$min should pick Decimal128 3.14 over double 3.14 regardless of order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(MIN_NUMERIC_COMPARISON_TESTS))
def test_min_numeric_cases(collection, test_case: ExpressionTestCase):
    """Test $min numeric comparison cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
