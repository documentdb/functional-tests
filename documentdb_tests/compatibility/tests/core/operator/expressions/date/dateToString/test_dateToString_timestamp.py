"""Tests for $dateToString formatting of BSON Timestamp date inputs, including boundaries."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import TS_MAX_SIGNED32, TS_MAX_UNSIGNED32

# Property [Timestamp Date]: a BSON Timestamp is formatted using its seconds field, across
# boundaries.
DATETOSTRING_TIMESTAMP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "ts_ymd",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should format a Timestamp date with %Y-%m-%d",
    ),
    ExpressionTestCase(
        "ts_hms",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%H:%M:%S"}},
        expected="12:00:00",
        msg="$dateToString should format a Timestamp date with %H:%M:%S",
    ),
    ExpressionTestCase(
        "ts_default_fmt",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date"}},
        expected="2024-06-15T12:00:00.000Z",
        msg="$dateToString should format a Timestamp date with the default format",
    ),
    ExpressionTestCase(
        "ts_with_tz",
        doc={"date": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d", "timezone": "UTC"}},
        expected="2024-06-15",
        msg="$dateToString should format a Timestamp date with a timezone",
    ),
    ExpressionTestCase(
        "ts_epoch",
        doc={"date": ts_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1970-01-01",
        msg="$dateToString should format a Timestamp date at the epoch",
    ),
    ExpressionTestCase(
        "ts_future",
        doc={"date": ts_from_args(2100, 6, 15, 0, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2100-06-15",
        msg="$dateToString should format a future Timestamp date",
    ),
    ExpressionTestCase(
        "ts_boundary_max_s32",
        doc={"date": TS_MAX_SIGNED32},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2038-01-19",
        msg="$dateToString should format a max signed 32-bit Timestamp date",
    ),
    ExpressionTestCase(
        "ts_boundary_max_u32",
        doc={"date": TS_MAX_UNSIGNED32},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2106-02-07",
        msg="$dateToString should format a max unsigned 32-bit Timestamp date",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_TIMESTAMP_TESTS))
def test_dateToString_timestamp(collection, test_case: ExpressionTestCase):
    """Test $dateToString with Timestamp date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
