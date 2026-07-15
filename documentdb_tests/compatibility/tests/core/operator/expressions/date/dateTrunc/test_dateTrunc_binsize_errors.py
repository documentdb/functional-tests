"""$dateTrunc binSize rejection cases: non-numeric, non-integral, non-positive, and overflow."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATETRUNC_BINSIZE_OVERFLOW_HOUR_ERROR,
    DATETRUNC_BINSIZE_OVERFLOW_YEAR_ERROR,
    DATETRUNC_INVALID_BINSIZE_ERROR,
    DATETRUNC_INVALID_BINSIZE_VALUE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [BinSize Type]: a non-numeric binSize is rejected.
DATETRUNC_BINSIZE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"binSize_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": val,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg=f"$dateTrunc should reject a {tid} binSize",
    )
    for tid, val in [
        ("string", "2"),
        ("boolean", True),
        ("array", [1]),
        ("empty_array", []),
        ("object", {"a": 1}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [BinSize Non-Integral]: a fractional or non-finite numeric binSize is rejected.
DATETRUNC_BINSIZE_NONINTEGRAL_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binSize_fractional",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": 0.5,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg="$dateTrunc should reject a fractional binSize",
    ),
    ExpressionTestCase(
        "binSize_nan",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": FLOAT_NAN,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg="$dateTrunc should reject a NaN binSize",
    ),
    ExpressionTestCase(
        "binSize_infinity",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": FLOAT_INFINITY,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg="$dateTrunc should reject an infinite binSize",
    ),
    ExpressionTestCase(
        "binSize_decimal128_fractional",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": DECIMAL128_HALF,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg="$dateTrunc should reject a fractional decimal128 binSize",
    ),
    ExpressionTestCase(
        "binSize_decimal128_nan",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": DECIMAL128_NAN,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg="$dateTrunc should reject a NaN decimal128 binSize",
    ),
    ExpressionTestCase(
        "binSize_decimal128_infinity",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": DECIMAL128_INFINITY,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_ERROR,
        msg="$dateTrunc should reject an infinite decimal128 binSize",
    ),
]

# Property [BinSize Value]: a zero or negative binSize is rejected as an invalid value.
DATETRUNC_BINSIZE_VALUE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binSize_zero",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": 0,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_VALUE_ERROR,
        msg="$dateTrunc should reject a zero binSize",
    ),
    ExpressionTestCase(
        "binSize_negative",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": -1,
            }
        },
        error_code=DATETRUNC_INVALID_BINSIZE_VALUE_ERROR,
        msg="$dateTrunc should reject a negative binSize",
    ),
]

# Property [BinSize Overflow]: a binSize that overflows the date range for its unit is rejected.
DATETRUNC_BINSIZE_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binSize_overflow_year",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "year",
                "binSize": Int64(100_000_000_001),
            }
        },
        error_code=DATETRUNC_BINSIZE_OVERFLOW_YEAR_ERROR,
        msg="$dateTrunc should reject a binSize that overflows the year unit",
    ),
    ExpressionTestCase(
        "binSize_overflow_hour",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "hour",
                "binSize": Int64(2_562_047_788_016_999),
            }
        },
        error_code=DATETRUNC_BINSIZE_OVERFLOW_HOUR_ERROR,
        msg="$dateTrunc should reject a binSize that overflows the hour unit",
    ),
]

DATETRUNC_BINSIZE_ERROR_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_BINSIZE_TYPE_ERROR_TESTS
    + DATETRUNC_BINSIZE_NONINTEGRAL_ERROR_TESTS
    + DATETRUNC_BINSIZE_VALUE_ERROR_TESTS
    + DATETRUNC_BINSIZE_OVERFLOW_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_BINSIZE_ERROR_TESTS))
def test_dateTrunc_binsize_errors(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc rejects invalid binSize types, values, and overflow."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
