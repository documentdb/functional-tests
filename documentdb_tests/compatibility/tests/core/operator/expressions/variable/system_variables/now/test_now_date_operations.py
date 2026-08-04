"""$$NOW as a date operand: acceptance by the date-operator family, round-trips, and
per-numeric-type arithmetic. Per-operator return types, per-unit/timezone behavior, and
error depth live in the date operators' own folders.
"""

from datetime import datetime, timezone

import pytest
from bson import Decimal128, Int64
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.aggregate

NOW_DATE_OPERATOR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="date_component_type_year",
        expression={"$type": {"$year": "$$NOW"}},
        expected="int",
        msg="$$NOW should be accepted as the date operand of an int-returning date operator",
    ),
    ExpressionTestCase(
        id="iso_week_year_component_type",
        expression={"$type": {"$isoWeekYear": "$$NOW"}},
        expected="long",
        msg="$$NOW should be accepted as the date operand of a long-returning date operator",
    ),
    ExpressionTestCase(
        id="date_to_string_round_trip",
        expression={
            "$eq": [
                {"$dateFromString": {"dateString": {"$dateToString": {"date": "$$NOW"}}}},
                "$$NOW",
            ]
        },
        expected=True,
        msg="$dateToString of $$NOW should round-trip through $dateFromString",
    ),
    ExpressionTestCase(
        id="date_to_string_custom_format",
        expression={
            "$type": {"$dateToString": {"date": "$$NOW", "format": "%Y-%m-%dT%H:%M:%S.%LZ"}}
        },
        expected="string",
        msg="$dateToString of $$NOW with a custom format should return a string",
    ),
    ExpressionTestCase(
        id="date_parts_round_trip_through_date_from_parts",
        expression={
            "$eq": [
                {
                    "$dateFromParts": {
                        "year": {"$year": "$$NOW"},
                        "month": {"$month": "$$NOW"},
                        "day": {"$dayOfMonth": "$$NOW"},
                        "hour": {"$hour": "$$NOW"},
                        "minute": {"$minute": "$$NOW"},
                        "second": {"$second": "$$NOW"},
                        "millisecond": {"$millisecond": "$$NOW"},
                    }
                },
                "$$NOW",
            ]
        },
        expected=True,
        msg="Calendar components of $$NOW should rebuild the same instant via $dateFromParts",
    ),
    ExpressionTestCase(
        id="date_to_parts_field_count",
        expression={"$size": {"$objectToArray": {"$dateToParts": {"date": "$$NOW"}}}},
        expected=7,
        msg="$dateToParts of $$NOW should return seven calendar parts",
    ),
    ExpressionTestCase(
        id="date_to_parts_iso8601_field_count",
        expression={
            "$size": {"$objectToArray": {"$dateToParts": {"date": "$$NOW", "iso8601": True}}}
        },
        expected=7,
        msg="$dateToParts of $$NOW with iso8601 should return seven ISO parts",
    ),
    ExpressionTestCase(
        id="date_trunc_to_millisecond_is_now",
        expression={"$eq": [{"$dateTrunc": {"date": "$$NOW", "unit": "millisecond"}}, "$$NOW"]},
        expected=True,
        msg="$dateTrunc of $$NOW to millisecond should be a no-op",
    ),
    ExpressionTestCase(
        id="date_diff_to_itself_is_zero",
        expression={"$dateDiff": {"startDate": "$$NOW", "endDate": "$$NOW", "unit": "millisecond"}},
        expected=Int64(0),
        msg="$dateDiff between two $$NOW references should be 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOW_DATE_OPERATOR_TESTS))
def test_now_date_operators(collection, test: ExpressionTestCase):
    """Test date operators accept $$NOW as their date operand (round-trips, no-ops, types)."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


NOW_ARITHMETIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="add_int",
        expression={"$subtract": [{"$add": ["$$NOW", 1000]}, "$$NOW"]},
        expected=Int64(1000),
        msg="$$NOW plus an int should shift the date by that many milliseconds",
    ),
    ExpressionTestCase(
        id="add_long",
        expression={"$subtract": [{"$add": ["$$NOW", Int64(1000)]}, "$$NOW"]},
        expected=Int64(1000),
        msg="$$NOW plus a long should shift the date by that many milliseconds",
    ),
    ExpressionTestCase(
        id="add_double",
        expression={"$subtract": [{"$add": ["$$NOW", 1000.0]}, "$$NOW"]},
        expected=Int64(1000),
        msg="$$NOW plus a double should shift the date by that many milliseconds",
    ),
    ExpressionTestCase(
        id="add_decimal128",
        expression={"$subtract": [{"$add": ["$$NOW", Decimal128("1000")]}, "$$NOW"]},
        expected=Int64(1000),
        msg="$$NOW plus a decimal128 should shift the date by that many milliseconds",
    ),
    ExpressionTestCase(
        id="subtract_int",
        expression={"$subtract": ["$$NOW", {"$subtract": ["$$NOW", 1000]}]},
        expected=Int64(1000),
        msg="$$NOW minus an int should move the date earlier by that many milliseconds",
    ),
    ExpressionTestCase(
        id="subtract_produces_earlier_date",
        expression={"$lt": [{"$subtract": ["$$NOW", 1000]}, "$$NOW"]},
        expected=True,
        msg="$$NOW minus a positive numeric should produce an earlier date",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NOW_ARITHMETIC_TESTS))
def test_now_arithmetic(collection, test: ExpressionTestCase):
    """Test arithmetic on $$NOW with numeric operands; rounding/error depth belongs to $add."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


def test_now_date_diff_from_stored_date(collection):
    """Test $dateDiff from a stored past date to $$NOW is positive."""
    result = execute_expression_with_insert(
        collection,
        {
            "$gt": [
                {
                    "$dateDiff": {
                        "startDate": "$stored",
                        "endDate": "$$NOW",
                        "unit": "year",
                    }
                },
                0,
            ]
        },
        {"stored": datetime(2000, 1, 1)},
    )
    assert_expression_result(
        result,
        expected=True,
        msg="$dateDiff from a stored past date to $$NOW should be positive",
    )


def test_now_elapsed_milliseconds_from_stored_date(collection):
    """Test elapsed time computed as $$NOW minus a stored date is positive."""
    result = execute_expression_with_insert(
        collection,
        {"$gt": [{"$subtract": ["$$NOW", "$stored"]}, 0]},
        {"stored": datetime(2000, 1, 1)},
    )
    assert_expression_result(
        result,
        expected=True,
        msg="$$NOW minus a stored past date should yield a positive elapsed duration",
    )


def test_now_decodes_as_timezone_aware_utc(collection):
    """Test a $$NOW-derived date decodes as a timezone-aware UTC datetime."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {"$project": {"_id": 0, "t": "$$NOW"}},
            ],
            "cursor": {},
        },
        codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc),
    )
    assertSuccess(
        result,
        [{"tzinfo": "UTC"}],
        msg="A $$NOW-derived date should decode as a timezone-aware UTC datetime",
        transform=lambda docs: [{"tzinfo": str(doc["t"].tzinfo)} for doc in docs],
    )
