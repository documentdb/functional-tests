from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64, Timestamp
from bson.code import Code

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    execute_expression,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN_POSITIVE,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

from .utils.substrCP_common import SubstrCPTest, _expr

# Property [Type Coercion]: non-string types for param 1 coerce to their string representation.
SUBSTRCP_TYPE_COERCION_TESTS: list[SubstrCPTest] = [
    SubstrCPTest(
        "coerce_int32",
        string=42,
        index=0,
        count=2,
        expected="42",
        msg="$substrCP should coerce int32 to its digit-string representation",
    ),
    SubstrCPTest(
        "coerce_int64",
        string=Int64(42),
        index=0,
        count=2,
        expected="42",
        msg="$substrCP should coerce Int64 to its digit-string representation",
    ),
    SubstrCPTest(
        "coerce_double_whole",
        string=3.0,
        index=0,
        count=1,
        expected="3",
        msg="$substrCP should coerce whole-number double without decimal point",
    ),
    SubstrCPTest(
        "coerce_double_fractional",
        string=3.14,
        index=0,
        count=4,
        expected="3.14",
        msg="$substrCP should coerce fractional double to string",
    ),
    # 1.23456789 has 9 significant digits but coerces to 6: "1.23457".
    SubstrCPTest(
        "coerce_double_fractional_6sig",
        string=1.23456789,
        index=0,
        count=7,
        expected="1.23457",
        msg="$substrCP should coerce fractional double to at most 6 significant digits",
    ),
    SubstrCPTest(
        "coerce_double_fixed_boundary",
        string=999_999.0,
        index=0,
        count=6,
        expected="999999",
        msg="$substrCP should coerce 999999.0 using fixed notation",
    ),
    SubstrCPTest(
        "coerce_double_scientific_boundary",
        string=1_000_000.0,
        index=0,
        count=5,
        expected="1e+06",
        msg="$substrCP should coerce 1000000.0 using scientific notation",
    ),
    SubstrCPTest(
        "coerce_double_small_fixed",
        string=1e-4,
        index=0,
        count=6,
        expected="0.0001",
        msg="$substrCP should coerce 1e-4 using fixed notation",
    ),
    SubstrCPTest(
        "coerce_double_small_scientific",
        string=1e-5,
        index=0,
        count=5,
        expected="1e-05",
        msg="$substrCP should coerce 1e-5 using scientific notation",
    ),
    SubstrCPTest(
        "coerce_double_nan",
        string=FLOAT_NAN,
        index=0,
        count=3,
        expected="nan",
        msg="$substrCP should coerce double NaN to 'nan'",
    ),
    SubstrCPTest(
        "coerce_double_inf",
        string=FLOAT_INFINITY,
        index=0,
        count=3,
        expected="inf",
        msg="$substrCP should coerce double inf to 'inf'",
    ),
    SubstrCPTest(
        "coerce_double_neg_inf",
        string=FLOAT_NEGATIVE_INFINITY,
        index=0,
        count=4,
        expected="-inf",
        msg="$substrCP should coerce double -inf to '-inf'",
    ),
    SubstrCPTest(
        "coerce_double_neg_zero",
        string=DOUBLE_NEGATIVE_ZERO,
        index=0,
        count=2,
        expected="-0",
        msg="$substrCP should coerce double -0.0 to '-0'",
    ),
    SubstrCPTest(
        "coerce_decimal128",
        string=Decimal128("123.0"),
        index=0,
        count=5,
        expected="123.0",
        msg="$substrCP should coerce Decimal128 preserving trailing zeros",
    ),
    SubstrCPTest(
        "coerce_decimal128_nan",
        string=Decimal128("NaN"),
        index=0,
        count=3,
        expected="NaN",
        msg="$substrCP should coerce Decimal128 NaN to 'NaN'",
    ),
    SubstrCPTest(
        "coerce_decimal128_infinity",
        string=DECIMAL128_INFINITY,
        index=0,
        count=8,
        expected="Infinity",
        msg="$substrCP should coerce Decimal128 Infinity to 'Infinity'",
    ),
    SubstrCPTest(
        "coerce_decimal128_large_exponent",
        string=DECIMAL128_LARGE_EXPONENT,
        index=0,
        count=41,
        expected="1.000000000000000000000000000000000E+6144",
        msg="$substrCP should coerce Decimal128 with large exponent to expanded form",
    ),
    SubstrCPTest(
        "coerce_decimal128_min_positive",
        string=DECIMAL128_MIN_POSITIVE,
        index=0,
        count=7,
        expected="1E-6176",
        msg="$substrCP should coerce Decimal128 minimum positive value",
    ),
    SubstrCPTest(
        "coerce_decimal128_max_negative",
        string=DECIMAL128_MAX_NEGATIVE,
        index=0,
        count=8,
        expected="-1E-6176",
        msg="$substrCP should coerce Decimal128 maximum negative value",
    ),
    SubstrCPTest(
        "coerce_datetime",
        string=datetime(2024, 1, 15, 12, 30, 45, 123_000, tzinfo=timezone.utc),
        index=0,
        count=24,
        expected="2024-01-15T12:30:45.123Z",
        msg="$substrCP should coerce datetime to ISO 8601 format",
    ),
    SubstrCPTest(
        "coerce_timestamp",
        string=Timestamp(1, 1),
        index=0,
        count=17,
        expected="Jan  1 00:00:01:1",
        msg="$substrCP should coerce Timestamp to its string format",
    ),
    SubstrCPTest(
        "coerce_code",
        string=Code("function() {}"),
        index=0,
        count=14,
        expected="function() {}",
        msg="$substrCP should coerce Code to its code string",
    ),
    # Timestamp(0,0) as a literal coerces to its string form. As a stored field, the server
    # replaces it with the current time, so this only tests the literal case.
    SubstrCPTest(
        "coerce_timestamp_zero",
        string=Timestamp(0, 0),
        index=0,
        count=17,
        expected="Jan  1 00:00:00:0",
        msg="$substrCP should coerce Timestamp(0,0) literal to its string format",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBSTRCP_TYPE_COERCION_TESTS))
def test_substrcp_string_coercion(collection, test_case: SubstrCPTest):
    """Test $substrCP string coercion cases."""
    result = execute_expression(collection, _expr(test_case))
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
