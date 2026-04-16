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
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Identity]: $sum of a single value returns that value unchanged,
# preserving its original BSON type.
SUM_IDENTITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "identity_int32",
        expression={"$sum": "$a"},
        doc={"a": 42},
        expected=42,
        msg="$sum should return int32 value unchanged",
    ),
    ExpressionTestCase(
        "identity_int64",
        expression={"$sum": "$a"},
        doc={"a": Int64(42)},
        expected=Int64(42),
        msg="$sum should return int64 value unchanged",
    ),
    ExpressionTestCase(
        "identity_double",
        expression={"$sum": "$a"},
        doc={"a": 3.14},
        expected=3.14,
        msg="$sum should return double value unchanged",
    ),
    ExpressionTestCase(
        "identity_decimal128",
        expression={"$sum": "$a"},
        doc={"a": Decimal128("42.5")},
        expected=Decimal128("42.5"),
        msg="$sum should return Decimal128 value unchanged",
    ),
]

# Property [Arithmetic]: $sum produces the correct arithmetic sum of same-type operands.
SUM_ARITHMETIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arith_two_int32",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 7, "b": 3},
        expected=10,
        msg="$sum should return arithmetic sum of two int32 values",
    ),
    ExpressionTestCase(
        "arith_range_int32",
        expression={"$sum": "$a"},
        doc={"a": list(range(1000))},
        expected=499500,
        msg="$sum should return arithmetic sum of a range of int32 values",
    ),
    ExpressionTestCase(
        "arith_two_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Int64(100), "b": Int64(200)},
        expected=Int64(300),
        msg="$sum should return arithmetic sum of two int64 values",
    ),
    ExpressionTestCase(
        "arith_range_int64",
        expression={"$sum": "$a"},
        doc={"a": [Int64(i) for i in range(1000)]},
        expected=Int64(499500),
        msg="$sum should return arithmetic sum of a range of int64 values",
    ),
    ExpressionTestCase(
        "arith_two_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 1.5, "b": 2.5},
        expected=4.0,
        msg="$sum should return arithmetic sum of two double values",
    ),
    ExpressionTestCase(
        "arith_range_double",
        expression={"$sum": "$a"},
        doc={"a": [float(i) for i in range(1000)]},
        expected=499500.0,
        msg="$sum should return arithmetic sum of a range of double values",
    ),
    ExpressionTestCase(
        "arith_two_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_ONE_AND_HALF, "b": DECIMAL128_TWO_AND_HALF},
        expected=Decimal128("4.0"),
        msg="$sum should return arithmetic sum of two Decimal128 values",
    ),
    ExpressionTestCase(
        "arith_range_decimal128",
        expression={"$sum": "$a"},
        doc={"a": [Decimal128(str(i)) for i in range(1000)]},
        expected=Decimal128("499500"),
        msg="$sum should return arithmetic sum of a range of Decimal128 values",
    ),
]

# Property [Additive Inverse]: opposite values of the same type cancel to that type's zero.
SUM_CANCEL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "cancel_int32",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5, "b": -5},
        expected=0,
        msg="$sum should return 0 when int32 values cancel",
    ),
    ExpressionTestCase(
        "cancel_int64",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Int64(100), "b": Int64(-100)},
        expected=INT64_ZERO,
        msg="$sum should return int64 0 when int64 values cancel",
    ),
    ExpressionTestCase(
        "cancel_double",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": 5.0, "b": -5.0},
        expected=DOUBLE_ZERO,
        msg="$sum should return 0.0 when double values cancel",
    ),
    ExpressionTestCase(
        "cancel_decimal128",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": Decimal128("7.5"), "b": Decimal128("-7.5")},
        expected=Decimal128("0.0"),
        msg="$sum should return Decimal128 0.0 when Decimal128 values cancel",
    ),
]

# Property [Negative Zero Normalization]: $sum normalizes -0 to +0 in output.
SUM_NEGATIVE_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "neg_zero_double_sole",
        expression={"$sum": "$a"},
        doc={"a": DOUBLE_NEGATIVE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$sum should normalize double negative zero to positive zero",
    ),
    ExpressionTestCase(
        "neg_zero_decimal128_sole",
        expression={"$sum": "$a"},
        doc={"a": DECIMAL128_NEGATIVE_ZERO},
        expected=DECIMAL128_ZERO,
        msg="$sum should normalize Decimal128 negative zero to positive zero",
    ),
    ExpressionTestCase(
        "neg_zero_double_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_NEGATIVE_ZERO, "b": DOUBLE_NEGATIVE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$sum should normalize -0.0 + -0.0 to positive zero",
    ),
    ExpressionTestCase(
        "neg_zero_double_plus_zero",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DOUBLE_NEGATIVE_ZERO, "b": DOUBLE_ZERO},
        expected=DOUBLE_ZERO,
        msg="$sum should normalize -0.0 + 0.0 to positive zero",
    ),
    ExpressionTestCase(
        "neg_zero_decimal128_pair",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_ZERO, "b": DECIMAL128_NEGATIVE_ZERO},
        expected=DECIMAL128_ZERO,
        msg="$sum should normalize Decimal128 -0 + -0 to positive zero",
    ),
    ExpressionTestCase(
        "neg_zero_decimal128_plus_zero",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": DECIMAL128_NEGATIVE_ZERO, "b": DECIMAL128_ZERO},
        expected=DECIMAL128_ZERO,
        msg="$sum should normalize Decimal128 -0 + 0 to positive zero",
    ),
]

SUM_CORE_TESTS = (
    SUM_IDENTITY_TESTS + SUM_ARITHMETIC_TESTS + SUM_CANCEL_TESTS + SUM_NEGATIVE_ZERO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_CORE_TESTS))
def test_sum_core(collection, test_case: ExpressionTestCase):
    """Test $sum core arithmetic properties."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
