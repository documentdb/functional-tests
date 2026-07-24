"""Tests for $year argument forms, field-path resolution, expression input, and return type."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
    ISO_DATE_MISSING_DATE_ERROR,
    ISO_DATE_UNKNOWN_FIELD_ERROR,
    TYPE_MISMATCH_DATE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Forms]: the operand may be a date, a single-element operand array, or a
# document with exactly a date field; other operand shapes and scalar non-date operands are
# rejected.
YEAR_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "document_form_missing_date",
        expression={"$year": {"timezone": "UTC"}},
        error_code=ISO_DATE_MISSING_DATE_ERROR,
        msg="$year should error when the document form omits the date field",
    ),
    ExpressionTestCase(
        "extra_field",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "extra": 1}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$year should error for an unknown field in the document form",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"a": "$date"}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$year should treat an object with an unknown key as an invalid document form",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$year": []},
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$year should error for an empty operand array",
    ),
    ExpressionTestCase(
        "two_element_array",
        expression={
            "$year": [
                datetime(2024, 6, 15, tzinfo=timezone.utc),
                datetime(2024, 7, 15, tzinfo=timezone.utc),
            ]
        },
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$year should error for a multi-element operand array",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$year": [datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)]},
        expected=2024,
        msg="$year should accept a single-element operand array as the date",
    ),
    ExpressionTestCase(
        "invalid_string",
        expression={"$year": "string"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$year should reject a literal string operand",
    ),
    ExpressionTestCase(
        "invalid_number",
        expression={"$year": 123},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$year should reject a literal number operand",
    ),
    ExpressionTestCase(
        "invalid_boolean",
        expression={"$year": True},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$year should reject a literal boolean operand",
    ),
]

# Property [Input Expression Types]: the operator accepts each expression type it can receive
# as the date argument (literal, field reference in shorthand and document form, an array
# expression holding a field reference, a nested field path, and a nested expression); a path
# that resolves to an array feeds the type contract and errors.
YEAR_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_date",
        expression={"$year": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expected=2024,
        msg="$year should return the calendar year for a literal date operand",
    ),
    ExpressionTestCase(
        "field_ref_simple",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$year": "$d"},
        expected=2024,
        msg="$year should accept a date from a shorthand field reference",
    ),
    ExpressionTestCase(
        "field_ref_object",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$d"}},
        expected=2024,
        msg="$year should accept a date field reference in the document form",
    ),
    ExpressionTestCase(
        "array_expression_field_ref",
        doc={"d": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": ["$d"]},
        expected=2024,
        msg="$year should unwrap a single-element array expression with a field reference",
    ),
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}},
        expression={"$year": "$a.b"},
        expected=2024,
        msg="$year should accept a date resolved from a nested field path",
    ),
    ExpressionTestCase(
        "missing_nested_field",
        doc={"a": {"x": 1}},
        expression={"$year": "$a.missing"},
        expected=None,
        msg="$year should return null when a nested field path is missing",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}]},
        expression={"$year": "$a.0.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$year should error when an array-index path resolves to an array",
    ),
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)},
                {"b": datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)},
            ]
        },
        expression={"$year": "$a.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$year should error when a path over an array of objects resolves to an array",
    ),
    ExpressionTestCase(
        "timezone_from_field",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc), "tz": "America/New_York"},
        expression={"$year": {"date": "$date", "timezone": "$tz"}},
        expected=2023,
        msg="$year should apply a timezone resolved from a field reference",
    ),
    ExpressionTestCase(
        "missing_tz_field_ref",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$year": {"date": "$date", "timezone": "$tz"}},
        expected=None,
        msg="$year should return null when the timezone field reference is missing",
    ),
    ExpressionTestCase(
        "expression_as_input",
        expression={"$year": {"$dateFromString": {"dateString": "2024-06-15T00:00:00Z"}}},
        expected=2024,
        msg="$year should accept the result of a nested expression as the date",
    ),
]

# Property [Return Type]: $year returns a value of BSON type int.
YEAR_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$type": {"$year": "$date"}},
        expected="int",
        msg="$year should return an int",
    ),
]

YEAR_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    YEAR_ARGUMENT_TESTS + YEAR_FIELD_PATH_TESTS + YEAR_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(YEAR_EXPRESSION_TESTS))
def test_year_expressions(collection, test_case: ExpressionTestCase):
    """Test $year argument forms, field paths, expression input, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
