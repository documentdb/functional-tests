"""Tests for $dateToParts field references, expression inputs, and return type."""

from datetime import datetime, timezone

import pytest

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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_DATE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field References]: the date and timezone may be supplied through field-path references.
DATETOPARTS_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref",
        doc={"d": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$dateToParts": {"date": "$d"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a date from a field reference",
    ),
    ExpressionTestCase(
        "nested_field",
        doc={"doc": {"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}},
        expression={"$dateToParts": {"date": "$doc.date"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a date from a nested-object path",
    ),
    ExpressionTestCase(
        "missing_nested",
        doc={"doc": {"x": 1}},
        expression={"$dateToParts": {"date": "$doc.missing"}},
        expected=None,
        msg="$dateToParts should return null when a nested path is missing",
    ),
    ExpressionTestCase(
        "objectid_ref",
        doc={"oid": oid_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToParts": {"date": "$oid"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept an ObjectId from a field reference",
    ),
    ExpressionTestCase(
        "timestamp_ref",
        doc={"ts": ts_from_args(2024, 6, 15, 12, 0, 0)},
        expression={"$dateToParts": {"date": "$ts"}},
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 12,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a Timestamp from a field reference",
    ),
    ExpressionTestCase(
        "timezone_from_field",
        doc={"date": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc), "tz": "America/New_York"},
        expression={"$dateToParts": {"date": "$date", "timezone": "$tz"}},
        expected={
            "year": 2024,
            "month": 1,
            "day": 1,
            "hour": 7,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should accept a timezone from a field reference",
    ),
]

# Property [Array-Valued Path]: a date path resolving to an array is rejected.
DATETOPARTS_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
                {"b": datetime(2024, 7, 1, 0, 0, 0, tzinfo=timezone.utc)},
            ]
        },
        expression={"$dateToParts": {"date": "$a.b"}},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$dateToParts should reject a date path that resolves to an array",
    ),
]

# Property [Expression Inputs]: the date may be computed by a sub-expression.
DATETOPARTS_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expression_as_date",
        expression={
            "$dateToParts": {"date": {"$dateFromParts": {"year": 2024, "month": 6, "day": 15}}}
        },
        expected={
            "year": 2024,
            "month": 6,
            "day": 15,
            "hour": 0,
            "minute": 0,
            "second": 0,
            "millisecond": 0,
        },
        msg="$dateToParts should evaluate a sub-expression for its date",
    ),
]

# Property [Return Type]: the extracted value is an object.
DATETOPARTS_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type",
        expression={
            "$type": {
                "$dateToParts": {"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}
            }
        },
        expected="object",
        msg="$dateToParts should return an object",
    ),
]

DATETOPARTS_EXPRESSIONS_TESTS: list[ExpressionTestCase] = (
    DATETOPARTS_FIELD_REF_TESTS
    + DATETOPARTS_ARRAY_PATH_TESTS
    + DATETOPARTS_EXPRESSION_INPUT_TESTS
    + DATETOPARTS_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATETOPARTS_EXPRESSIONS_TESTS))
def test_dateToParts_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateToParts field references, expression inputs, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
