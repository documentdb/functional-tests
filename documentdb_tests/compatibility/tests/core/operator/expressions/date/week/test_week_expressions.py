"""Tests for $week argument forms, field-path resolution, expression input, and return type."""

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
WEEK_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "document_form_missing_date",
        expression={"$week": {"timezone": "UTC"}},
        error_code=ISO_DATE_MISSING_DATE_ERROR,
        msg="$week should error when the document form omits the date field",
    ),
    ExpressionTestCase(
        "extra_field",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "extra": 1}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$week should error for an unknown field in the document form",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"a": "$date"}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$week should treat an object with an unknown key as an invalid document form",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$week": []},
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$week should error for an empty operand array",
    ),
    ExpressionTestCase(
        "two_element_array",
        expression={
            "$week": [
                datetime(2024, 6, 15, tzinfo=timezone.utc),
                datetime(2024, 7, 15, tzinfo=timezone.utc),
            ]
        },
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$week should error for a multi-element operand array",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$week": [datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)]},
        expected=23,
        msg="$week should accept a single-element operand array as the date",
    ),
    ExpressionTestCase(
        "invalid_string",
        expression={"$week": "string"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$week should reject a literal string operand",
    ),
    ExpressionTestCase(
        "invalid_number",
        expression={"$week": 123},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$week should reject a literal number operand",
    ),
    ExpressionTestCase(
        "invalid_boolean",
        expression={"$week": True},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$week should reject a literal boolean operand",
    ),
]

# Property [Input Expression Types]: the operator accepts each expression type it can receive
# as the date argument (literal, field reference in shorthand and document form, an array
# expression holding a field reference, a nested field path, and a nested expression); a path
# that resolves to an array feeds the type contract and errors.
WEEK_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_date",
        expression={"$week": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expected=23,
        msg="$week should return the Sunday-based week for a literal date operand",
    ),
    ExpressionTestCase(
        "field_ref_simple",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": "$d"},
        expected=23,
        msg="$week should accept a date from a shorthand field reference",
    ),
    ExpressionTestCase(
        "field_ref_object",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$d"}},
        expected=23,
        msg="$week should accept a date field reference in the document form",
    ),
    ExpressionTestCase(
        "array_expression_field_ref",
        doc={"d": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": ["$d"]},
        expected=23,
        msg="$week should unwrap a single-element array expression with a field reference",
    ),
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}},
        expression={"$week": "$a.b"},
        expected=23,
        msg="$week should accept a date resolved from a nested field path",
    ),
    ExpressionTestCase(
        "missing_nested_field",
        doc={"a": {"x": 1}},
        expression={"$week": "$a.missing"},
        expected=None,
        msg="$week should return null when a nested field path is missing",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}]},
        expression={"$week": "$a.0.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$week should error when an array-index path resolves to an array",
    ),
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 1, 7, 0, 0, 0, tzinfo=timezone.utc)},
                {"b": datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)},
            ]
        },
        expression={"$week": "$a.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$week should error when a path over an array of objects resolves to an array",
    ),
    ExpressionTestCase(
        "timezone_from_field",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc), "tz": "America/New_York"},
        expression={"$week": {"date": "$date", "timezone": "$tz"}},
        expected=53,
        msg="$week should apply a timezone resolved from a field reference",
    ),
    ExpressionTestCase(
        "missing_tz_field_ref",
        doc={"date": datetime(2024, 7, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$week": {"date": "$date", "timezone": "$tz"}},
        expected=None,
        msg="$week should return null when the timezone field reference is missing",
    ),
    ExpressionTestCase(
        "expression_as_input",
        expression={"$week": {"$dateFromString": {"dateString": "2024-06-15T00:00:00Z"}}},
        expected=23,
        msg="$week should accept the result of a nested expression as the date",
    ),
]

# Property [Return Type]: $week returns a value of BSON type int.
WEEK_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$type": {"$week": "$date"}},
        expected="int",
        msg="$week should return an int",
    ),
]

WEEK_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    WEEK_ARGUMENT_TESTS + WEEK_FIELD_PATH_TESTS + WEEK_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(WEEK_EXPRESSION_TESTS))
def test_week_expressions(collection, test_case: ExpressionTestCase):
    """Test $week argument forms, field paths, expression input, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
