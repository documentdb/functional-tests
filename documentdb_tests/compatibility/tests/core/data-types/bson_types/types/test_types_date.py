from datetime import datetime, timedelta, timezone

import pytest
from bson.datetime_ms import DatetimeMS

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

from ..utils.round_trip_test_case import RoundTripTestCase

# Property [Date Signed Epoch Offset]: BSON Date stores time as a signed
# 64-bit millisecond offset from the Unix epoch.
DATE_ORDERING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pre_epoch_before_post_epoch",
        expression={
            "$lt": [
                datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                datetime(1970, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="Pre-epoch date (negative offset) should sort before post-epoch date",
    ),
    ExpressionTestCase(
        "min_before_max",
        expression={
            "$lt": [
                datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="Minimum representable date should sort before maximum representable date",
    ),
]

# Property [Date Millisecond Precision]: BSON Date has millisecond granularity;
# sub-millisecond differences are truncated.
DATE_PRECISION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "sub_millisecond_truncated_equal",
        # Python datetime carries microseconds but BSON Date stores
        # milliseconds, so 0us and 999us within the same ms compare equal.
        expression={
            "$eq": [
                datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 0, 0, 0, 999, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="Sub-millisecond differences should be truncated to the same ms",
    ),
    ExpressionTestCase(
        "crossing_millisecond_boundary_not_equal",
        # 999us rounds to ms 0, 1000us rounds to ms 1 - distinct values.
        expression={
            "$eq": [
                datetime(2024, 1, 1, 0, 0, 0, 999, tzinfo=timezone.utc),
                datetime(2024, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
            ]
        },
        expected=False,
        msg="Crossing a millisecond boundary should produce distinct date values",
    ),
]

# Property [Date Timezone Normalization]: BSON Date stores only UTC
# milliseconds; timezone offset is normalized away.
DATE_TIMEZONE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "same_instant_different_tz_equal",
        expression={
            "$eq": [
                datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5))),
                datetime(2024, 6, 15, 17, 0, 0, tzinfo=timezone.utc),
            ]
        },
        expected=True,
        msg="Same instant in different timezones should compare equal",
    ),
    ExpressionTestCase(
        "same_wall_clock_different_tz_not_equal",
        expression={
            "$eq": [
                datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5))),
                datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            ]
        },
        expected=False,
        msg="Same wall-clock time in different timezones should not compare equal",
    ),
]

DATE_COMPARISON_TESTS = DATE_ORDERING_TESTS + DATE_PRECISION_TESTS + DATE_TIMEZONE_TESTS


@pytest.mark.parametrize("test", pytest_params(DATE_COMPARISON_TESTS))
def test_date_comparison(collection, test):
    """Test Date BSON type comparison semantics."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# Property [Date Round-Trip Fidelity]: Date values survive insert and retrieval
# unchanged across the full representable range.
DATE_ROUND_TRIP_TESTS: list[RoundTripTestCase] = [
    RoundTripTestCase(
        "min_date",
        value=datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        expected=datetime(1, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="Minimum representable date should survive round-trip",
    ),
    RoundTripTestCase(
        "pre_epoch",
        value=datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        expected=datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        msg="Pre-epoch date should survive round-trip",
    ),
    RoundTripTestCase(
        "epoch",
        value=datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        expected=datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="Epoch date should survive round-trip",
    ),
    RoundTripTestCase(
        "max_date",
        value=datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
        expected=datetime(9999, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
        msg="Maximum representable date should survive round-trip",
    ),
    RoundTripTestCase(
        "non_utc_normalized_to_utc",
        value=datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone(timedelta(hours=-5))),
        expected=datetime(2024, 6, 15, 17, 0, 0, tzinfo=timezone.utc),
        msg="Non-UTC date should be stored as equivalent UTC instant",
    ),
    RoundTripTestCase(
        "datetime_ms_epoch",
        value=DatetimeMS(0),
        expected=datetime(1970, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="DatetimeMS epoch should be decoded as the UTC epoch datetime.",
    ),
    RoundTripTestCase(
        "datetime_ms_before_epoch",
        value=DatetimeMS(-1),
        expected=datetime(1969, 12, 31, 23, 59, 59, 999000, tzinfo=timezone.utc),
        msg="DatetimeMS before epoch should be decoded as the equivalent UTC datetime.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATE_ROUND_TRIP_TESTS))
def test_date_round_trip(collection, test):
    """Test Date values survive storage and retrieval unchanged."""
    collection.insert_one({"_id": test.id, "v": test.value})
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": test.id}})
    assertSuccess(result, [{"_id": test.id, "v": test.expected}], msg=test.msg)
