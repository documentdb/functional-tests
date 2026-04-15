from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.accumulator.avg.utils.avg_common import (  # noqa: E501
    AvgTest,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    MISSING,
)

# Property [Return Type]: the result is always double unless at least one
# numeric operand is Decimal128, in which case the result is Decimal128.
AVG_RETURN_TYPE_TESTS: list[AvgTest] = [
    AvgTest(
        "return_type_single_int32",
        args=42,
        expected="double",
        msg="$avg of a single int32 should return double",
    ),
    AvgTest(
        "return_type_single_int64",
        args=Int64(42),
        expected="double",
        msg="$avg of a single int64 should return double",
    ),
    AvgTest(
        "return_type_single_double",
        args=42.0,
        expected="double",
        msg="$avg of a single double should return double",
    ),
    AvgTest(
        "return_type_single_decimal",
        args=Decimal128("42"),
        expected="decimal",
        msg="$avg of a single Decimal128 scalar should return Decimal128",
    ),
    AvgTest(
        "return_type_int32_int32",
        args=[1, 2],
        expected="double",
        msg="$avg of two int32 values should return double",
    ),
    AvgTest(
        "return_type_int64_int64",
        args=[Int64(1), Int64(2)],
        expected="double",
        msg="$avg of two int64 values should return double",
    ),
    AvgTest(
        "return_type_double_double",
        args=[1.0, 2.0],
        expected="double",
        msg="$avg of two double values should return double",
    ),
    AvgTest(
        "return_type_int32_int64",
        args=[1, Int64(2)],
        expected="double",
        msg="$avg of int32 and int64 should return double",
    ),
    AvgTest(
        "return_type_int32_double",
        args=[1, 2.0],
        expected="double",
        msg="$avg of int32 and double should return double",
    ),
    AvgTest(
        "return_type_int64_double",
        args=[Int64(1), 2.0],
        expected="double",
        msg="$avg of int64 and double should return double",
    ),
    AvgTest(
        "return_type_int32_decimal",
        args=[1, Decimal128("2")],
        expected="decimal",
        msg="$avg should return Decimal128 when int32 is mixed with Decimal128",
    ),
    AvgTest(
        "return_type_int64_decimal",
        args=[Int64(1), Decimal128("2")],
        expected="decimal",
        msg="$avg should return Decimal128 when int64 is mixed with Decimal128",
    ),
    AvgTest(
        "return_type_double_decimal",
        args=[1.0, Decimal128("2")],
        expected="decimal",
        msg="$avg should return Decimal128 when double is mixed with Decimal128",
    ),
    AvgTest(
        "return_type_decimal_decimal",
        args=[Decimal128("1"), Decimal128("2")],
        expected="decimal",
        msg="$avg of two Decimal128 values should return Decimal128",
    ),
    AvgTest(
        "return_type_array_traversal_no_decimal",
        args={"$literal": [1, Int64(2), 3.0]},
        expected="double",
        msg="$avg should return double during array traversal without Decimal128",
    ),
    AvgTest(
        "return_type_array_traversal_with_decimal",
        args={"$literal": [1, Decimal128("2")]},
        expected="decimal",
        msg="$avg should return Decimal128 during array traversal with Decimal128",
    ),
    AvgTest(
        "return_type_non_numeric_with_decimal",
        args=["string", Decimal128("5")],
        expected="decimal",
        msg="$avg should return Decimal128 when non-numeric is mixed with Decimal128",
    ),
    AvgTest(
        "return_type_nan",
        args=FLOAT_NAN,
        expected="double",
        msg="$avg of NaN should return double",
    ),
    AvgTest(
        "return_type_float_infinity",
        args=FLOAT_INFINITY,
        expected="double",
        msg="$avg of float Infinity should return double",
    ),
    AvgTest(
        "return_type_decimal128_nan",
        args=DECIMAL128_NAN,
        expected="decimal",
        msg="$avg of Decimal128 NaN should return decimal",
    ),
    AvgTest(
        "return_type_decimal128_infinity",
        args=DECIMAL128_INFINITY,
        expected="decimal",
        msg="$avg of Decimal128 Infinity should return decimal",
    ),
]

# Property [Null Return Type]: when $avg returns null the BSON type is null.
AVG_RETURN_TYPE_NULL_TESTS: list[AvgTest] = [
    AvgTest(
        "return_type_null_scalar",
        args=None,
        expected="null",
        msg="$avg of null should have BSON type null",
    ),
    AvgTest(
        "return_type_empty_list",
        args=[],
        expected="null",
        msg="$avg of empty list should have BSON type null",
    ),
    AvgTest(
        "return_type_missing",
        args=MISSING,
        expected="null",
        msg="$avg of a missing field should have BSON type null",
    ),
    AvgTest(
        "return_type_non_numeric",
        args=["string"],
        expected="null",
        msg="$avg of all non-numeric values should have BSON type null",
    ),
]

AVG_RETURN_TYPE_ALL_TESTS = AVG_RETURN_TYPE_TESTS + AVG_RETURN_TYPE_NULL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_RETURN_TYPE_ALL_TESTS))
def test_avg_return_type(collection, test_case: AvgTest):
    """Test $avg return type."""
    result = execute_expression(collection, {"$type": {"$avg": test_case.args}})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
