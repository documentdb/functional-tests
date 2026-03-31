from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.test_case import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_NEGATIVE_ZERO, DOUBLE_NEGATIVE_ZERO
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import execute_expression

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Numeric Type Acceptance]: index and count accept int32, Int64, whole-number doubles,
# Decimal128 whole numbers, and negative zero across all numeric type combinations.
SUBSTRCP_NUMERIC_TYPE_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "numtype_double_index",
        string="hello",
        index=2.0,
        count=2,
        expected="ll",
        msg="$substrCP should accept whole-number double index",
    ),
    SubstrCPTest(
        "numtype_decimal128_index",
        string="hello",
        index=Decimal128("2"),
        count=2,
        expected="ll",
        msg="$substrCP should accept Decimal128 index",
    ),
    SubstrCPTest(
        "numtype_decimal128_trailing_zero_index",
        string="hello",
        index=Decimal128("2.0"),
        count=2,
        expected="ll",
        msg="$substrCP should accept Decimal128 with trailing zero as index",
    ),
    SubstrCPTest(
        "numtype_decimal128_scientific_index",
        string="hello",
        index=Decimal128("20E-1"),
        count=2,
        expected="ll",
        msg="$substrCP should accept Decimal128 in scientific notation as index",
    ),
    SubstrCPTest(
        "numtype_neg_zero_double_index",
        string="hello",
        index=DOUBLE_NEGATIVE_ZERO,
        count=2,
        expected="he",
        msg="$substrCP should treat double -0.0 as 0 for index",
    ),
    SubstrCPTest(
        "numtype_neg_zero_decimal128_index",
        string="hello",
        index=DECIMAL128_NEGATIVE_ZERO,
        count=2,
        expected="he",
        msg="$substrCP should treat Decimal128 -0 as 0 for index",
    ),
    SubstrCPTest(
        "numtype_int64_count",
        string="hello",
        index=0,
        count=Int64(2),
        expected="he",
        msg="$substrCP should accept Int64 count",
    ),
    SubstrCPTest(
        "numtype_double_count",
        string="hello",
        index=0,
        count=2.0,
        expected="he",
        msg="$substrCP should accept whole-number double count",
    ),
    SubstrCPTest(
        "numtype_decimal128_count",
        string="hello",
        index=0,
        count=Decimal128("2"),
        expected="he",
        msg="$substrCP should accept Decimal128 count",
    ),
    SubstrCPTest(
        "numtype_decimal128_trailing_zero_count",
        string="hello",
        index=0,
        count=Decimal128("2.0"),
        expected="he",
        msg="$substrCP should accept Decimal128 with trailing zero as count",
    ),
    SubstrCPTest(
        "numtype_decimal128_scientific_count",
        string="hello",
        index=0,
        count=Decimal128("20E-1"),
        expected="he",
        msg="$substrCP should accept Decimal128 in scientific notation as count",
    ),
    SubstrCPTest(
        "numtype_neg_zero_double_count",
        string="hello",
        index=0,
        count=DOUBLE_NEGATIVE_ZERO,
        expected="",
        msg="$substrCP should treat double -0.0 as 0 for count",
    ),
    SubstrCPTest(
        "numtype_neg_zero_decimal128_count",
        string="hello",
        index=0,
        count=DECIMAL128_NEGATIVE_ZERO,
        expected="",
        msg="$substrCP should treat Decimal128 -0 as 0 for count",
    ),
    # Cross-product of numeric types for index and count.
    SubstrCPTest(
        "numtype_int32_int64",
        string="hello",
        index=1,
        count=Int64(2),
        expected="el",
        msg="$substrCP should accept int32 index with Int64 count",
    ),
    SubstrCPTest(
        "numtype_int32_double",
        string="hello",
        index=1,
        count=2.0,
        expected="el",
        msg="$substrCP should accept int32 index with double count",
    ),
    SubstrCPTest(
        "numtype_int32_decimal128",
        string="hello",
        index=1,
        count=Decimal128("2"),
        expected="el",
        msg="$substrCP should accept int32 index with Decimal128 count",
    ),
    SubstrCPTest(
        "numtype_int64_int32",
        string="hello",
        index=Int64(1),
        count=2,
        expected="el",
        msg="$substrCP should accept Int64 index with int32 count",
    ),
    SubstrCPTest(
        "numtype_int64_int64",
        string="hello",
        index=Int64(1),
        count=Int64(2),
        expected="el",
        msg="$substrCP should accept Int64 index with Int64 count",
    ),
    SubstrCPTest(
        "numtype_int64_double",
        string="hello",
        index=Int64(1),
        count=2.0,
        expected="el",
        msg="$substrCP should accept Int64 index with double count",
    ),
    SubstrCPTest(
        "numtype_int64_decimal128",
        string="hello",
        index=Int64(1),
        count=Decimal128("2"),
        expected="el",
        msg="$substrCP should accept Int64 index with Decimal128 count",
    ),
    SubstrCPTest(
        "numtype_double_int32",
        string="hello",
        index=1.0,
        count=2,
        expected="el",
        msg="$substrCP should accept double index with int32 count",
    ),
    SubstrCPTest(
        "numtype_double_int64",
        string="hello",
        index=1.0,
        count=Int64(2),
        expected="el",
        msg="$substrCP should accept double index with Int64 count",
    ),
    SubstrCPTest(
        "numtype_double_double",
        string="hello",
        index=1.0,
        count=2.0,
        expected="el",
        msg="$substrCP should accept double index with double count",
    ),
    SubstrCPTest(
        "numtype_double_decimal128",
        string="hello",
        index=1.0,
        count=Decimal128("2"),
        expected="el",
        msg="$substrCP should accept double index with Decimal128 count",
    ),
    SubstrCPTest(
        "numtype_decimal128_int32",
        string="hello",
        index=Decimal128("1"),
        count=2,
        expected="el",
        msg="$substrCP should accept Decimal128 index with int32 count",
    ),
    SubstrCPTest(
        "numtype_decimal128_int64",
        string="hello",
        index=Decimal128("1"),
        count=Int64(2),
        expected="el",
        msg="$substrCP should accept Decimal128 index with Int64 count",
    ),
    SubstrCPTest(
        "numtype_decimal128_double",
        string="hello",
        index=Decimal128("1"),
        count=2.0,
        expected="el",
        msg="$substrCP should accept Decimal128 index with double count",
    ),
    SubstrCPTest(
        "numtype_decimal128_decimal128",
        string="hello",
        index=Decimal128("1"),
        count=Decimal128("2"),
        expected="el",
        msg="$substrCP should accept Decimal128 for both index and count",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_NUMERIC_TYPE_TESTS))
def test_substrcp_numeric_coercion(collection, test_case: SubstrCPTest):
    """Test $substrCP numeric type acceptance cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
