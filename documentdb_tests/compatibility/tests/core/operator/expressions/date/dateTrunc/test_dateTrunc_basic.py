"""$dateTrunc argument handling, null/missing, and type/value validation of every parameter."""

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
    DATETRUNC_BINSIZE_OVERFLOW_HOUR_ERROR,
    DATETRUNC_BINSIZE_OVERFLOW_YEAR_ERROR,
    DATETRUNC_INVALID_BINSIZE_ERROR,
    DATETRUNC_INVALID_BINSIZE_VALUE_ERROR,
    DATETRUNC_MISSING_DATE_ERROR,
    DATETRUNC_MISSING_UNIT_ERROR,
    DATETRUNC_NON_OBJECT_ERROR,
    DATETRUNC_UNKNOWN_FIELD_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_DATE_UNIT_ERROR,
    INVALID_DATE_VALUE_ERROR,
    INVALID_STARTOFWEEK_ERROR,
    INVALID_STARTOFWEEK_TYPE_ERROR,
    INVALID_TIMEZONE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    FLOAT_INFINITY,
    FLOAT_NAN,
    MISSING,
)

# Property [Argument Handling]: $dateTrunc accepts the required date and unit plus the optional
# binSize, timezone, and startOfWeek parameters.
DATETRUNC_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_required_only",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour"}},
        expected=datetime(2021, 3, 20, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should truncate with the required fields only",
    ),
    ExpressionTestCase(
        "arg_with_binSize",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": 2}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a binSize",
    ),
    ExpressionTestCase(
        "arg_with_timezone",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "timezone": "UTC"}},
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a timezone",
    ),
    ExpressionTestCase(
        "arg_with_startOfWeek",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "monday"}},
        expected=datetime(2021, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a startOfWeek",
    ),
    ExpressionTestCase(
        "arg_all_fields",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={
            "$dateTrunc": {
                "date": "$date",
                "unit": "week",
                "binSize": 1,
                "timezone": "UTC",
                "startOfWeek": "monday",
            }
        },
        expected=datetime(2021, 3, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept all fields together",
    ),
]

# Property [BinSize Numeric Types]: integral int64, decimal128, and double binSize values are
# accepted.
DATETRUNC_BINSIZE_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "binSize_int64",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": Int64(2)}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an int64 binSize",
    ),
    ExpressionTestCase(
        "binSize_decimal128",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": Decimal128("2")}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a decimal128 binSize",
    ),
    ExpressionTestCase(
        "binSize_double_integral",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "binSize": 2.0}},
        expected=datetime(2021, 3, 20, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an integral double binSize",
    ),
]

# Property [Timezone Extremes]: out-of-range two-digit offsets and additional named zones are
# accepted.
DATETRUNC_TIMEZONE_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_over60_minutes_positive",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+05:70"}},
        expected=datetime(2021, 6, 15, 11, 50, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a +05:70 offset with over-60 minutes",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_negative",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-05:70"}},
        expected=datetime(2021, 6, 15, 11, 10, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a -05:70 offset with over-60 minutes",
    ),
    ExpressionTestCase(
        "tz_over24_hours_positive",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+25:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a +25:00 offset with over-24 hours",
    ),
    ExpressionTestCase(
        "tz_over24_hours_negative",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-25:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a -25:00 offset with over-24 hours",
    ),
    ExpressionTestCase(
        "tz_max_valid_positive",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+99:99"}},
        expected=datetime(2021, 6, 15, 11, 21, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the maximum two-digit +99:99 offset",
    ),
    ExpressionTestCase(
        "tz_max_valid_negative",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-99:99"}},
        expected=datetime(2021, 6, 15, 11, 39, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the maximum two-digit -99:99 offset",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "Pacific/Apia"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the Pacific/Apia named zone",
    ),
    ExpressionTestCase(
        "tz_offset_45min",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+05:45"}},
        expected=datetime(2021, 6, 15, 11, 15, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a +05:45 offset with 45 minutes",
    ),
    ExpressionTestCase(
        "tz_offset_half_hour_west",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-02:30"}},
        expected=datetime(2021, 6, 15, 11, 30, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a -02:30 half-hour offset",
    ),
    ExpressionTestCase(
        "tz_offset_max_east",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "+14:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the +14:00 maximum east offset",
    ),
    ExpressionTestCase(
        "tz_offset_max_west",
        doc={"date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "hour", "timezone": "-11:00"}},
        expected=datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept the -11:00 maximum west offset",
    ),
]

# Property [StartOfWeek Case]: startOfWeek accepts full day names and three-letter abbreviations
# in any case.
DATETRUNC_STARTOFWEEK_ACCEPT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_mixed_case_Monday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "Monday"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a mixed-case Monday",
    ),
    ExpressionTestCase(
        "sow_uppercase_MONDAY",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "MONDAY"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase MONDAY",
    ),
    ExpressionTestCase(
        "sow_abbrev_MON",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "MON"}},
        expected=datetime(2021, 6, 14, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase abbreviation MON",
    ),
    ExpressionTestCase(
        "sow_mixed_case_Friday",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "Friday"}},
        expected=datetime(2021, 6, 11, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept a mixed-case Friday",
    ),
    ExpressionTestCase(
        "sow_uppercase_FRIDAY",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "FRIDAY"}},
        expected=datetime(2021, 6, 11, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase FRIDAY",
    ),
    ExpressionTestCase(
        "sow_abbrev_FRI",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "FRI"}},
        expected=datetime(2021, 6, 11, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase abbreviation FRI",
    ),
    ExpressionTestCase(
        "sow_uppercase_SUNDAY",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "SUNDAY"}},
        expected=datetime(2021, 6, 13, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase SUNDAY",
    ),
    ExpressionTestCase(
        "sow_abbrev_SUN",
        doc={"date": datetime(2021, 6, 16, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "week", "startOfWeek": "SUN"}},
        expected=datetime(2021, 6, 13, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should accept an uppercase abbreviation SUN",
    ),
]

# Property [StartOfWeek Relevance]: for a non-week unit a null startOfWeek is ignored when the date
# is a constant literal, but short-circuits the result to null when the date is a field reference.
DATETRUNC_STARTOFWEEK_RELEVANCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_relevance_literal_day",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "day",
                "startOfWeek": None,
            }
        },
        expected=datetime(2021, 3, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateTrunc should ignore a null startOfWeek for a non-week unit when the date is a "
        "constant",
    ),
    ExpressionTestCase(
        "sow_relevance_field_ref_day",
        doc={"date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc)},
        expression={"$dateTrunc": {"date": "$date", "unit": "day", "startOfWeek": None}},
        expected=None,
        msg="$dateTrunc should return null for a null startOfWeek on a non-week unit when the date "
        "is a field reference",
    ),
]

# Property [Null Handling]: a null date, unit, binSize, timezone, or week startOfWeek returns null.
DATETRUNC_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_date",
        doc={"date": None},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        expected=None,
        msg="$dateTrunc should return null for a null date",
    ),
    ExpressionTestCase(
        "null_unit",
        expression={
            "$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc), "unit": None}
        },
        expected=None,
        msg="$dateTrunc should return null for a null unit",
    ),
    ExpressionTestCase(
        "null_binSize",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "binSize": None,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a null binSize",
    ),
    ExpressionTestCase(
        "null_timezone",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": None,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a null timezone",
    ),
    ExpressionTestCase(
        "null_startOfWeek_week",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": None,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a null startOfWeek with the week unit",
    ),
]

# Property [Missing Field Reference]: a missing field reference for date or any optional parameter
# returns null.
DATETRUNC_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_date_ref",
        expression={"$dateTrunc": {"date": MISSING, "unit": "day"}},
        expected=None,
        msg="$dateTrunc should return null for a missing date field reference",
    ),
    ExpressionTestCase(
        "missing_binSize_ref",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "hour",
                "binSize": MISSING,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a missing binSize field reference",
    ),
    ExpressionTestCase(
        "missing_timezone_ref",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": MISSING,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a missing timezone field reference",
    ),
    ExpressionTestCase(
        "missing_startOfWeek_ref",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, 11, 30, 5, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": MISSING,
            }
        },
        expected=None,
        msg="$dateTrunc should return null for a missing startOfWeek field reference",
    ),
]

DATETRUNC_SUCCESS_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_ARG_TESTS
    + DATETRUNC_BINSIZE_ACCEPT_TESTS
    + DATETRUNC_TIMEZONE_ACCEPT_TESTS
    + DATETRUNC_STARTOFWEEK_ACCEPT_TESTS
    + DATETRUNC_STARTOFWEEK_RELEVANCE_TESTS
    + DATETRUNC_NULL_TESTS
    + DATETRUNC_MISSING_TESTS
)

# Property [Argument Shape]: a missing required field, an empty object, an unknown field, or a
# non-object argument is rejected.
DATETRUNC_ARG_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_missing_date",
        expression={"$dateTrunc": {"unit": "day"}},
        error_code=DATETRUNC_MISSING_DATE_ERROR,
        msg="$dateTrunc should error when date is missing",
    ),
    ExpressionTestCase(
        "arg_missing_unit",
        expression={"$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc)}},
        error_code=DATETRUNC_MISSING_UNIT_ERROR,
        msg="$dateTrunc should error when unit is missing",
    ),
    ExpressionTestCase(
        "arg_empty_object",
        expression={"$dateTrunc": {}},
        error_code=DATETRUNC_MISSING_DATE_ERROR,
        msg="$dateTrunc should error for an empty argument object",
    ),
    ExpressionTestCase(
        "arg_unknown_field",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
                "foo": 1,
            }
        },
        error_code=DATETRUNC_UNKNOWN_FIELD_ERROR,
        msg="$dateTrunc should error for an unknown field",
    ),
    ExpressionTestCase(
        "arg_non_object_string",
        expression={"$dateTrunc": "string"},
        error_code=DATETRUNC_NON_OBJECT_ERROR,
        msg="$dateTrunc should reject a string argument",
    ),
    ExpressionTestCase(
        "arg_non_object_array",
        expression={"$dateTrunc": [1, 2]},
        error_code=DATETRUNC_NON_OBJECT_ERROR,
        msg="$dateTrunc should reject an array argument",
    ),
    ExpressionTestCase(
        "arg_non_object_number",
        expression={"$dateTrunc": 123},
        error_code=DATETRUNC_NON_OBJECT_ERROR,
        msg="$dateTrunc should reject a numeric argument",
    ),
]

# Property [Date Type]: a non-date, non-ObjectId, non-Timestamp date value is rejected.
DATETRUNC_DATE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"date_{tid}",
            doc={"date": val},
            expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
            error_code=INVALID_DATE_VALUE_ERROR,
            msg=f"$dateTrunc should reject a {tid} date",
        )
        for tid, val in [
            ("string", "2021"),
            ("int", 123),
            ("int64", Int64(123)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("boolean", True),
            ("array", [1, 2]),
            ("empty_array", []),
            ("object", {"a": 1}),
            ("binary", Binary(b"\x01\x02\x03")),
            ("regex", Regex(".*")),
            ("javascript", Code("function() {}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    ExpressionTestCase(
        "date_boolean_false",
        doc={"date": False},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a false boolean date",
    ),
    ExpressionTestCase(
        "date_single_date_array",
        doc={"date": [datetime(2021, 6, 15, tzinfo=timezone.utc)]},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a single-element array containing a date",
    ),
    ExpressionTestCase(
        "date_decimal128_infinity",
        doc={"date": DECIMAL128_INFINITY},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a Decimal128 Infinity date",
    ),
    ExpressionTestCase(
        "date_decimal128_neg_infinity",
        doc={"date": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$dateTrunc": {"date": "$date", "unit": "day"}},
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateTrunc should reject a Decimal128 -Infinity date",
    ),
]

# Property [Unit Type]: a non-string unit is rejected as an invalid date unit.
DATETRUNC_UNIT_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={"$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc), "unit": val}},
        error_code=INVALID_DATE_UNIT_ERROR,
        msg=f"$dateTrunc should reject a {tid} unit",
    )
    for tid, val in [
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["day"]),
        ("empty_array", []),
        ("object", {"t": "day"}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
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
DATETRUNC_UNIT_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"unit_{tid}",
        expression={"$dateTrunc": {"date": datetime(2021, 1, 1, tzinfo=timezone.utc), "unit": val}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"$dateTrunc should reject the {desc}",
    )
    for tid, val, desc in [
        ("invalid_string", "invalid", "unrecognized unit string"),
        ("empty_string", "", "empty string unit"),
        ("mixed_case_Year", "Year", "mixed-case unit Year"),
        ("mixed_case_Day", "Day", "mixed-case unit Day"),
        ("mixed_case_Hour", "Hour", "mixed-case unit Hour"),
        ("mixed_case_Month", "Month", "mixed-case unit Month"),
        ("mixed_case_Quarter", "Quarter", "mixed-case unit Quarter"),
        ("mixed_case_Week", "Week", "mixed-case unit Week"),
        ("mixed_case_Second", "Second", "mixed-case unit Second"),
        ("mixed_case_Minute", "Minute", "mixed-case unit Minute"),
        ("mixed_case_Millisecond", "Millisecond", "mixed-case unit Millisecond"),
        ("uppercase_YEAR", "YEAR", "uppercase unit YEAR"),
        ("uppercase_DAY", "DAY", "uppercase unit DAY"),
        ("uppercase_HOUR", "HOUR", "uppercase unit HOUR"),
        ("uppercase_MONTH", "MONTH", "uppercase unit MONTH"),
        ("uppercase_MILLISECOND", "MILLISECOND", "uppercase unit MILLISECOND"),
        ("uppercase_QUARTER", "QUARTER", "uppercase unit QUARTER"),
        ("uppercase_WEEK", "WEEK", "uppercase unit WEEK"),
        ("uppercase_SECOND", "SECOND", "uppercase unit SECOND"),
        ("uppercase_MINUTE", "MINUTE", "uppercase unit MINUTE"),
        ("plural_years", "years", "plural unit years"),
        ("plural_months", "months", "plural unit months"),
        ("plural_days", "days", "plural unit days"),
        ("plural_hours", "hours", "plural unit hours"),
        ("plural_minutes", "minutes", "plural unit minutes"),
        ("plural_seconds", "seconds", "plural unit seconds"),
        ("plural_milliseconds", "milliseconds", "plural unit milliseconds"),
        ("plural_weeks", "weeks", "plural unit weeks"),
        ("plural_quarters", "quarters", "plural unit quarters"),
    ]
]

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

# Property [Timezone Type]: a non-string timezone is rejected.
DATETRUNC_TIMEZONE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 6, 15, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": val,
            }
        },
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateTrunc should reject a {tid} timezone",
    )
    for tid, val in [
        ("int", 5),
        ("int64", Int64(5)),
        ("double", 5.0),
        ("decimal128", Decimal128("5")),
        ("boolean", True),
        ("array", ["UTC"]),
        ("empty_array", []),
        ("object", {"tz": "UTC"}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("UTC")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Timezone String]: an unrecognized timezone string, including wrong-case Olson names and
# out-of-range offsets, is rejected.
DATETRUNC_TIMEZONE_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 6, 15, tzinfo=timezone.utc),
                "unit": "day",
                "timezone": val,
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg=f"$dateTrunc should reject the {desc}",
    )
    for tid, val, desc in [
        ("invalid_string", "NotATimezone", "unrecognized timezone string"),
        ("empty_string", "", "empty timezone string"),
        ("olson_lowercase", "america/new_york", "all-lowercase Olson name"),
        ("olson_uppercase", "AMERICA/NEW_YORK", "all-uppercase Olson name"),
        ("offset_3digit_hours", "+100:00", "three-digit hour offset"),
    ]
]

# Property [StartOfWeek Type]: a non-string startOfWeek is rejected.
DATETRUNC_STARTOFWEEK_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"sow_{tid}",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": val,
            }
        },
        error_code=INVALID_STARTOFWEEK_TYPE_ERROR,
        msg=f"$dateTrunc should reject a {tid} startOfWeek",
    )
    for tid, val in [
        ("int", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("boolean", True),
        ("array", ["monday"]),
        ("empty_array", []),
        ("object", {"day": "monday"}),
        ("datetime", datetime(2021, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("600000000000000000000000")),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex("monday")),
        ("javascript", Code("function() {}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [StartOfWeek String]: an unrecognized startOfWeek string is rejected.
DATETRUNC_STARTOFWEEK_STRING_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sow_invalid_string",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "notaday",
            }
        },
        error_code=INVALID_STARTOFWEEK_ERROR,
        msg="$dateTrunc should reject an unrecognized startOfWeek string",
    ),
    ExpressionTestCase(
        "sow_empty_string",
        expression={
            "$dateTrunc": {
                "date": datetime(2021, 3, 20, tzinfo=timezone.utc),
                "unit": "week",
                "startOfWeek": "",
            }
        },
        error_code=INVALID_STARTOFWEEK_ERROR,
        msg="$dateTrunc should reject an empty startOfWeek string",
    ),
]

DATETRUNC_ERROR_TESTS: list[ExpressionTestCase] = (
    DATETRUNC_ARG_ERROR_TESTS
    + DATETRUNC_DATE_TYPE_ERROR_TESTS
    + DATETRUNC_UNIT_TYPE_ERROR_TESTS
    + DATETRUNC_UNIT_STRING_ERROR_TESTS
    + DATETRUNC_BINSIZE_TYPE_ERROR_TESTS
    + DATETRUNC_BINSIZE_NONINTEGRAL_ERROR_TESTS
    + DATETRUNC_BINSIZE_VALUE_ERROR_TESTS
    + DATETRUNC_BINSIZE_OVERFLOW_TESTS
    + DATETRUNC_TIMEZONE_TYPE_ERROR_TESTS
    + DATETRUNC_TIMEZONE_STRING_ERROR_TESTS
    + DATETRUNC_STARTOFWEEK_TYPE_ERROR_TESTS
    + DATETRUNC_STARTOFWEEK_STRING_ERROR_TESTS
)

DATETRUNC_BASIC_TESTS: list[ExpressionTestCase] = DATETRUNC_SUCCESS_TESTS + DATETRUNC_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(DATETRUNC_BASIC_TESTS))
def test_dateTrunc_basic(collection, test_case: ExpressionTestCase):
    """Test $dateTrunc argument handling and validation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
