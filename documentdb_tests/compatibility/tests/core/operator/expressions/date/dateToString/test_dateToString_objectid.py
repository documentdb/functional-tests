"""Tests for $dateToString formatting of ObjectId date inputs, including boundaries."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    OID_MAX_SIGNED32,
    OID_MAX_UNSIGNED32,
    OID_MIN_SIGNED32,
)

# Property [ObjectId Date]: an ObjectId is formatted using its embedded timestamp, across
# boundaries.
DATETOSTRING_OBJECTID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "oid_ymd",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should format an ObjectId date with %Y-%m-%d",
    ),
    ExpressionTestCase(
        "oid_hms",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%H:%M:%S"}},
        expected="12:00:00",
        msg="$dateToString should format an ObjectId date with %H:%M:%S",
    ),
    ExpressionTestCase(
        "oid_default_fmt",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date"}},
        expected="2024-06-15T12:00:00.000Z",
        msg="$dateToString should format an ObjectId date with the default format",
    ),
    ExpressionTestCase(
        "oid_with_tz",
        doc={"date": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d", "timezone": "UTC"}},
        expected="2024-06-15",
        msg="$dateToString should format an ObjectId date with a timezone",
    ),
    ExpressionTestCase(
        "oid_epoch",
        doc={"date": oid_from_args(1970, 1, 1, 0, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1970-01-01",
        msg="$dateToString should format an ObjectId date at the epoch",
    ),
    ExpressionTestCase(
        "oid_future",
        doc={"date": oid_from_args(2035, 6, 15, 0, 0, 0)},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2035-06-15",
        msg="$dateToString should format a future ObjectId date",
    ),
    ExpressionTestCase(
        "oid_boundary_max_s32",
        doc={"date": OID_MAX_SIGNED32},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="2038-01-19",
        msg="$dateToString should format a max signed 32-bit ObjectId date",
    ),
    ExpressionTestCase(
        "oid_boundary_min_s32",
        doc={"date": OID_MIN_SIGNED32},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1901-12-13",
        msg="$dateToString should format a min signed 32-bit ObjectId date",
    ),
    ExpressionTestCase(
        "oid_boundary_max_u32",
        doc={"date": OID_MAX_UNSIGNED32},
        expression={"$dateToString": {"date": "$date", "format": "%Y-%m-%d"}},
        expected="1969-12-31",
        msg="$dateToString should format a max unsigned 32-bit ObjectId date",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_OBJECTID_TESTS))
def test_dateToString_objectid(collection, test_case: ExpressionTestCase):
    """Test $dateToString with ObjectId date inputs."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
