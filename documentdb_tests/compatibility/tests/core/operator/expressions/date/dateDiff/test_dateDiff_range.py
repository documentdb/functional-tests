"""$dateDiff across the representable date range: epoch-crossing and extreme boundary values."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
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
    OID_MAX_SIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

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

DATEDIFF_RANGE_TESTS: list[ExpressionTestCase] = (
    DATEDIFF_EPOCH_TESTS + DATEDIFF_EXTREME_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_RANGE_TESTS))
def test_dateDiff_range(collection, test_case: ExpressionTestCase):
    """Test $dateDiff counts correctly across epoch and extreme boundary dates."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
