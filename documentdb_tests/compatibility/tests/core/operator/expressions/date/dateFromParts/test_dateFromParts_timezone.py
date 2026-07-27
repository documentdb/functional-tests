"""Tests for $dateFromParts timezone parsing, offsets, DST, and type validation."""

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
    INVALID_TIMEZONE_ERROR,
    INVALID_TIMEZONE_TYPE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Valid Timezone]: a UTC-equivalent timezone leaves the constructed date unchanged.
DATEFROMPARTS_TZ_VALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_gmt",
        doc={"timezone": "GMT"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept the GMT timezone",
    ),
    ExpressionTestCase(
        "tz_utc",
        doc={"timezone": "UTC"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept the UTC timezone",
    ),
    ExpressionTestCase(
        "tz_zero_offset",
        doc={"timezone": "+00:00"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        expected=datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a zero UTC offset",
    ),
]

# Property [Offset Application]: a timezone shifts the constructed local time back to UTC.
DATEFROMPARTS_TZ_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_ny",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateFromParts": {
                "year": 2016,
                "month": 12,
                "day": 31,
                "hour": 23,
                "minute": 46,
                "second": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2017, 1, 1, 4, 46, 12, tzinfo=timezone.utc),
        msg="$dateFromParts should shift an Olson timezone local time to UTC",
    ),
    ExpressionTestCase(
        "tz_no_colon",
        doc={"timezone": "-0500"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a compact offset without a colon",
    ),
    ExpressionTestCase(
        "tz_hour_only",
        doc={"timezone": "+03"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 9, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an hour-only offset",
    ),
    ExpressionTestCase(
        "tz_half_hour",
        doc={"timezone": "+05:30"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 0,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply a half-hour offset",
    ),
    ExpressionTestCase(
        "tz_45min",
        doc={"timezone": "+05:45"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 0,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 18, 15, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply a 45-minute offset",
    ),
    ExpressionTestCase(
        "tz_asia_kolkata",
        doc={"timezone": "Asia/Kolkata"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 0,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply a half-hour Olson timezone",
    ),
    ExpressionTestCase(
        "tz_asia_tokyo",
        doc={"timezone": "Asia/Tokyo"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 0,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the Asia/Tokyo timezone",
    ),
    ExpressionTestCase(
        "tz_pacific_apia",
        doc={"timezone": "Pacific/Apia"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 22, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the Pacific/Apia timezone",
    ),
    ExpressionTestCase(
        "tz_offset_max_east",
        doc={"timezone": "+14:00"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 0,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the maximum eastern offset",
    ),
    ExpressionTestCase(
        "tz_offset_max_west",
        doc={"timezone": "-11:00"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 0,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply a large western offset",
    ),
    ExpressionTestCase(
        "tz_offset_half_hour_west",
        doc={"timezone": "-02:30"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 14, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply a half-hour western offset",
    ),
    ExpressionTestCase(
        "tz_offset_minus13",
        doc={"timezone": "-13:00"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 2, 1, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply an offset beyond -12:00",
    ),
    ExpressionTestCase(
        "tz_offset_plus15",
        doc={"timezone": "+15:00"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 21, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply an offset beyond +14:00",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_positive",
        doc={"timezone": "+05:70"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 5, 50, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an offset with more than 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over60_minutes_negative",
        doc={"timezone": "-05:70"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 18, 10, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a negative offset with more than 60 minutes",
    ),
    ExpressionTestCase(
        "tz_over24_hours_positive",
        doc={"timezone": "+25:00"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 31, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept an offset above 24 hours",
    ),
    ExpressionTestCase(
        "tz_over24_hours_negative",
        doc={"timezone": "-25:00"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 2, 13, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a negative offset below -24 hours",
    ),
    ExpressionTestCase(
        "tz_max_valid_positive",
        doc={"timezone": "+99:99"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2019, 12, 28, 7, 21, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept the maximum two-digit offset",
    ),
    ExpressionTestCase(
        "tz_max_valid_negative",
        doc={"timezone": "-99:99"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 5, 16, 39, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept the maximum negative two-digit offset",
    ),
    ExpressionTestCase(
        "tz_europe_london",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the Europe/London winter offset",
    ),
    ExpressionTestCase(
        "tz_est_abbreviation",
        doc={"timezone": "EST"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept the EST three-letter Olson identifier",
    ),
]

# Property [DST Application]: an Olson timezone applies the correct offset for the date's season.
DATEFROMPARTS_TZ_DST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_dst_summer",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 7,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 7, 1, 16, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the EDT offset in summer",
    ),
    ExpressionTestCase(
        "tz_dst_winter",
        doc={"timezone": "America/New_York"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 1,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 1, 1, 17, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the EST offset in winter",
    ),
    ExpressionTestCase(
        "tz_europe_london_bst",
        doc={"timezone": "Europe/London"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 7,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        expected=datetime(2020, 7, 1, 11, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should apply the BST offset in summer for Europe/London",
    ),
]

# Property [Null and Missing Timezone]: a null or missing timezone returns null.
DATEFROMPARTS_TZ_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_null",
        doc={"timezone": None},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        expected=None,
        msg="$dateFromParts should return null for a null timezone",
    ),
    ExpressionTestCase(
        "tz_missing_ref",
        expression={"$dateFromParts": {"year": 2020, "timezone": MISSING}},
        expected=None,
        msg="$dateFromParts should return null for a missing timezone field reference",
    ),
]

# Property [Invalid Timezone String]: an unrecognized timezone string is rejected.
DATEFROMPARTS_TZ_INVALID_STRING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "tz_invalid_str",
        doc={"timezone": "NotATimezone"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject an unrecognized timezone string",
    ),
    ExpressionTestCase(
        "tz_empty",
        doc={"timezone": ""},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject an empty timezone string",
    ),
    ExpressionTestCase(
        "tz_olson_lowercase",
        doc={"timezone": "america/new_york"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject an all-lowercase Olson name",
    ),
    ExpressionTestCase(
        "tz_olson_uppercase",
        doc={"timezone": "AMERICA/NEW_YORK"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject an all-uppercase Olson name",
    ),
    ExpressionTestCase(
        "tz_3digit_hours",
        doc={"timezone": "+100:00"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject a three-digit hour offset",
    ),
    ExpressionTestCase(
        "tz_edt_abbreviation",
        doc={"timezone": "EDT"},
        expression={
            "$dateFromParts": {
                "year": 2020,
                "month": 7,
                "day": 1,
                "hour": 12,
                "timezone": "$timezone",
            }
        },
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject EDT, which is not a valid Olson identifier",
    ),
    ExpressionTestCase(
        "tz_nonexistent_olson",
        doc={"timezone": "America/Nowhere"},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_ERROR,
        msg="$dateFromParts should reject a non-existent Olson timezone",
    ),
]

# Property [Timezone Type Rejection]: a non-string timezone produces a type error.
DATEFROMPARTS_TZ_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"tz_type_{tid}",
        doc={"timezone": val},
        expression={"$dateFromParts": {"year": 2024, "timezone": "$timezone"}},
        error_code=INVALID_TIMEZONE_TYPE_ERROR,
        msg=f"$dateFromParts should reject a {tid} timezone as a non-string",
    )
    for tid, val in [
        ("int32", 5),
        ("int64", Int64(5)),
        ("double", 5.0),
        ("decimal128", Decimal128("5")),
        ("bool", True),
        ("array", ["UTC"]),
        ("object", {"tz": "UTC"}),
        ("objectid", ObjectId("000000000000000000000000")),
        ("datetime", datetime(2020, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("binary", Binary(b"\x01")),
        ("code", Code("function(){}")),
        ("timestamp", Timestamp(0, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

DATEFROMPARTS_TIMEZONE_TESTS: list[ExpressionTestCase] = (
    DATEFROMPARTS_TZ_VALID_TESTS
    + DATEFROMPARTS_TZ_OFFSET_TESTS
    + DATEFROMPARTS_TZ_DST_TESTS
    + DATEFROMPARTS_TZ_NULL_TESTS
    + DATEFROMPARTS_TZ_INVALID_STRING_TESTS
    + DATEFROMPARTS_TZ_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMPARTS_TIMEZONE_TESTS))
def test_dateFromParts_timezone(collection, test_case: ExpressionTestCase):
    """Test $dateFromParts timezone handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
