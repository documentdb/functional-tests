"""Tests for $dateToString field references, expression inputs, and return type."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import ExpressionTestCase
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.date_utils import (
    oid_from_args,
    ts_from_args,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_DATE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field References]: each argument may be supplied through a field-path reference.
DATETOSTRING_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_date",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$d", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should accept a date from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_format",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc), "fmt": "%Y-%m-%d"},
        expression={"$dateToString": {"date": "$d", "format": "$fmt"}},
        expected="2024-06-15",
        msg="$dateToString should accept a format from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_timezone",
        doc={"d": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc), "tz": "America/New_York"},
        expression={"$dateToString": {"date": "$d", "format": "%H:%M", "timezone": "$tz"}},
        expected="07:00",
        msg="$dateToString should accept a timezone from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_onNull",
        doc={"fb": "FALLBACK"},
        expression={"$dateToString": {"date": "$d", "format": "%Y", "onNull": "$fb"}},
        expected="FALLBACK",
        msg="$dateToString should accept an onNull value from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_objectid",
        doc={"oid": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$oid", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should accept an ObjectId date from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_timestamp",
        doc={"ts": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToString": {"date": "$ts", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should accept a Timestamp date from a field reference",
    ),
    ExpressionTestCase(
        "nested_field",
        doc={"a": {"b": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)}},
        expression={"$dateToString": {"date": "$a.b", "format": "%Y-%m-%d"}},
        expected="2024-06-15",
        msg="$dateToString should resolve a nested field-path date",
    ),
    ExpressionTestCase(
        "missing_timezone_field_ref",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": "%Y", "timezone": "$tz"}},
        expected=None,
        msg="$dateToString should return null when the referenced timezone field is missing",
    ),
    ExpressionTestCase(
        "missing_format_field_ref",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToString": {"date": "$date", "format": "$fmt"}},
        expected=None,
        msg="$dateToString should return null when the referenced format field is missing",
    ),
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 6, 15, tzinfo=timezone.utc)},
                {"b": datetime(2025, 1, 1, tzinfo=timezone.utc)},
            ]
        },
        expression={"$dateToString": {"date": "$a.b", "format": "%Y"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToString should reject a field path that resolves to an array of dates",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATETOSTRING_FIELD_REF_TESTS))
def test_dateToString_field_references(collection, test_case: ExpressionTestCase):
    """Test $dateToString field references."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


def test_dateToString_expression_as_date(collection):
    """Test $dateToString with an expression operator as the date input."""
    result = execute_expression(
        collection,
        {
            "$dateToString": {
                "date": {"$dateFromString": {"dateString": "2024-06-15"}},
                "format": "%Y-%m-%d",
            }
        },
    )
    assert_expression_result(result, expected="2024-06-15")


def test_dateToString_return_type(collection):
    """Test $dateToString return type."""
    result = execute_expression(
        collection,
        {
            "$type": {
                "$dateToString": {
                    "date": datetime(2024, 6, 15, tzinfo=timezone.utc),
                    "format": "%Y",
                }
            }
        },
    )
    assert_expression_result(result, expected="string")
