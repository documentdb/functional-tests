"""Tests for $dateFromParts field references, expression inputs, and return type."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import DATEFROMPARTS_INVALID_TYPE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

# Property [Field References]: field values may be supplied through field-path references.
DATEFROMPARTS_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_ymd",
        doc={"y": 2024, "m": 6, "d": 15},
        expression={"$dateFromParts": {"year": "$y", "month": "$m", "day": "$d"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept calendar fields from field references",
    ),
    ExpressionTestCase(
        "field_ref_iso",
        doc={"wy": 2017, "w": 6, "dow": 3},
        expression={
            "$dateFromParts": {"isoWeekYear": "$wy", "isoWeek": "$w", "isoDayOfWeek": "$dow"}
        },
        expected=datetime(2017, 2, 8, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept ISO fields from field references",
    ),
    ExpressionTestCase(
        "nested_field",
        doc={"doc": {"y": 2024, "m": 6, "d": 15}},
        expression={"$dateFromParts": {"year": "$doc.y", "month": "$doc.m", "day": "$doc.d"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept fields from a nested-object path",
    ),
    ExpressionTestCase(
        "timezone_field_ref",
        doc={"y": 2020, "tz": "+05:30"},
        expression={
            "$dateFromParts": {"year": "$y", "month": 1, "day": 1, "hour": 0, "timezone": "$tz"}
        },
        expected=datetime(2019, 12, 31, 18, 30, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should accept a timezone from a field reference",
    ),
]

# Property [Array-Valued Path]: a field path resolving to an array is rejected.
DATEFROMPARTS_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={"a": [{"b": 2021}, {"b": 2022}]},
        expression={"$dateFromParts": {"year": "$a.b"}},
        error_code=DATEFROMPARTS_INVALID_TYPE_ERROR,
        msg="$dateFromParts should reject a year path that resolves to an array",
    ),
]

# Property [Expression Inputs]: field values may be computed by sub-expressions.
DATEFROMPARTS_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expression_as_input",
        expression={
            "$dateFromParts": {"year": {"$add": [2000, 20]}, "month": {"$subtract": [12, 6]}}
        },
        expected=datetime(2020, 6, 1, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromParts should evaluate sub-expressions for its fields",
    ),
]

# Property [Return Type]: the constructed value is a date.
DATEFROMPARTS_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_date",
        expression={"$type": {"$dateFromParts": {"year": 2021, "month": 1, "day": 1}}},
        expected="date",
        msg="$dateFromParts should return a date",
    ),
]

DATEFROMPARTS_EXPRESSIONS_TESTS: list[ExpressionTestCase] = (
    DATEFROMPARTS_FIELD_REF_TESTS
    + DATEFROMPARTS_ARRAY_PATH_TESTS
    + DATEFROMPARTS_EXPRESSION_INPUT_TESTS
    + DATEFROMPARTS_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMPARTS_EXPRESSIONS_TESTS))
def test_dateFromParts_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateFromParts field references, expression inputs, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
