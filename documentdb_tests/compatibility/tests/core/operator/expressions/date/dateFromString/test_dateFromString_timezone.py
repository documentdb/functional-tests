"""Tests for $dateFromString timezone argument handling, offsets, DST, and Z-suffix conflicts."""

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
    INVALID_TIMEZONE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Named Timezones]: Olson names and abbreviations shift the parsed instant by their
# offset.
DATEFROMSTRING_NAMED_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_ny",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateFromString": {"dateString": "2024-06-15T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2024, 6, 15, 16, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply the America/New_York offset",
    ),
    ExpressionTestCase(
        "tz_gmt",
        doc={"timezone": "GMT"},
        expression={
            "$dateFromString": {"dateString": "2024-06-15T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should treat GMT as a zero offset",
    ),
    ExpressionTestCase(
        "tz_utc",
        doc={"timezone": "UTC"},
        expression={
            "$dateFromString": {"dateString": "2024-06-15T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should treat UTC as a zero offset",
    ),
    ExpressionTestCase(
        "tz_europe_london",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply the Europe/London winter offset",
    ),
    ExpressionTestCase(
        "tz_europe_london_bst",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateFromString": {"dateString": "2020-07-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 7, 1, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply the Europe/London summer BST offset",
    ),
    ExpressionTestCase(
        "tz_asia_tokyo",
        doc={"timezone": "Asia/Tokyo"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 3, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply the Asia/Tokyo offset",
    ),
    ExpressionTestCase(
        "tz_asia_kolkata",
        doc={"timezone": "Asia/Kolkata"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 6, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply the Asia/Kolkata half-hour offset",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"timezone": "Pacific/Apia"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2019, 12, 31, 22, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply the Pacific/Apia offset across a day boundary",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"timezone": "EST"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept the EST three-letter abbreviation",
    ),
]

# Property [DST Transitions]: a named timezone uses its standard or daylight offset by date.
DATEFROMSTRING_DST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_dst_summer",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateFromString": {"dateString": "2020-07-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 7, 1, 16, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should use the EDT offset in summer",
    ),
    ExpressionTestCase(
        "tz_dst_winter",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should use the EST offset in winter",
    ),
]

# Property [Numeric Offsets]: numeric UTC offsets shift the parsed instant, in full and compact
# forms.
DATEFROMSTRING_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_positive",
        doc={"timezone": "+05:30"},
        expression={
            "$dateFromString": {"dateString": "2024-06-15T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2024, 6, 15, 6, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply a positive numeric offset",
    ),
    ExpressionTestCase(
        "tz_offset_negative",
        doc={"timezone": "-05:00"},
        expression={
            "$dateFromString": {"dateString": "2024-06-15T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2024, 6, 15, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply a negative numeric offset",
    ),
    ExpressionTestCase(
        "tz_zero",
        doc={"timezone": "+00:00"},
        expression={
            "$dateFromString": {"dateString": "2024-06-15T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should treat +00:00 as no shift",
    ),
    ExpressionTestCase(
        "tz_no_colon",
        doc={"timezone": "-0530"},
        expression={
            "$dateFromString": {"dateString": "2017-02-08T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2017, 2, 8, 17, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a colon-less numeric offset",
    ),
    ExpressionTestCase(
        "tz_hour_only",
        doc={"timezone": "+03"},
        expression={
            "$dateFromString": {"dateString": "2017-02-08T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2017, 2, 8, 9, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept an hour-only numeric offset",
    ),
    ExpressionTestCase(
        "tz_45min",
        doc={"timezone": "+05:45"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 6, 15, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply a 45-minute offset",
    ),
    ExpressionTestCase(
        "tz_half_hour_west",
        doc={"timezone": "-03:30"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 15, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromString should apply a half-hour west offset",
    ),
]

# Property [Boundary Offsets]: offsets at and beyond the usual bounds are accepted and applied.
DATEFROMSTRING_OFFSET_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_offset_max_east",
        doc={"timezone": "+14:00"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2019, 12, 31, 22, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept the +14:00 maximum east offset",
    ),
    ExpressionTestCase(
        "tz_offset_max_west",
        doc={"timezone": "-11:00"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 23, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept the -11:00 maximum west offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"timezone": "-13:00"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 2, 1, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a -13:00 offset",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"timezone": "+15:00"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2019, 12, 31, 21, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a +15:00 offset",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_positive",
        doc={"timezone": "+05:70"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 5, 50, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a positive offset with over 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_negative",
        doc={"timezone": "-05:70"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 1, 18, 10, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a negative offset with over 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over24_hours_positive",
        doc={"timezone": "+25:00"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2019, 12, 31, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a positive offset over 24 hours",
    ),
    ExpressionTestCase(
        "tz_over24_hours_negative",
        doc={"timezone": "-25:00"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 2, 13, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a negative offset over 24 hours",
    ),
    ExpressionTestCase(
        "tz_max_valid_positive",
        doc={"timezone": "+99:99"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2019, 12, 28, 7, 21, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept the maximum two-digit positive offset",
    ),
    ExpressionTestCase(
        "tz_max_valid_negative",
        doc={"timezone": "-99:99"},
        expression={
            "$dateFromString": {"dateString": "2020-01-01T12:00:00", "timezone": "$timezone"}
        },
        expected=datetime(2020, 1, 5, 16, 39, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept the maximum two-digit negative offset",
    ),
    ExpressionTestCase(
        "tz_3digit_hours_invalid",
        doc={"timezone": "+100:00"},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject a three-digit hour offset",
    ),
]

# Property [Invalid Timezone String]: an unrecognized or wrongly-cased timezone string is rejected.
DATEFROMSTRING_INVALID_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_olson_wrong_case_lowercase",
        doc={"timezone": "america/new_york"},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject an all-lowercase Olson name",
    ),
    ExpressionTestCase(
        "tz_olson_wrong_case_uppercase",
        doc={"timezone": "AMERICA/NEW_YORK"},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject an all-uppercase Olson name",
    ),
    ExpressionTestCase(
        "tz_invalid_str",
        doc={"timezone": "NotATimezone"},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject an unrecognized timezone string",
    ),
    ExpressionTestCase(
        "tz_empty",
        doc={"timezone": ""},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject an empty timezone string",
    ),
    ExpressionTestCase(
        "tz_nonexistent_olson",
        doc={"timezone": "America/Nowhere"},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject a non-existent Olson timezone",
    ),
    ExpressionTestCase(
        "tz_z",
        doc={"timezone": "Z"},
        expression={
            "$dateFromString": {"dateString": "2017-02-08T12:00:00", "timezone": "$timezone"}
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromString should reject Z as a timezone identifier",
    ),
]

# Property [Null Timezone]: a null timezone yields null.
DATEFROMSTRING_NULL_TZ_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_null",
        doc={"timezone": None},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$timezone"}},
        expected=None,
        msg="$dateFromString should return null for a null timezone",
    ),
]

# Property [Z Suffix Conflict]: a Z-suffixed dateString conflicts with an explicit timezone
# argument.
DATEFROMSTRING_Z_CONFLICT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "z_no_tz_field",
        doc={"dateString": "2017-02-08T12:10:40.787Z"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 12, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should parse a Z-suffixed dateString without a timezone argument",
    ),
    ExpressionTestCase(
        "z_with_tz_field",
        doc={"dateString": "2017-02-08T12:10:40.787Z"},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "timezone": "America/New_York",
            }
        },
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject a Z-suffixed dateString with a timezone argument",
    ),
]

# Property [dateString Offset Interaction]: an offset inside the dateString combines with the
# timezone argument.
DATEFROMSTRING_DS_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_ny_adjust",
        doc={"dateString": "2017-02-08T12:10:40.787"},
        expression={
            "$dateFromString": {
                "dateString": "$dateString",
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2017, 2, 8, 17, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should shift a naive dateString by the named timezone",
    ),
    ExpressionTestCase(
        "tz_0530_adjust",
        doc={"dateString": "2017-02-09T03:35:02.055"},
        expression={"$dateFromString": {"dateString": "$dateString", "timezone": "+0530"}},
        expected=datetime(2017, 2, 8, 22, 5, 2, 55000, tzinfo=timezone.utc),
        msg="$dateFromString should shift a naive dateString by a numeric offset",
    ),
    ExpressionTestCase(
        "offset_in_dateString_with_tz",
        doc={"dateString": "2017-02-08T12:10:40.787+05:00"},
        expression={"$dateFromString": {"dateString": "$dateString", "timezone": "UTC"}},
        expected=datetime(2017, 2, 8, 7, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should honor an offset embedded in the dateString",
    ),
    ExpressionTestCase(
        "offset_in_dateString_no_tz",
        doc={"dateString": "2017-02-08T12:10:40+05:00"},
        expression={"$dateFromString": {"dateString": "$dateString"}},
        expected=datetime(2017, 2, 8, 7, 10, 40, tzinfo=timezone.utc),
        msg="$dateFromString should honor an embedded offset with no timezone argument",
    ),
]

DATEFROMSTRING_TIMEZONE_TESTS: list[ExpressionTestCase] = (
    DATEFROMSTRING_NAMED_TZ_TESTS
    + DATEFROMSTRING_DST_TESTS
    + DATEFROMSTRING_OFFSET_TESTS
    + DATEFROMSTRING_OFFSET_BOUNDARY_TESTS
    + DATEFROMSTRING_INVALID_TZ_TESTS
    + DATEFROMSTRING_NULL_TZ_TESTS
    + DATEFROMSTRING_Z_CONFLICT_TESTS
    + DATEFROMSTRING_DS_OFFSET_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMSTRING_TIMEZONE_TESTS))
def test_dateFromString_timezone(collection, test_case: ExpressionTestCase):
    """Test $dateFromString timezone handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
