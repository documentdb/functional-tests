"""$dateAdd basic operations, amount types, and boundaries."""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import DATEADD_INVALID_AMOUNT_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MIN,
    DOUBLE_NEGATIVE_ZERO,
    INT32_MAX,
    INT32_MIN,
)

# Property [Unit Arithmetic]: adding a positive amount advances the start date by that unit.
DATEADD_UNIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": 1}},
        expected=datetime(2001, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 1 year",
    ),
    ExpressionTestCase(
        "month_add",
        doc={"date": datetime(2000, 1, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": 2}},
        expected=datetime(2000, 3, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 2 months",
    ),
    ExpressionTestCase(
        "day_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 10}},
        expected=datetime(2000, 1, 11, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 10 days",
    ),
    ExpressionTestCase(
        "hour_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "hour", "amount": 5}},
        expected=datetime(2000, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 5 hours",
    ),
    ExpressionTestCase(
        "minute_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "minute", "amount": 30}},
        expected=datetime(2000, 1, 1, 12, 30, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 30 minutes",
    ),
    ExpressionTestCase(
        "second_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "second", "amount": 45}},
        expected=datetime(2000, 1, 1, 12, 0, 45, tzinfo=timezone.utc),
        msg="$dateAdd should add 45 seconds",
    ),
    ExpressionTestCase(
        "millisecond_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": 500}},
        expected=datetime(2000, 1, 1, 12, 0, 0, 500000, tzinfo=timezone.utc),
        msg="$dateAdd should add 500 milliseconds",
    ),
    ExpressionTestCase(
        "week_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "week", "amount": 2}},
        expected=datetime(2000, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 2 weeks",
    ),
    ExpressionTestCase(
        "quarter_add",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "quarter", "amount": 1}},
        expected=datetime(2000, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should add 1 quarter",
    ),
]

# Property [Negative Amount]: a negative amount subtracts the given unit.
DATEADD_NEGATIVE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "year_subtract",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "year", "amount": -1}},
        expected=datetime(1999, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should subtract 1 year with a negative amount",
    ),
    ExpressionTestCase(
        "month_subtract",
        doc={"date": datetime(2000, 3, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "month", "amount": -2}},
        expected=datetime(2000, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should subtract 2 months with a negative amount",
    ),
    ExpressionTestCase(
        "day_subtract",
        doc={"date": datetime(2000, 1, 11, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": -10}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should subtract 10 days with a negative amount",
    ),
]

# Property [Zero Amount]: a zero amount for any unit returns the start date unchanged.
DATEADD_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"zero_amount_{unit}",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": unit, "amount": 0}},
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg=f"$dateAdd should return the start date unchanged for a zero {unit} amount",
    )
    for unit in (
        "year",
        "quarter",
        "month",
        "week",
        "day",
        "hour",
        "minute",
        "second",
        "millisecond",
    )
]

# Property [Amount Numeric Types]: integral int64, double, and decimal128 amounts, including
# negative zero, are accepted.
DATEADD_AMOUNT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "amount_int64",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": Int64(5)}},
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept an int64 amount",
    ),
    ExpressionTestCase(
        "amount_double_integral",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 5.0}},
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept an integral double amount",
    ),
    ExpressionTestCase(
        "amount_decimal",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": Decimal128("5")}},
        expected=datetime(2000, 1, 6, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept an integral decimal128 amount",
    ),
    ExpressionTestCase(
        "amount_double_negative_zero",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "day", "amount": DOUBLE_NEGATIVE_ZERO}
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should treat a negative-zero double as a zero amount",
    ),
    ExpressionTestCase(
        "amount_decimal128_negative_zero",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "day", "amount": DECIMAL128_NEGATIVE_ZERO}
        },
        expected=datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should treat a negative-zero decimal128 as a zero amount",
    ),
    ExpressionTestCase(
        "amount_decimal128_max_precision_integral",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {
                "startDate": "$date",
                "unit": "day",
                "amount": Decimal128("3.0000000000000000000000000000000000"),
            }
        },
        expected=datetime(2000, 1, 4, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateAdd should accept a max-precision integral decimal128 amount",
    ),
]

# Property [Amount Boundary]: large valid int32/int64 amounts are accepted.
DATEADD_AMOUNT_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "amount_long_large",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "second", "amount": Int64(2_200_000_000)}
        },
        expected=datetime(2069, 9, 18, 11, 6, 40, tzinfo=timezone.utc),
        msg="$dateAdd should accept a large int64 amount",
    ),
    ExpressionTestCase(
        "amount_int32_max",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": INT32_MAX}},
        expected=datetime(2000, 1, 26, 8, 31, 23, 647000, tzinfo=timezone.utc),
        msg="$dateAdd should accept INT32_MAX milliseconds",
    ),
    ExpressionTestCase(
        "amount_int32_min",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "millisecond", "amount": INT32_MIN}},
        expected=datetime(1999, 12, 7, 15, 28, 36, 352000, tzinfo=timezone.utc),
        msg="$dateAdd should accept INT32_MIN milliseconds",
    ),
]

# Property [Amount Non-Integral]: a non-integral numeric amount is rejected.
DATEADD_AMOUNT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "amount_non_integral_double_1_5",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 1.5}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a non-integral double amount",
    ),
    ExpressionTestCase(
        "amount_non_integral_double_5_9",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": 5.9}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a non-integral double amount close to an integer",
    ),
    ExpressionTestCase(
        "amount_non_integral_double_negative",
        doc={"date": datetime(2000, 1, 10, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": -5.9}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a non-integral negative double amount",
    ),
    ExpressionTestCase(
        "amount_non_integral_decimal128",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "day", "amount": DECIMAL128_ONE_AND_HALF}
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a non-integral decimal128 amount",
    ),
    ExpressionTestCase(
        "amount_decimal128_non_integral_34th_digit",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {
                "startDate": "$date",
                "unit": "day",
                "amount": Decimal128("3.000000000000000000000000000000001"),
            }
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a decimal128 amount that is non-integral at the 34th digit",
    ),
    ExpressionTestCase(
        "amount_double_near_min",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateAdd": {"startDate": "$date", "unit": "day", "amount": DOUBLE_NEAR_MIN}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a near-minimum double amount as non-integral",
    ),
    ExpressionTestCase(
        "amount_double_min_subnormal",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateAdd": {"startDate": "$date", "unit": "day", "amount": DOUBLE_MIN_SUBNORMAL}
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateAdd should reject a minimum subnormal double amount as non-integral",
    ),
]

DATEADD_BASIC_TESTS: list[ExpressionTestCase] = (
    DATEADD_UNIT_TESTS
    + DATEADD_NEGATIVE_TESTS
    + DATEADD_ZERO_TESTS
    + DATEADD_AMOUNT_TYPE_TESTS
    + DATEADD_AMOUNT_BOUNDARY_TESTS
    + DATEADD_AMOUNT_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEADD_BASIC_TESTS))
def test_dateAdd_basic(collection, test_case: ExpressionTestCase):
    """Test $dateAdd basic operations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
