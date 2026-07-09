"""$dateDiff leap years, ObjectId/Timestamp/DatetimeMS date sources, and extreme boundaries."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DATE_MS_BEFORE_EPOCH,
    DATE_MS_EPOCH,
    DATE_MS_MAX,
    DATE_MS_MIN,
    DATE_YEAR_1900,
    INT64_ZERO,
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Leap Year]: day counting honors leap years, including the century leap rule.
DATEDIFF_LEAP_YEAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "leap_feb28_mar1",
        expression={
            "$dateDiff": {
                "startDate": datetime(2020, 2, 28, tzinfo=timezone.utc),
                "endDate": datetime(2020, 3, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should count two days across Feb 29 in a leap year",
    ),
    ExpressionTestCase(
        "non_leap_feb28_mar1",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 2, 28, tzinfo=timezone.utc),
                "endDate": datetime(2021, 3, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one day from Feb 28 in a non-leap year",
    ),
    ExpressionTestCase(
        "full_leap_year",
        expression={
            "$dateDiff": {
                "startDate": datetime(2020, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(366),
        msg="$dateDiff should count 366 days across a full leap year",
    ),
    ExpressionTestCase(
        "full_non_leap_year",
        expression={
            "$dateDiff": {
                "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2022, 1, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(365),
        msg="$dateDiff should count 365 days across a full non-leap year",
    ),
    ExpressionTestCase(
        "century_leap_2000",
        expression={
            "$dateDiff": {
                "startDate": datetime(2000, 2, 28, tzinfo=timezone.utc),
                "endDate": datetime(2000, 3, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(2),
        msg="$dateDiff should treat 2000 as a leap century year",
    ),
    ExpressionTestCase(
        "century_non_leap_1900",
        expression={
            "$dateDiff": {
                "startDate": datetime(1900, 2, 28, tzinfo=timezone.utc),
                "endDate": datetime(1900, 3, 1, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should treat 1900 as a non-leap century year",
    ),
]

# Property [ObjectId Source]: an ObjectId date operand uses its embedded timestamp for either
# position and for the timezone option.
DATEDIFF_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_day",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 1, 6, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should count days between two ObjectId dates",
    ),
    ExpressionTestCase(
        "oid_hour",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2024, 1, 1, 5, 0, 0, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should count hours from an ObjectId startDate",
    ),
    ExpressionTestCase(
        "oid_month",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 6, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(5),
        msg="$dateDiff should count months between two ObjectId dates",
    ),
    ExpressionTestCase(
        "oid_year",
        doc={
            "s": oid_from_args(2024, 1, 1, 0, 0, 0),
            "e": oid_from_args(2024, 12, 31, 23, 59, 59),
        },
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year"}},
        expected=INT64_ZERO,
        msg="$dateDiff should count zero years within the same ObjectId year",
    ),
    ExpressionTestCase(
        "oid_with_tz",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 1, 6, 0, 0, 0)},
        expression={
            "$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day", "timezone": "UTC"}
        },
        expected=Int64(5),
        msg="$dateDiff should count days between ObjectId dates with a timezone",
    ),
    ExpressionTestCase(
        "oid_negative",
        doc={"s": oid_from_args(2024, 6, 1, 0, 0, 0), "e": oid_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(-5),
        msg="$dateDiff should return a negative month difference between ObjectId dates",
    ),
    ExpressionTestCase(
        "oid_endDate",
        doc={"e": oid_from_args(2024, 1, 6, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": "$e",
                "unit": "day",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept an ObjectId endDate",
    ),
    ExpressionTestCase(
        "oid_epoch",
        doc={"s": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1970, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should accept an epoch ObjectId startDate",
    ),
    ExpressionTestCase(
        "oid_far_future",
        doc={"s": oid_from_args(2035, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2035, 6, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept a far-future ObjectId startDate",
    ),
]

# Property [Timestamp Source]: a Timestamp date operand uses its seconds for either position
# and for the timezone option.
DATEDIFF_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_day",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 6, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should count days between two Timestamp dates",
    ),
    ExpressionTestCase(
        "ts_hour",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2024, 1, 1, 5, 0, 0, tzinfo=timezone.utc),
                "unit": "hour",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should count hours from a Timestamp startDate",
    ),
    ExpressionTestCase(
        "ts_month",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 6, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(5),
        msg="$dateDiff should count months between two Timestamp dates",
    ),
    ExpressionTestCase(
        "ts_year",
        doc={
            "s": ts_from_args(2024, 1, 1, 0, 0, 0),
            "e": ts_from_args(2024, 12, 31, 23, 59, 59),
        },
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year"}},
        expected=INT64_ZERO,
        msg="$dateDiff should count zero years within the same Timestamp year",
    ),
    ExpressionTestCase(
        "ts_with_tz",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 6, 0, 0, 0)},
        expression={
            "$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day", "timezone": "UTC"}
        },
        expected=Int64(5),
        msg="$dateDiff should count days between Timestamp dates with a timezone",
    ),
    ExpressionTestCase(
        "ts_negative",
        doc={"s": ts_from_args(2024, 6, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(-5),
        msg="$dateDiff should return a negative month difference between Timestamp dates",
    ),
    ExpressionTestCase(
        "ts_epoch",
        doc={"s": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1970, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should accept an epoch Timestamp startDate",
    ),
    ExpressionTestCase(
        "ts_far_future",
        doc={"s": ts_from_args(2100, 1, 1, 0, 0, 0)},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2100, 6, 1, tzinfo=timezone.utc),
                "unit": "month",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should accept a far-future Timestamp startDate",
    ),
]

# Property [Mixed Source]: ObjectId and Timestamp date operands can be combined.
DATEDIFF_MIXED_SOURCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_ts_mixed",
        doc={"s": oid_from_args(2024, 1, 1, 0, 0, 0), "e": ts_from_args(2024, 1, 6, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should count days from an ObjectId startDate to a Timestamp endDate",
    ),
    ExpressionTestCase(
        "ts_oid_mixed",
        doc={"s": ts_from_args(2024, 1, 1, 0, 0, 0), "e": oid_from_args(2024, 6, 1, 0, 0, 0)},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "month"}},
        expected=Int64(5),
        msg="$dateDiff should count months from a Timestamp startDate to an ObjectId endDate",
    ),
]

# Property [Epoch Crossing]: dates around the Unix epoch and far from it are counted correctly.
DATEDIFF_EPOCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch_date",
        doc={"s": DATE_EPOCH},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1970, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one day from the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch",
        expression={
            "$dateDiff": {
                "startDate": datetime(1969, 12, 31, tzinfo=timezone.utc),
                "endDate": DATE_EPOCH,
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one day across the epoch from 1969",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"s": DATE_YEAR_1900},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1900, 12, 31, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(364),
        msg="$dateDiff should count days within a distant past year",
    ),
    ExpressionTestCase(
        "distant_future",
        expression={
            "$dateDiff": {
                "startDate": datetime(2100, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2100, 12, 31, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(364),
        msg="$dateDiff should count days within a distant future year",
    ),
    ExpressionTestCase(
        "cross_epoch",
        expression={
            "$dateDiff": {
                "startDate": datetime(1969, 6, 1, tzinfo=timezone.utc),
                "endDate": datetime(1970, 6, 1, tzinfo=timezone.utc),
                "unit": "year",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one year crossing the epoch",
    ),
]

# Property [Extreme Boundary]: DatetimeMS, Timestamp, and ObjectId values at the edges of the
# 32-bit and 64-bit ranges are counted correctly.
DATEDIFF_EXTREME_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch_diff",
        doc={"s": DATE_MS_EPOCH},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(1970, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count one day from an epoch DatetimeMS",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch_diff",
        doc={"s": DATE_MS_BEFORE_EPOCH},
        expression={"$dateDiff": {"startDate": "$s", "endDate": DATE_EPOCH, "unit": "millisecond"}},
        expected=Int64(1),
        msg="$dateDiff should count one millisecond from just before the epoch",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"s": TS_MAX_SIGNED32, "e": TS_MAX_UNSIGNED32},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year"}},
        expected=Int64(68),
        msg="$dateDiff should count years between the signed and unsigned 32-bit Timestamp limits",
    ),
    ExpressionTestCase(
        "oid_max_signed32",
        doc={"s": OID_MAX_SIGNED32},
        expression={
            "$dateDiff": {
                "startDate": "$s",
                "endDate": datetime(2038, 1, 20, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        expected=Int64(1),
        msg="$dateDiff should count from a max signed 32-bit ObjectId",
    ),
    ExpressionTestCase(
        "oid_high_bit_pre_epoch",
        doc={"s": OID_MIN_SIGNED32},
        expression={"$dateDiff": {"startDate": "$s", "endDate": DATE_EPOCH, "unit": "year"}},
        expected=Int64(69),
        msg="$dateDiff should handle an ObjectId with the high timestamp bit set as pre-epoch",
    ),
    ExpressionTestCase(
        "ms_overflow_int64",
        doc={"s": DATE_MS_MIN, "e": DATE_MS_MAX},
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year"}},
        expected=Int64(584_554_049),
        msg="$dateDiff should count years between the minimum and maximum representable dates",
    ),
]

DATEDIFF_TYPE_TESTS = (
    DATEDIFF_LEAP_YEAR_TESTS
    + DATEDIFF_OBJECTID_TESTS
    + DATEDIFF_TIMESTAMP_TESTS
    + DATEDIFF_MIXED_SOURCE_TESTS
    + DATEDIFF_EPOCH_TESTS
    + DATEDIFF_EXTREME_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_TYPE_TESTS))
def test_dateDiff_types(collection, test_case: ExpressionTestCase):
    """Test $dateDiff date-source types and boundaries."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
