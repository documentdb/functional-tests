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
from documentdb_tests.framework.test_constants import INT32_MAX

# Property [Numeric Deduplication]: identical numeric values of the same type
# are deduplicated.
SETUNION_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "numeric_dedup_int32",
        expression={"$setUnion": ["$a"]},
        doc={"a": [10, 10, 20]},
        expected=[10, 20],
        msg="$setUnion should deduplicate identical int32 values",
    ),
    ExpressionTestCase(
        "numeric_dedup_int64",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Int64(10), Int64(10), Int64(20)]},
        expected=[Int64(10), Int64(20)],
        msg="$setUnion should deduplicate identical Int64 values",
    ),
    ExpressionTestCase(
        "numeric_dedup_double",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1.5, 1.5, 2.5]},
        expected=[1.5, 2.5],
        msg="$setUnion should deduplicate identical double values",
    ),
    ExpressionTestCase(
        "numeric_dedup_decimal128",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Decimal128("3.14"), Decimal128("3.14"), Decimal128("2.72")]},
        expected=[Decimal128("2.72"), Decimal128("3.14")],
        msg="$setUnion should deduplicate identical Decimal128 values",
    ),
]

# Property [Numeric Type Equivalence for Deduplication]: numerically equal
# values across int32, int64, double, and Decimal128 are treated as duplicates
# and collapse to a single element retaining the first-seen type, while booleans
# and non-numeric types remain distinct.
SETUNION_NUMERIC_TYPE_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "numtype_int32_int64_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1, Int64(1)]},
        expected=[1],
        msg="$setUnion should collapse int32 and int64, retaining first-seen int32",
    ),
    ExpressionTestCase(
        "numtype_int64_int32_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Int64(1), 1]},
        expected=[Int64(1)],
        msg="$setUnion should collapse int64 and int32, retaining first-seen int64",
    ),
    ExpressionTestCase(
        "numtype_int32_double_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1, 1.0]},
        expected=[1],
        msg="$setUnion should collapse int32 and double, retaining first-seen int32",
    ),
    ExpressionTestCase(
        "numtype_double_int32_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1.0, 1]},
        expected=[1.0],
        msg="$setUnion should collapse double and int32, retaining first-seen double",
    ),
    ExpressionTestCase(
        "numtype_int32_decimal_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1, Decimal128("1")]},
        expected=[1],
        msg="$setUnion should collapse int32 and Decimal128, retaining first-seen int32",
    ),
    ExpressionTestCase(
        "numtype_decimal_int32_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Decimal128("1"), 1]},
        expected=[Decimal128("1")],
        msg="$setUnion should collapse Decimal128 and int32, retaining first-seen Decimal128",
    ),
    ExpressionTestCase(
        "numtype_int64_double_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Int64(1), 1.0]},
        expected=[Int64(1)],
        msg="$setUnion should collapse int64 and double, retaining first-seen int64",
    ),
    ExpressionTestCase(
        "numtype_double_int64_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1.0, Int64(1)]},
        expected=[1.0],
        msg="$setUnion should collapse double and int64, retaining first-seen double",
    ),
    ExpressionTestCase(
        "numtype_int64_decimal_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Int64(1), Decimal128("1")]},
        expected=[Int64(1)],
        msg="$setUnion should collapse int64 and Decimal128, retaining first-seen int64",
    ),
    ExpressionTestCase(
        "numtype_decimal_int64_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Decimal128("1"), Int64(1)]},
        expected=[Decimal128("1")],
        msg="$setUnion should collapse Decimal128 and int64, retaining first-seen Decimal128",
    ),
    ExpressionTestCase(
        "numtype_double_decimal_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1.0, Decimal128("1")]},
        expected=[1.0],
        msg="$setUnion should collapse double and Decimal128, retaining first-seen double",
    ),
    ExpressionTestCase(
        "numtype_decimal_double_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Decimal128("1"), 1.0]},
        expected=[Decimal128("1")],
        msg="$setUnion should collapse Decimal128 and double, retaining first-seen Decimal128",
    ),
    ExpressionTestCase(
        "numtype_all_four_collapse",
        expression={"$setUnion": ["$a"]},
        doc={"a": [1, Int64(1), 1.0, Decimal128("1")]},
        expected=[1],
        msg="$setUnion should collapse all four numeric types, retaining first-seen int32",
    ),
    ExpressionTestCase(
        "numtype_cross_array_collapse",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [1, 2], "b": [Int64(1), Int64(3)]},
        expected=[1, 2, Int64(3)],
        msg="$setUnion should collapse equal values across arrays, retaining first-seen types",
    ),
]

# Property [Numeric Boundary Deduplication]: numeric type equivalence holds at
# boundary values like INT32_MAX and the double precision limit.
SETUNION_NUMERIC_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "boundary_int32_max_as_int64",
        expression={"$setUnion": ["$a"]},
        doc={"a": [INT32_MAX, Int64(INT32_MAX)]},
        expected=[INT32_MAX],
        msg="$setUnion should collapse int32 max with equivalent int64",
    ),
    ExpressionTestCase(
        "boundary_large_exact_int64_double",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Int64(2**53), float(2**53)]},
        expected=[Int64(2**53)],
        msg="$setUnion should collapse int64 and exact double at 2^53",
    ),
    ExpressionTestCase(
        "boundary_large_inexact_int64_double",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Int64(2**53 + 1), float(2**53 + 1)]},
        expected=[float(2**53 + 1), Int64(2**53 + 1)],
        msg="$setUnion should treat int64 and inexact double as distinct at 2^53+1",
    ),
]

# Property [Decimal128 Precision Deduplication]: Decimal128 values with
# different trailing zeros but the same numeric value are treated as duplicates,
# retaining the first-seen representation.
SETUNION_DECIMAL128_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dec_prec_short_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Decimal128("3.1"), Decimal128("3.10")]},
        expected=[Decimal128("3.1")],
        msg="$setUnion should retain Decimal128 3.1 when it is seen before 3.10",
    ),
    ExpressionTestCase(
        "dec_prec_long_first",
        expression={"$setUnion": ["$a"]},
        doc={"a": [Decimal128("3.10"), Decimal128("3.1")]},
        expected=[Decimal128("3.10")],
        msg="$setUnion should retain Decimal128 3.10 when it is seen before 3.1",
    ),
    ExpressionTestCase(
        "dec_prec_cross_array",
        expression={"$setUnion": ["$a", "$b"]},
        doc={"a": [Decimal128("5.0")], "b": [Decimal128("5.00")]},
        expected=[Decimal128("5.0")],
        msg="$setUnion should retain first-seen Decimal128 precision across arrays",
    ),
]

SETUNION_NUMERIC_TESTS_ALL = (
    SETUNION_NUMERIC_TESTS
    + SETUNION_NUMERIC_TYPE_EQUIV_TESTS
    + SETUNION_NUMERIC_BOUNDARY_TESTS
    + SETUNION_DECIMAL128_PRECISION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SETUNION_NUMERIC_TESTS_ALL))
def test_setunion_numeric(collection, test_case: ExpressionTestCase):
    """Test $setUnion numeric deduplication cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
        ignore_order=True,
    )
