"""Tests for $millisecond argument forms, field-path resolution, expression input, and type."""

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

# Property [Literal Input]: an inline literal date computes the correct millisecond.
MILLISECOND_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_date",
        expression={"$millisecond": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
        expected=500,
        msg="$millisecond should return the millisecond for a literal date operand",
    ),
]

# Property [Argument Forms]: the document form requires exactly a date field, and the
# operand-array form accepts only a single element.
MILLISECOND_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_date",
        expression={"$millisecond": {"timezone": "UTC"}},
        error_code=ISO_DATE_MISSING_DATE_ERROR,
        msg="$millisecond should error when the document form omits the date field",
    ),
    ExpressionTestCase(
        "extra_field",
        expression={
            "$millisecond": {
                "date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc),
                "extra": 1,
            }
        },
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$millisecond should error for an unknown field in the document form",
    ),
    ExpressionTestCase(
        "empty_array",
        expression={"$millisecond": []},
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$millisecond should error for an empty operand array",
    ),
    ExpressionTestCase(
        "two_element_array",
        expression={
            "$millisecond": [
                datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc),
                datetime(2024, 6, 16, 12, 0, 0, 250000, tzinfo=timezone.utc),
            ]
        },
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$millisecond should error for a two-element operand array",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$millisecond": [datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)]},
        expected=500,
        msg="$millisecond should accept a single-element operand array as the date",
    ),
    ExpressionTestCase(
        "single_element_array_field_ref",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
        expression={"$millisecond": ["$date"]},
        expected=500,
        msg="$millisecond should accept a single-element operand array holding a field reference",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
        expression={"$millisecond": {"a": "$date"}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$millisecond should treat an object with an unknown key as an invalid document form",
    ),
]

# Property [Field-Path Resolution]: the operator accepts a resolved field reference; a path
# that resolves to an array (array-index or array-of-objects) feeds the type contract and errors.
MILLISECOND_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)}},
        expression={"$millisecond": "$a.b"},
        expected=500,
        msg="$millisecond should accept a date resolved from a nested field path",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)}]},
        expression={"$millisecond": "$a.0.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should error when an array-index path resolves to an array",
    ),
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
                {"b": datetime(2024, 6, 15, 12, 0, 0, 250000, tzinfo=timezone.utc)},
            ]
        },
        expression={"$millisecond": "$a.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$millisecond should error when a path over an array of objects resolves to an array",
    ),
    ExpressionTestCase(
        "timezone_from_field",
        doc={
            "date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc),
            "tz": "America/New_York",
        },
        expression={"$millisecond": {"date": "$date", "timezone": "$tz"}},
        expected=500,
        msg="$millisecond should apply a timezone resolved from a field reference",
    ),
    ExpressionTestCase(
        "missing_tz_field_ref",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
        expression={"$millisecond": {"date": "$date", "timezone": "$tz"}},
        expected=None,
        msg="$millisecond should return null when the timezone field reference is missing",
    ),
    ExpressionTestCase(
        "expression_as_input",
        expression={
            "$millisecond": {"$dateFromString": {"dateString": "2024-06-15T12:00:00.500Z"}}
        },
        expected=500,
        msg="$millisecond should accept the result of a nested expression as the date",
    ),
]

# Property [Return Type]: $millisecond returns a value of BSON type int.
MILLISECOND_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, 500000, tzinfo=timezone.utc)},
        expression={"$type": {"$millisecond": "$date"}},
        expected="int",
        msg="$millisecond should return an int",
    ),
]

MILLISECOND_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    MILLISECOND_LITERAL_TESTS
    + MILLISECOND_ARGUMENT_TESTS
    + MILLISECOND_FIELD_PATH_TESTS
    + MILLISECOND_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MILLISECOND_EXPRESSION_TESTS))
def test_millisecond_expressions(collection, test_case: ExpressionTestCase):
    """Test $millisecond argument forms, field-path resolution, and expression input."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
