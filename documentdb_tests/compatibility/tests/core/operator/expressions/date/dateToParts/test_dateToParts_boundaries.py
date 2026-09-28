"""Tests for $dateToParts extraction across the date range and at epoch/32-bit boundaries."""

from datetime import datetime, timezone

import pytest

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
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
    TS_MAX_SIGNED32,
    TS_MAX_UNSIGNED32,
)

# Property [Date Range]: extraction works across the representable date range.
DATETOPARTS_RANGE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "epoch",
        doc={"date": DATE_EPOCH},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1970,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts at the epoch",
    ),
    ExpressionTestCase(
        "pre_epoch",
        doc={"date": datetime(1969, 12, 31, 23, 59, 59, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1969,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts just before the epoch",
    ),
    ExpressionTestCase(
        "distant_past",
        doc={"date": datetime(1900, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1900,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a distant-past date",
    ),
    ExpressionTestCase(
        "distant_future",
        doc={"date": datetime(2100, 3, 1, 0, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2100,
            "month": 3,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a distant-future date",
    ),
]

# Property [Boundary Values]: millisecond-resolution and 32-bit epoch boundaries extract correctly.
DATETOPARTS_BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_ms_epoch",
        doc={"date": DATE_MS_EPOCH},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1970,
            "month": 1,
            "day": 1,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a millisecond date at the epoch",
    ),
    ExpressionTestCase(
        "date_ms_before_epoch",
        doc={"date": DATE_MS_BEFORE_EPOCH},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1969,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 999,
        },
        msg="$dateToParts should extract parts from a millisecond date just before the epoch",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2038,
            "month": 1,
            "day": 19,
            "hour": 3,
            "minute": 14,
            "second": 7,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a Timestamp at the max signed 32-bit second",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2106,
            "month": 2,
            "day": 7,
            "hour": 6,
            "minute": 28,
            "second": 15,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from a Timestamp at the max unsigned 32-bit second",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 2038,
            "month": 1,
            "day": 19,
            "hour": 3,
            "minute": 14,
            "second": 7,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from an ObjectId at the max signed 32-bit second",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1901,
            "month": 12,
            "day": 13,
            "hour": 20,
            "minute": 45,
            "second": 52,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from an ObjectId at the min signed 32-bit second",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$dateToParts": {"date": "$date"}},
        expected={
            "year": 1969,
            "month": 12,
            "day": 31,
            "hour": 23,
            "minute": 59,
            "second": 59,
            "millisecond": 0,
        },
        msg="$dateToParts should extract parts from an ObjectId at the max unsigned 32-bit second",
    ),
]

DATETOPARTS_BOUNDARIES_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_RANGE_TESTS + DATETOPARTS_BOUNDARY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_BOUNDARIES_TESTS))
def test_dateToParts_boundaries(collection, test_case: ExpressionTestCase):
    """Test $dateToParts range and boundary extraction."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
