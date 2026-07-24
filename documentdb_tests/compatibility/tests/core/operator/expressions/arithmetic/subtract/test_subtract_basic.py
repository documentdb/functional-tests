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
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_TWO_AND_HALF,
    DOUBLE_ZERO,
    INT32_ZERO,
)

# Property [Same-type arithmetic]: $subtract preserves the BSON type when both operands share
# a type.
SAME_TYPE_ARITHMETIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_type_int32",
        doc={"a": 10, "b": 3},
        expression={"$subtract": ["$a", "$b"]},
        expected=7,
        msg="$subtract should return int32 for int32 - int32",
    ),
    ExpressionTestCase(
        "same_type_int64",
        doc={"a": Int64(20), "b": Int64(5)},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(15),
        msg="$subtract should return int64 for int64 - int64",
    ),
    ExpressionTestCase(
        "same_type_double",
        doc={"a": 10.5, "b": DOUBLE_TWO_AND_HALF},
        expression={"$subtract": ["$a", "$b"]},
        expected=8.0,
        msg="$subtract should return double for double - double",
    ),
    ExpressionTestCase(
        "same_type_decimal",
        doc={"a": Decimal128("20.5"), "b": Decimal128("10.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("10.0"),
        msg="$subtract should return Decimal128 for Decimal128 - Decimal128",
    ),
]

# Property [Mixed-type promotion]: $subtract promotes the result to the wider of the two input
# types.
MIXED_TYPE_PROMOTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int32_int64",
        doc={"a": 10, "b": Int64(3)},
        expression={"$subtract": ["$a", "$b"]},
        expected=Int64(7),
        msg="$subtract should promote to int64 for int32 - int64",
    ),
    ExpressionTestCase(
        "int32_double",
        doc={"a": 10, "b": DOUBLE_TWO_AND_HALF},
        expression={"$subtract": ["$a", "$b"]},
        expected=7.5,
        msg="$subtract should promote to double for int32 - double",
    ),
    ExpressionTestCase(
        "int32_decimal",
        doc={"a": 10, "b": DECIMAL128_TWO_AND_HALF},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("7.5"),
        msg="$subtract should promote to Decimal128 for int32 - Decimal128",
    ),
    ExpressionTestCase(
        "int64_double",
        doc={"a": Int64(20), "b": 5.5},
        expression={"$subtract": ["$a", "$b"]},
        expected=14.5,
        msg="$subtract should promote to double for int64 - double",
    ),
    ExpressionTestCase(
        "int64_decimal",
        doc={"a": Int64(20), "b": Decimal128("5.5")},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("14.5"),
        msg="$subtract should promote to Decimal128 for int64 - Decimal128",
    ),
    ExpressionTestCase(
        "double_decimal",
        doc={"a": 10.5, "b": DECIMAL128_TWO_AND_HALF},
        expression={"$subtract": ["$a", "$b"]},
        expected=Decimal128("8.0000000000000"),
        msg="$subtract should promote to Decimal128 for double - Decimal128",
    ),
]

# Property [Sign handling]: $subtract correctly computes the sign of the result.
SIGN_HANDLING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "negative_positive",
        doc={"a": -10, "b": 3},
        expression={"$subtract": ["$a", "$b"]},
        expected=-13,
        msg="$subtract should return negative for negative minuend minus positive subtrahend",
    ),
    ExpressionTestCase(
        "positive_negative",
        doc={"a": 10, "b": -3},
        expression={"$subtract": ["$a", "$b"]},
        expected=13,
        msg="$subtract should return positive for positive minuend minus negative subtrahend",
    ),
    ExpressionTestCase(
        "both_negative",
        doc={"a": -10, "b": -3},
        expression={"$subtract": ["$a", "$b"]},
        expected=-7,
        msg="$subtract should return negative when both operands are negative and |a| > |b|",
    ),
    ExpressionTestCase(
        "result_negative",
        doc={"a": 5, "b": 10},
        expression={"$subtract": ["$a", "$b"]},
        expected=-5,
        msg="$subtract should return negative when the minuend is smaller than the subtrahend",
    ),
    ExpressionTestCase(
        "result_negative_double",
        doc={"a": 5.5, "b": 10},
        expression={"$subtract": ["$a", "$b"]},
        expected=-4.5,
        msg="$subtract should return negative double when minuend is smaller than subtrahend",
    ),
]

# Property [Zero handling]: $subtract handles zero operands correctly.
ZERO_HANDLING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_minuend",
        doc={"a": INT32_ZERO, "b": 5},
        expression={"$subtract": ["$a", "$b"]},
        expected=-5,
        msg="$subtract should return negated subtrahend when the minuend is zero",
    ),
    ExpressionTestCase(
        "zero_subtrahend",
        doc={"a": 5, "b": INT32_ZERO},
        expression={"$subtract": ["$a", "$b"]},
        expected=5,
        msg="$subtract should return the minuend unchanged when the subtrahend is zero",
    ),
    ExpressionTestCase(
        "zeros",
        doc={"a": INT32_ZERO, "b": INT32_ZERO},
        expression={"$subtract": ["$a", "$b"]},
        expected=INT32_ZERO,
        msg="$subtract should return zero for zero - zero",
    ),
    ExpressionTestCase(
        "zero_negative_zero",
        doc={"a": INT32_ZERO, "b": DOUBLE_NEGATIVE_ZERO},
        expression={"$subtract": ["$a", "$b"]},
        expected=DOUBLE_ZERO,
        msg="$subtract of int32 zero minus double negative-zero should return double positive-zero",
    ),
    ExpressionTestCase(
        "negative_zero_zero",
        doc={"a": DOUBLE_NEGATIVE_ZERO, "b": INT32_ZERO},
        expression={"$subtract": ["$a", "$b"]},
        expected=DOUBLE_NEGATIVE_ZERO,
        msg="$subtract of double negative-zero minus int32 zero should return double negative-zero",
    ),
]

SUBTRACT_BASIC_TESTS: list[ExpressionTestCase] = (
    SAME_TYPE_ARITHMETIC_TESTS
    + MIXED_TYPE_PROMOTION_TESTS
    + SIGN_HANDLING_TESTS
    + ZERO_HANDLING_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_BASIC_TESTS))
def test_subtract_basic(collection, test_case: ExpressionTestCase):
    """Test $subtract same-type and mixed-type numeric arithmetic."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
