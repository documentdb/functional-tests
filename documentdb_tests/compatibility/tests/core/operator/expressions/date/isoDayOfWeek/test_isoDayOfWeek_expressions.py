"""Tests for $isoDayOfWeek argument forms, field-path resolution, and expression input."""

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
from documentdb_tests.framework.error_codes import (
    ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
    ISO_DATE_MISSING_DATE_ERROR,
    ISO_DATE_UNKNOWN_FIELD_ERROR,
    TYPE_MISMATCH_DATE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Forms]: the document form requires exactly a date field, and the
# operand-array form accepts only a single element.
ISODAYOFWEEK_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_date",
        expression={"$isoDayOfWeek": {"timezone": "UTC"}},
        error_code=ISO_DATE_MISSING_DATE_ERROR,
        msg="$isoDayOfWeek should error when the document form omits the date field",
    ),
    ExpressionTestCase(
        "extra_field",
        expression={
            "$isoDayOfWeek": {
                "date": datetime(2024, 1, 15, tzinfo=timezone.utc),
                "extra": 1,
            }
        },
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$isoDayOfWeek should error for an unknown field in the document form",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": {"a": "$date"}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$isoDayOfWeek should treat an object with an unknown key as an invalid document form",
    ),
    ExpressionTestCase(
        "invalid_array",
        expression={"$isoDayOfWeek": [1, 2]},
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$isoDayOfWeek should error for a multi-element operand array",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$isoDayOfWeek": [datetime(2024, 1, 15, tzinfo=timezone.utc)]},
        expected=1,
        msg="$isoDayOfWeek should accept a single-element operand array as the date",
    ),
    ExpressionTestCase(
        "invalid_string",
        expression={"$isoDayOfWeek": "string"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a literal string operand",
    ),
    ExpressionTestCase(
        "invalid_number",
        expression={"$isoDayOfWeek": 123},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a literal number operand",
    ),
    ExpressionTestCase(
        "invalid_boolean",
        expression={"$isoDayOfWeek": True},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should reject a literal boolean operand",
    ),
]

# Property [Input Expression Types]: the operator accepts each expression type it can receive
# as the date argument (literal, field reference in shorthand and document form, an array
# expression holding a field reference, and a nested expression); a path or array expression
# that resolves to an array feeds the type contract and errors.
ISODAYOFWEEK_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_date",
        expression={"$isoDayOfWeek": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expected=1,
        msg="$isoDayOfWeek should return the ISO day for a literal date operand",
    ),
    ExpressionTestCase(
        "field_ref_simple",
        doc={"d": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": "$d"},
        expected=1,
        msg="$isoDayOfWeek should accept a date from a shorthand field reference",
    ),
    ExpressionTestCase(
        "field_ref_object",
        doc={"d": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": {"date": "$d"}},
        expected=1,
        msg="$isoDayOfWeek should accept a date field reference in the document form",
    ),
    ExpressionTestCase(
        "array_expression_field_ref",
        doc={"d": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": ["$d"]},
        expected=1,
        msg="$isoDayOfWeek should unwrap a single-element array expression holding a field "
        "reference",
    ),
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": datetime(2024, 1, 15, tzinfo=timezone.utc)}},
        expression={"$isoDayOfWeek": "$a.b"},
        expected=1,
        msg="$isoDayOfWeek should accept a date resolved from a nested field path",
    ),
    ExpressionTestCase(
        "nested_field_document_form",
        doc={"doc": {"date": datetime(2024, 1, 15, tzinfo=timezone.utc)}},
        expression={"$isoDayOfWeek": "$doc.date"},
        expected=1,
        msg="$isoDayOfWeek should accept a date resolved from a dotted document path",
    ),
    ExpressionTestCase(
        "missing_nested_field",
        doc={"a": {"x": 1}},
        expression={"$isoDayOfWeek": "$a.missing"},
        expected=None,
        msg="$isoDayOfWeek should return null when a nested field path is missing",
    ),
    ExpressionTestCase(
        "oid_field_ref",
        doc={"oid": oid_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$oid"},
        expected=1,
        msg="$isoDayOfWeek should accept an ObjectId from a shorthand field reference",
    ),
    ExpressionTestCase(
        "oid_field_ref_object",
        doc={"oid": oid_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoDayOfWeek": {"date": "$oid"}},
        expected=1,
        msg="$isoDayOfWeek should accept an ObjectId field reference in the document form",
    ),
    ExpressionTestCase(
        "ts_field_ref",
        doc={"ts": ts_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoDayOfWeek": "$ts"},
        expected=1,
        msg="$isoDayOfWeek should accept a Timestamp from a shorthand field reference",
    ),
    ExpressionTestCase(
        "ts_field_ref_object",
        doc={"ts": ts_from_args(2024, 1, 15, 0, 0, 0)},
        expression={"$isoDayOfWeek": {"date": "$ts"}},
        expected=1,
        msg="$isoDayOfWeek should accept a Timestamp field reference in the document form",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2024, 1, 15, tzinfo=timezone.utc)}]},
        expression={"$isoDayOfWeek": "$a.0.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should error when an array-index path resolves to an array",
    ),
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 1, 15, tzinfo=timezone.utc)},
                {"b": datetime(2024, 1, 16, tzinfo=timezone.utc)},
            ]
        },
        expression={"$isoDayOfWeek": "$a.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoDayOfWeek should error when a path over an array of objects resolves to an array",
    ),
    ExpressionTestCase(
        "timezone_from_field",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc), "tz": "America/New_York"},
        expression={"$isoDayOfWeek": {"date": "$date", "timezone": "$tz"}},
        expected=7,
        msg="$isoDayOfWeek should apply a timezone resolved from a field reference",
    ),
    ExpressionTestCase(
        "missing_tz_field_ref",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoDayOfWeek": {"date": "$date", "timezone": "$tz"}},
        expected=None,
        msg="$isoDayOfWeek should return null when the timezone field reference is missing",
    ),
    ExpressionTestCase(
        "expression_as_input",
        expression={"$isoDayOfWeek": {"$dateFromString": {"dateString": "2024-01-15T00:00:00Z"}}},
        expected=1,
        msg="$isoDayOfWeek should accept the result of a nested expression as the date",
    ),
]

# Property [Return Type]: $isoDayOfWeek returns a value of BSON type int.
ISODAYOFWEEK_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$type": {"$isoDayOfWeek": "$date"}},
        expected="int",
        msg="$isoDayOfWeek should return an int",
    ),
]

ISODAYOFWEEK_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    ISODAYOFWEEK_ARGUMENT_TESTS + ISODAYOFWEEK_FIELD_PATH_TESTS + ISODAYOFWEEK_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISODAYOFWEEK_EXPRESSION_TESTS))
def test_isoDayOfWeek_expressions(collection, test_case: ExpressionTestCase):
    """Test $isoDayOfWeek argument forms, field paths, expression input, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
