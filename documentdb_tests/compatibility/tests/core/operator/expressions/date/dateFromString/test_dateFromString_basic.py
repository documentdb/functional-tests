"""Tests for $dateFromString argument handling, null/onNull, onError, formats, and parsing."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DATEFROMSTRING_MISSING_DATESTRING_ERROR,
    DATEFROMSTRING_NON_OBJECT_ERROR,
    DATEFROMSTRING_UNKNOWN_FIELD_ERROR,
    DATETOSTRING_INVALID_FORMAT_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_LEAP_FEB29,
    DATE_YEAR_1900,
    DATE_YEAR_9999,
    MISSING,
)

# Property [Argument Handling]: a date is parsed from a dateString, optionally with format and
# timezone.
DATEFROMSTRING_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dateString_only",
        doc={"dateString": "2017-02-08T12:10:40.787"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 12, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should parse an ISO dateString on its own",
    ),
    ExpressionTestCase(
        "with_format",
        doc={"dateString": "06-15-2018"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%m-%d-%Y"}},
        expected=datetime(2018, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a dateString with a custom format",
    ),
    ExpressionTestCase(
        "with_tz",
        doc={"dateString": "2017-02-08T12:10:40.787"},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2017, 2, 8, 17, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should apply the timezone argument to a naive dateString",
    ),
    ExpressionTestCase(
        "all_fields",
        doc={"dateString": "06-15-2018"},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "format": "%m-%d-%Y",
                "timezone": "UTC",
                "onError": "bad",
                "onNull": "missing",
            }
        },
        expected=datetime(2018, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse when every argument is provided",
    ),
]

# Property [Argument Validation]: a missing dateString, unknown field, or non-object argument is
# rejected.
DATEFROMSTRING_ARG_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_dateString",
        expression={"$dateFromString": {"format": "%Y"}},
        error_code=DATEFROMSTRING_MISSING_DATESTRING_ERROR,
        msg="$dateFromString should reject an argument with no dateString field",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$dateFromString": {}},
        error_code=DATEFROMSTRING_MISSING_DATESTRING_ERROR,
        msg="$dateFromString should reject an empty object argument",
    ),
    ExpressionTestCase(
        "unknown_field",
        expression={"$dateFromString": {"dateString": "2017-02-08", "foo": 1}},
        error_code=DATEFROMSTRING_UNKNOWN_FIELD_ERROR,
        msg="$dateFromString should reject an unknown field",
    ),
    ExpressionTestCase(
        "non_object_str",
        expression={"$dateFromString": "string"},
        error_code=DATEFROMSTRING_NON_OBJECT_ERROR,
        msg="$dateFromString should reject a string argument",
    ),
    ExpressionTestCase(
        "non_object_arr",
        expression={"$dateFromString": [1, 2]},
        error_code=DATEFROMSTRING_NON_OBJECT_ERROR,
        msg="$dateFromString should reject an array argument",
    ),
    ExpressionTestCase(
        "non_object_num",
        expression={"$dateFromString": 123},
        error_code=DATEFROMSTRING_NON_OBJECT_ERROR,
        msg="$dateFromString should reject a numeric argument",
    ),
]

# Property [Null and onNull]: a null or missing dateString yields null unless onNull supplies a
# value.
DATEFROMSTRING_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_no_onNull",
        doc={"dateString": None},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=None,
        msg="$dateFromString should return null for a null dateString with no onNull",
    ),
    ExpressionTestCase(
        "null_onNull_str",
        doc={"dateString": None},
        expression={"$dateFromString": {"dateString": "$dateString", "onNull": "N/A"}},
        expected="N/A",
        msg="$dateFromString should return the onNull value for a null dateString",
    ),
    ExpressionTestCase(
        "null_onNull_date",
        doc={"dateString": None},
        expression={"$dateFromString": {"dateString": "$dateString", "onNull": DATE_EPOCH}},
        expected=DATE_EPOCH,
        msg="$dateFromString should return a date onNull value for a null dateString",
    ),
    ExpressionTestCase(
        "missing_ref",
        expression={"$dateFromString": {"dateString": MISSING}},
        expected=None,
        msg="$dateFromString should return null when the dateString field is missing",
    ),
    ExpressionTestCase(
        "missing_ref_onNull",
        expression={"$dateFromString": {"dateString": MISSING, "onNull": "missing"}},
        expected="missing",
        msg="$dateFromString should return the onNull value when the dateString field is missing",
    ),
]

# Property [onError]: an unparsable dateString yields the onError value, or errors when onError is
# absent.
DATEFROMSTRING_ONERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unparsable_no_onError",
        doc={"dateString": "not-a-date"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should error on an unparsable dateString with no onError",
    ),
    ExpressionTestCase(
        "unparsable_onError_str",
        doc={"dateString": "not-a-date"},
        expression={"$dateFromString": {"dateString": "$dateString", "onError": "bad"}},
        expected="bad",
        msg="$dateFromString should return the onError value for an unparsable dateString",
    ),
    ExpressionTestCase(
        "unparsable_onError_null",
        doc={"dateString": "not-a-date"},
        expression={"$dateFromString": {"dateString": "$dateString", "onError": None}},
        expected=None,
        msg="$dateFromString should return a null onError value for an unparsable dateString",
    ),
    ExpressionTestCase(
        "valid_with_onError",
        doc={"dateString": "2017-02-08"},
        expression={"$dateFromString": {"dateString": "$dateString", "onError": "bad"}},
        expected=datetime(2017, 2, 8, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should ignore onError when the dateString parses",
    ),
    # onNull takes precedence over onError when the dateString is null.
    ExpressionTestCase(
        "null_with_both_onError_onNull",
        doc={"dateString": None},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "onError": "error_val",
                "onNull": "null_val",
            }
        },
        expected="null_val",
        msg="$dateFromString should prefer onNull over onError for a null dateString",
    ),
]

# Property [Custom Format]: an explicit format string controls how the dateString is parsed.
DATEFROMSTRING_FORMAT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "format_dmy",
        doc={"dateString": "15-06-2018"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%d-%m-%Y"}},
        expected=datetime(2018, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a day-month-year format",
    ),
    ExpressionTestCase(
        "format_mdy",
        doc={"dateString": "06-15-2018"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%m-%d-%Y"}},
        expected=datetime(2018, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a month-day-year format",
    ),
    ExpressionTestCase(
        "format_full",
        doc={"dateString": "2018-06-15T10:30:45.123"},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "format": "%Y-%m-%dT%H:%M:%S.%L",
            }
        },
        expected=datetime(2018, 6, 15, 10, 30, 45, 123000, tzinfo=timezone.utc),
        msg="$dateFromString should parse a full datetime format",
    ),
]

# Property [Format Specifiers]: each supported conversion specifier parses its component correctly.
DATEFROMSTRING_FORMAT_SPECIFIER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "format_b_month",
        doc={"dateString": "jan 15 2020"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%b %d %Y"}},
        expected=datetime(2020, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse an abbreviated month name with %b",
    ),
    ExpressionTestCase(
        "format_B_month",
        doc={"dateString": "january 15 2020"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%B %d %Y"}},
        expected=datetime(2020, 1, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a full month name with %B",
    ),
    ExpressionTestCase(
        "format_slash",
        doc={"dateString": "08/02/2017"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%d/%m/%Y"}},
        expected=datetime(2017, 2, 8, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse slash-separated components",
    ),
    ExpressionTestCase(
        "format_no_sep",
        doc={"dateString": "20170208"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%Y%m%d"}},
        expected=datetime(2017, 2, 8, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse components with no separators",
    ),
    ExpressionTestCase(
        "format_G_iso_year",
        doc={"dateString": "2024"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%G"}},
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse an ISO week-numbering year with %G",
    ),
    ExpressionTestCase(
        "format_V_iso_week",
        doc={"dateString": "2024-W24"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%G-W%V"}},
        expected=datetime(2024, 6, 10, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse an ISO week number with %V",
    ),
    ExpressionTestCase(
        "format_u_iso_day_of_week",
        doc={"dateString": "2024-W24-6"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%G-W%V-%u"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse an ISO day of week with %u",
    ),
    ExpressionTestCase(
        "format_z_tz_offset",
        doc={"dateString": "2024-06-15 +0530"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%Y-%m-%d %z"}},
        expected=datetime(2024, 6, 14, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a timezone offset with %z",
    ),
    ExpressionTestCase(
        "format_Z_tz_minutes",
        doc={"dateString": "2024-06-15 +330"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%Y-%m-%d %Z"}},
        expected=datetime(2024, 6, 14, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a timezone offset in minutes with %Z",
    ),
    ExpressionTestCase(
        "format_j_day_of_year",
        doc={"dateString": "2024 167"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%Y %j"}},
        expected=datetime(2024, 6, 16, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a day of year with %j",
    ),
    ExpressionTestCase(
        "format_percent_literal",
        doc={"dateString": "100% 2024-06-15"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "100%% %Y-%m-%d"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should treat %% as a literal percent",
    ),
    ExpressionTestCase(
        "format_H_hour",
        doc={"dateString": "2024-06-15 14"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%Y-%m-%d %H"}},
        expected=datetime(2024, 6, 15, 14, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse an hour with %H",
    ),
    ExpressionTestCase(
        "format_M_minute",
        doc={"dateString": "2024-06-15 14:30"},
        expression={"$dateFromString": {"dateString": "$dateString", "format": "%Y-%m-%d %H:%M"}},
        expected=datetime(2024, 6, 15, 14, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a minute with %M",
    ),
    ExpressionTestCase(
        "format_S_second",
        doc={"dateString": "2024-06-15 14:30:45"},
        expression={
            "$dateFromString": {"dateString": "$dateString", "format": "%Y-%m-%d %H:%M:%S"}
        },
        expected=datetime(2024, 6, 15, 14, 30, 45, tzinfo=timezone.utc),
        msg="$dateFromString should parse a second with %S",
    ),
    ExpressionTestCase(
        "format_L_millisecond",
        doc={"dateString": "2024-06-15 14:30:45.123"},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "format": "%Y-%m-%d %H:%M:%S.%L",
            }
        },
        expected=datetime(2024, 6, 15, 14, 30, 45, 123000, tzinfo=timezone.utc),
        msg="$dateFromString should parse a millisecond with %L",
    ),
]

# Property [Invalid Format]: an unsupported specifier or a format that does not match the dateString
# errors.
DATEFROMSTRING_FORMAT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "format_Q_unsupported",
        doc={"format": "%Q"},
        expression={"$dateFromString": {"dateString": "2017-02-08", "format": "$format"}},
        error_code=DATETOSTRING_INVALID_FORMAT_ERROR,
        msg="$dateFromString should reject the unsupported %Q format specifier",
    ),
    ExpressionTestCase(
        "format_U_unsupported",
        doc={"format": "%Y %U %w"},
        expression={"$dateFromString": {"dateString": "2024 23 6", "format": "$format"}},
        error_code=DATETOSTRING_INVALID_FORMAT_ERROR,
        msg="$dateFromString should reject the unsupported %U format specifier",
    ),
    ExpressionTestCase(
        "format_w_unsupported",
        doc={"format": "%G-W%V-%w"},
        expression={"$dateFromString": {"dateString": "2024-W24-6", "format": "$format"}},
        error_code=DATETOSTRING_INVALID_FORMAT_ERROR,
        msg="$dateFromString should reject the unsupported %w format specifier",
    ),
    ExpressionTestCase(
        "format_mismatch",
        doc={"format": "%m-%d-%Y"},
        expression={"$dateFromString": {"dateString": "2017-02-08", "format": "$format"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should error when the dateString does not match the format",
    ),
]

# Property [Auto-Parsing]: with no format, common date representations are recognized automatically.
DATEFROMSTRING_AUTO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "auto_iso_ms",
        doc={"dateString": "2017-02-08T12:10:40.787"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 12, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should auto-parse an ISO datetime with milliseconds",
    ),
    ExpressionTestCase(
        "auto_iso_z",
        doc={"dateString": "2017-02-08T12:10:40.787Z"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 12, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should auto-parse an ISO datetime with a Z suffix",
    ),
    ExpressionTestCase(
        "auto_date_only",
        doc={"dateString": "2017-02-08"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should auto-parse a date-only string",
    ),
    ExpressionTestCase(
        "auto_natural",
        doc={"dateString": "oct 20 2020"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2020, 10, 20, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should auto-parse a natural-language date",
    ),
]

# Property [Millisecond Precision]: fractional seconds are preserved to millisecond precision.
DATEFROMSTRING_MS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ms_000",
        doc={"dateString": "2017-02-08T12:10:40.000"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 12, 10, 40, 0, tzinfo=timezone.utc),
        msg="$dateFromString should preserve zero milliseconds",
    ),
    ExpressionTestCase(
        "ms_999",
        doc={"dateString": "2017-02-08T12:10:40.999"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 12, 10, 40, 999000, tzinfo=timezone.utc),
        msg="$dateFromString should preserve maximum milliseconds",
    ),
]

# Property [Unparsable dateString]: a syntactically invalid dateString is rejected.
DATEFROMSTRING_UNPARSABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_dateString",
        doc={"dateString": ""},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject an empty dateString",
    ),
    ExpressionTestCase(
        "invalid_month",
        doc={"dateString": "2017-13-01"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject an out-of-range month",
    ),
    ExpressionTestCase(
        "invalid_day",
        doc={"dateString": "2017-02-30"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject an out-of-range day",
    ),
]

# Property [Leap Year]: February 29 is accepted only in leap years.
DATEFROMSTRING_LEAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_year_valid",
        doc={"dateString": "2020-02-29"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2020, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept February 29 in a leap year",
    ),
    ExpressionTestCase(
        "leap_year_2024",
        doc={"dateString": "2024-02-29"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2024, 2, 29, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept February 29 in another leap year",
    ),
    ExpressionTestCase(
        "leap_year_invalid",
        doc={"dateString": "2019-02-29"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject February 29 in a non-leap year",
    ),
    ExpressionTestCase(
        "leap_year_century",
        doc={"dateString": "2000-02-29"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=DATE_LEAP_FEB29,
        msg="$dateFromString should accept February 29 in a leap century year",
    ),
    ExpressionTestCase(
        "non_leap_century",
        doc={"dateString": "1900-02-29"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject February 29 in a non-leap century year",
    ),
]

# Property [Date Range]: dates across the epoch and into the distant past and future are parsed.
DATEFROMSTRING_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"dateString": "1970-01-01"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=DATE_EPOCH,
        msg="$dateFromString should parse the Unix epoch",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"dateString": "1969-12-31"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(1969, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a pre-epoch date",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"dateString": "1900-01-01"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=DATE_YEAR_1900,
        msg="$dateFromString should parse a distant past date",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"dateString": "2100-12-31"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2100, 12, 31, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse a distant future date",
    ),
    ExpressionTestCase(
        "natural_with_tz_offset",
        doc={"dateString": "WED jan 31 12:05:28 +03:30 1996"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(1996, 1, 31, 8, 35, 28, tzinfo=timezone.utc),
        msg="$dateFromString should parse a natural-language date with a timezone offset",
    ),
    ExpressionTestCase(
        "year_9999_max",
        doc={"dateString": "9999-12-31T23:59:59.999Z"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=DATE_YEAR_9999,
        msg="$dateFromString should parse the maximum representable year",
    ),
]

DATEFROMSTRING_BASIC_TESTS: list[ExpressionTestCase] = (
    DATEFROMSTRING_ARG_TESTS
    + DATEFROMSTRING_ARG_ERROR_TESTS
    + DATEFROMSTRING_NULL_TESTS
    + DATEFROMSTRING_ONERROR_TESTS
    + DATEFROMSTRING_FORMAT_TESTS
    + DATEFROMSTRING_FORMAT_SPECIFIER_TESTS
    + DATEFROMSTRING_FORMAT_ERROR_TESTS
    + DATEFROMSTRING_AUTO_TESTS
    + DATEFROMSTRING_MS_TESTS
    + DATEFROMSTRING_UNPARSABLE_TESTS
    + DATEFROMSTRING_LEAP_TESTS
    + DATEFROMSTRING_RANGE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMSTRING_BASIC_TESTS))
def test_dateFromString_basic(collection, test_case: ExpressionTestCase):
    """Test $dateFromString basic operations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
