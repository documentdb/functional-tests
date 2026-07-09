"""$dateSubtract timezone: Olson IDs, UTC offsets, DST, null, and invalid values and types."""

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

# Property [Olson Timezone]: a valid Olson timezone id is accepted.
DATESUBTRACT_TIMEZONE_OLSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"timezone_{tid}",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 5, "timezone": tz}
        },
        expected=datetime(2000, 1, 1, 7, 0, 0, tzinfo=timezone.utc),
        msg=f"$dateSubtract should accept the {tz} timezone",
    )
    for tid, tz in [
        ("utc", "UTC"),
        ("gmt", "GMT"),
        ("america_ny", "America/New_York"),
        ("europe_london", "Europe/London"),
        ("asia_tokyo", "Asia/Tokyo"),
        ("asia_kolkata", "Asia/Kolkata"),
        ("pacific_apia", "Pacific/Apia"),
    ]
]

# Property [UTC Offset]: syntactically valid UTC offset strings are accepted, including
# numerically out-of-range but well-formed offsets.
DATESUBTRACT_TIMEZONE_OFFSET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"timezone_offset_{tid}",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 5, "timezone": tz}
        },
        expected=datetime(2000, 1, 1, 7, 0, 0, tzinfo=timezone.utc),
        msg=f"$dateSubtract should accept the {tz} UTC offset",
    )
    for tid, tz in [
        ("colon_positive", "+05:30"),
        ("no_colon", "-0530"),
        ("hour_only", "+03"),
        ("zero", "+00:00"),
        ("max_east", "+14:00"),
        ("max_west", "-11:00"),
        ("half_hour_west", "-02:30"),
        ("45min", "+05:45"),
        ("over60_minutes_positive", "+05:70"),
        ("over60_minutes_negative", "-05:70"),
        ("over24_hours_positive", "+25:00"),
        ("over24_hours_negative", "-25:00"),
        ("max_valid_positive", "+99:99"),
        ("max_valid_negative", "-99:99"),
        ("out_of_range_east", "+15:00"),
        ("out_of_range_west", "-13:00"),
    ]
]

# Property [DST Transition]: day and larger units track wall-clock time across DST, while
# 24-hour and sub-day units subtract absolute time and do not adjust.
DATESUBTRACT_TIMEZONE_DST_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dst_spring_forward_day",
        doc={"date": datetime(2021, 3, 14, 14, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "day",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 3, 13, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a day across spring-forward",
    ),
    ExpressionTestCase(
        "dst_spring_forward_hour_24",
        doc={"date": datetime(2021, 3, 14, 15, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "hour",
                "amount": 24,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 3, 13, 15, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not DST-adjust 24 hours across spring-forward",
    ),
    ExpressionTestCase(
        "dst_spring_forward_week",
        doc={"date": datetime(2021, 3, 14, 9, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "week",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 3, 7, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a week across spring-forward",
    ),
    ExpressionTestCase(
        "dst_spring_forward_month",
        doc={"date": datetime(2021, 3, 14, 9, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "month",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 2, 14, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a month across spring-forward",
    ),
    ExpressionTestCase(
        "dst_spring_forward_quarter",
        doc={"date": datetime(2021, 4, 14, 9, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "quarter",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 1, 14, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a quarter across spring-forward",
    ),
    ExpressionTestCase(
        "dst_fall_back_day",
        doc={"date": datetime(2021, 11, 7, 11, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "day",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 11, 6, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a day across fall-back",
    ),
    ExpressionTestCase(
        "dst_fall_back_hour_24",
        doc={"date": datetime(2021, 11, 7, 10, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "hour",
                "amount": 24,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 11, 6, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not DST-adjust 24 hours across fall-back",
    ),
    ExpressionTestCase(
        "dst_fall_back_week",
        doc={"date": datetime(2021, 11, 7, 11, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "week",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 10, 31, 10, 0, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a week across fall-back",
    ),
    ExpressionTestCase(
        "dst_spring_minute_no_adjust",
        doc={"date": datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "minute",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 3, 14, 6, 59, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not DST-adjust a minute",
    ),
    ExpressionTestCase(
        "dst_spring_second_no_adjust",
        doc={"date": datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "second",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 3, 14, 6, 59, 59, tzinfo=timezone.utc),
        msg="$dateSubtract should not DST-adjust a second",
    ),
    ExpressionTestCase(
        "dst_spring_millisecond_no_adjust",
        doc={"date": datetime(2021, 3, 14, 7, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "millisecond",
                "amount": 1,
                "timezone": "America/New_York",
            }
        },
        expected=datetime(2021, 3, 14, 6, 59, 59, 999000, tzinfo=timezone.utc),
        msg="$dateSubtract should not DST-adjust a millisecond",
    ),
    ExpressionTestCase(
        "dst_europe_paris_hour_no_adjust",
        doc={"date": datetime(2020, 10, 25, 18, 10, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "hour",
                "amount": 24,
                "timezone": "Europe/Paris",
            }
        },
        expected=datetime(2020, 10, 24, 18, 10, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should not DST-adjust 24 hours in Europe/Paris",
    ),
    ExpressionTestCase(
        "dst_europe_paris_day_adjust",
        doc={"date": datetime(2020, 10, 25, 19, 10, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {
                "startDate": "$date",
                "unit": "day",
                "amount": 1,
                "timezone": "Europe/Paris",
            }
        },
        expected=datetime(2020, 10, 24, 18, 10, 0, tzinfo=timezone.utc),
        msg="$dateSubtract should DST-adjust a day across Europe/Paris fall-back",
    ),
]

# Property [Timezone Field Reference]: the timezone operand resolves from a field, and a
# missing timezone field reference returns null.
DATESUBTRACT_TIMEZONE_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timezone_field_ref",
        doc={"tz": "Europe/Paris"},
        expression={
            "$dateSubtract": {
                "startDate": datetime(2021, 2, 28, 12, 10, 5, tzinfo=timezone.utc),
                "unit": "month",
                "amount": 2,
                "timezone": "$tz",
            }
        },
        expected=datetime(2020, 12, 28, 12, 10, 5, tzinfo=timezone.utc),
        msg="$dateSubtract should resolve the timezone from a field reference",
    ),
    ExpressionTestCase(
        "timezone_missing_field_ref",
        doc={},
        expression={
            "$dateSubtract": {
                "startDate": datetime(2021, 2, 28, 12, 10, 5, tzinfo=timezone.utc),
                "unit": "month",
                "amount": 2,
                "timezone": "$tz",
            }
        },
        expected=None,
        msg="$dateSubtract should return null for a missing timezone field reference",
    ),
]

# Property [Null Timezone]: a null timezone returns null.
DATESUBTRACT_TIMEZONE_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "timezone_null",
        doc={"date": datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)},
        expression={
            "$dateSubtract": {"startDate": "$date", "unit": "hour", "amount": 5, "timezone": None}
        },
        expected=None,
        msg="$dateSubtract should return null when the timezone is null",
    ),
]

DATESUBTRACT_TIMEZONE_SUCCESS_TESTS = (
    DATESUBTRACT_TIMEZONE_OLSON_TESTS
    + DATESUBTRACT_TIMEZONE_OFFSET_TESTS
    + DATESUBTRACT_TIMEZONE_DST_TESTS
    + DATESUBTRACT_TIMEZONE_FIELD_REF_TESTS
    + DATESUBTRACT_TIMEZONE_NULL_TESTS
)

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

DATESUBTRACT_TIMEZONE_ERROR_TESTS = (
    DATESUBTRACT_TIMEZONE_INVALID_TESTS + DATESUBTRACT_TIMEZONE_TYPE_ERROR_TESTS
)

DATESUBTRACT_TIMEZONE_TESTS = (
    DATESUBTRACT_TIMEZONE_SUCCESS_TESTS + DATESUBTRACT_TIMEZONE_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATESUBTRACT_TIMEZONE_TESTS))
def test_dateSubtract_timezone(collection, test_case: ExpressionTestCase):
    """Test $dateSubtract timezone handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
