"""$dateSubtract rejection cases: invalid operand types/values, timezone, overflow, and shape."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    DATEADD_INVALID_AMOUNT_ERROR,
    DATEADD_INVALID_LARGE_VALUE_ERROR,
    DATEADD_INVALID_STARTDATE_ERROR,
    DATEADD_MISSING_FIELD_ERROR,
    DATEADD_UNKNOWN_FIELD_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DATE_UNIT_ERROR,
    INVALID_TIMEZONE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEAR_MIN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Amount Non-Integral]: a non-integral numeric amount is rejected.
DATESUBTRACT_AMOUNT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "amount_non_integral_double_1_5",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1.5}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a non-integral double amount",
    ),
    ExpressionTestCase(
        "amount_non_integral_double_5_9",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 5.9}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a non-integral double amount close to an integer",
    ),
    ExpressionTestCase(
        "amount_non_integral_double_negative",
        doc={"date": datetime(2000, 1, 10, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": -5.9}},
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a non-integral negative double amount",
    ),
    ExpressionTestCase(
        "amount_non_integral_decimal128",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "day",
                "amount": DECIMAL128_ONE_AND_HALF,
            }
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a non-integral decimal128 amount",
    ),
    ExpressionTestCase(
        "amount_decimal128_non_integral_34th_digit",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "day",
                "amount": Decimal128("3.000000000000000000000000000000001"),
            }
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a decimal128 amount non-integral at the 34th digit",
    ),
    ExpressionTestCase(
        "amount_double_near_min",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "day", "amount": DOUBLE_NEAR_MIN}
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a near-minimum double amount as non-integral",
    ),
    ExpressionTestCase(
        "amount_double_min_subnormal",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "day", "amount": DOUBLE_MIN_SUBNORMAL}
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg="$dateSubtract should reject a minimum subnormal double amount as non-integral",
    ),
]

# Property [StartDate Type]: a non-date, non-Timestamp, non-ObjectId startDate is rejected.
DATESUBTRACT_STARTDATE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"startDate_{tid}",
        doc={"date": val},
        expression={"$dateSubtract": {"startDate": "$date", "unit": "day", "amount": 1}},
        error_code=DATEADD_INVALID_STARTDATE_ERROR,
        msg=f"$dateSubtract should reject a {tid} startDate",
    )
    for tid, val in [
        ("string", "2000-01-01"),
        ("int", 123_456_789),
        ("int64", Int64(123_456_789)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", [2000, 1, 1]),
        ("empty_array", []),
        ("single_date_array", [datetime(2021, 6, 15, tzinfo=timezone.utc)]),
        ("object", {"year": 2000}),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Amount Type]: a non-numeric amount is rejected.
DATESUBTRACT_AMOUNT_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"amount_{tid}",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": val,
            }
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg=f"$dateSubtract should reject a {tid} amount",
    )
    for tid, val in [
        ("string", "5"),
        ("boolean", True),
        ("array", [5]),
        ("object", {"value": 5}),
        ("datetime", datetime(2000, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Amount Non-Finite]: a NaN or infinite numeric amount is rejected.
DATESUBTRACT_AMOUNT_NONFINITE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"amount_{tid}",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": val,
            }
        },
        error_code=DATEADD_INVALID_AMOUNT_ERROR,
        msg=f"$dateSubtract should reject a {tid} amount",
    )
    for tid, val in [
        ("nan", FLOAT_NAN),
        ("decimal128_nan", DECIMAL128_NAN),
        ("infinity", FLOAT_INFINITY),
        ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [Unit Type]: a non-string unit is rejected as an invalid date unit.
DATESUBTRACT_UNIT_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": val,
                "amount": 5,
            }
        },
        error_code=INVALID_DATE_UNIT_ERROR,
        msg=f"$dateSubtract should reject a {tid} unit",
    )
    for tid, val in [
        ("number", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["day"]),
        ("object", {"type": "day"}),
        ("datetime", datetime(2000, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("day")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Unit String]: an unrecognized unit string, including wrong case and plurals, is
# rejected at parse time.
DATESUBTRACT_UNIT_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": val,
                "amount": 5,
            }
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"$dateSubtract should reject the {desc}",
    )
    for tid, val, desc in [
        ("invalid_string", "invalid", "unrecognized unit string"),
        ("empty_string", "", "empty string unit"),
        ("mixed_case_Day", "Day", "mixed-case unit Day"),
        ("mixed_case_Hour", "Hour", "mixed-case unit Hour"),
        ("mixed_case_Month", "Month", "mixed-case unit Month"),
        ("mixed_case_Quarter", "Quarter", "mixed-case unit Quarter"),
        ("mixed_case_Week", "Week", "mixed-case unit Week"),
        ("mixed_case_Second", "Second", "mixed-case unit Second"),
        ("mixed_case_Minute", "Minute", "mixed-case unit Minute"),
        ("mixed_case_Millisecond", "Millisecond", "mixed-case unit Millisecond"),
        ("mixed_case_Year", "Year", "mixed-case unit Year"),
        ("uppercase_DAY", "DAY", "uppercase unit DAY"),
        ("uppercase_MILLISECOND", "MILLISECOND", "uppercase unit MILLISECOND"),
        ("uppercase_YEAR", "YEAR", "uppercase unit YEAR"),
        ("uppercase_HOUR", "HOUR", "uppercase unit HOUR"),
        ("uppercase_MONTH", "MONTH", "uppercase unit MONTH"),
        ("uppercase_QUARTER", "QUARTER", "uppercase unit QUARTER"),
        ("uppercase_WEEK", "WEEK", "uppercase unit WEEK"),
        ("uppercase_SECOND", "SECOND", "uppercase unit SECOND"),
        ("uppercase_MINUTE", "MINUTE", "uppercase unit MINUTE"),
        ("plural_years", "years", "plural unit years"),
        ("plural_days", "days", "plural unit days"),
        ("plural_months", "months", "plural unit months"),
        ("plural_hours", "hours", "plural unit hours"),
        ("plural_minutes", "minutes", "plural unit minutes"),
        ("plural_seconds", "seconds", "plural unit seconds"),
        ("plural_milliseconds", "milliseconds", "plural unit milliseconds"),
        ("plural_weeks", "weeks", "plural unit weeks"),
        ("plural_quarters", "quarters", "plural unit quarters"),
        ("epoch_invalid", "epoch", "invalid unit epoch"),
    ]
]

# Property [Invalid Timezone]: an unrecognized or malformed timezone string is rejected.
DATESUBTRACT_TIMEZONE_INVALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"timezone_{tid}",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 5, "timezone": tz}
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg=f"$dateSubtract should reject {desc}",
    )
    for tid, tz, desc in [
        ("offset_3digit_hours_invalid", "+100:00", "a 3-digit hour offset"),
        ("invalid", "Invalid/Timezone", "an unrecognized Olson timezone"),
        ("empty_string", "", "an empty string timezone"),
        ("olson_wrong_case_lowercase", "america/new_york", "an all-lowercase Olson name"),
        ("olson_wrong_case_uppercase", "AMERICA/NEW_YORK", "an all-uppercase Olson name"),
        ("olson_wrong_case_mixed", "america/New_York", "a mixed-case Olson name"),
    ]
]

# Property [Timezone Type]: a non-string timezone is rejected as an invalid type.
DATESUBTRACT_TIMEZONE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"timezone_{tid}",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 5, "timezone": tz}
        },
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateSubtract should reject a {tid} timezone",
    )
    for tid, tz in [
        ("int", 5),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["UTC"]),
        ("object", {"tz": "UTC"}),
        ("datetime", datetime(2000, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Overflow]: an amount that pushes the result beyond the representable date range
# is rejected.
DATESUBTRACT_OVERFLOW_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "large_positive_month_overflow",
        doc={"date": datetime(2020, 12, 31, 12, 10, 5, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "month", "amount": 30_000_000_000}
        },
        error_code=DATEADD_INVALID_LARGE_VALUE_ERROR,
        msg="$dateSubtract should reject a month amount that underflows the date range",
    ),
]

# Property [Array-Resolving Path]: a startDate field path that resolves to an array is rejected
# by the operator's startDate type contract.
DATESUBTRACT_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2021, 6, 15, tzinfo=timezone.utc)},
                {"b": datetime(2021, 7, 1, tzinfo=timezone.utc)},
            ]
        },
        expression={"$dateSubtract": {"startDate": "$a.b", "unit": "day", "amount": 1}},
        error_code=DATEADD_INVALID_STARTDATE_ERROR,
        msg="$dateSubtract should reject a composite array field path as startDate",
    ),
    ExpressionTestCase(
        "single_element_array_path",
        doc={"a": [{"b": datetime(2021, 6, 15, tzinfo=timezone.utc)}]},
        expression={"$dateSubtract": {"startDate": "$a.b", "unit": "day", "amount": 1}},
        error_code=DATEADD_INVALID_STARTDATE_ERROR,
        msg="$dateSubtract should reject a single-element array field path as startDate",
    ),
]

# Property [Argument Shape]: a missing required field or an unknown field is rejected.
DATESUBTRACT_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_missing_startDate",
        expression={"$dateSubtract": {"unit": "day", "amount": 1}},
        error_code=DATEADD_MISSING_FIELD_ERROR,
        msg="$dateSubtract should error when startDate is missing",
    ),
    ExpressionTestCase(
        "arg_missing_unit",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "amount": 1,
            }
        },
        error_code=DATEADD_MISSING_FIELD_ERROR,
        msg="$dateSubtract should error when unit is missing",
    ),
    ExpressionTestCase(
        "arg_missing_amount",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=DATEADD_MISSING_FIELD_ERROR,
        msg="$dateSubtract should error when amount is missing",
    ),
    ExpressionTestCase(
        "arg_empty_object",
        expression={"$dateSubtract": {}},
        error_code=DATEADD_MISSING_FIELD_ERROR,
        msg="$dateSubtract should error for an empty argument object",
    ),
    ExpressionTestCase(
        "arg_unknown_field",
        expression={
            "$dateSubtract": {
                "startDate": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "amount": 1,
                "foo": 1,
            }
        },
        error_code=DATEADD_UNKNOWN_FIELD_ERROR,
        msg="$dateSubtract should error for an unknown field",
    ),
]

DATESUBTRACT_ERROR_TESTS: list[ExpressionTestCase] = (
    DATESUBTRACT_AMOUNT_ERROR_TESTS
    + DATESUBTRACT_STARTDATE_TYPE_ERROR_TESTS
    + DATESUBTRACT_AMOUNT_TYPE_ERROR_TESTS
    + DATESUBTRACT_AMOUNT_NONFINITE_ERROR_TESTS
    + DATESUBTRACT_UNIT_TYPE_ERROR_TESTS
    + DATESUBTRACT_UNIT_STRING_ERROR_TESTS
    + DATESUBTRACT_TIMEZONE_INVALID_TESTS
    + DATESUBTRACT_TIMEZONE_TYPE_ERROR_TESTS
    + DATESUBTRACT_OVERFLOW_ERROR_TESTS
    + DATESUBTRACT_ARRAY_PATH_TESTS
    + DATESUBTRACT_ARGUMENT_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_ERROR_TESTS))
def test_dateSubtract_errors(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract rejects invalid operands, timezones, overflow, and argument shapes."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
