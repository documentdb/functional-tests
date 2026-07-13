"""Tests for $isoWeekYear argument forms, field-path resolution, and expression input."""

from datetime import datetime, timezone

import pytest
from bson import Int64

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

# Property [Argument Forms]: the operand may be a date, a single-element operand array, or a
# document with exactly a date field; other operand shapes and scalar non-date operands are
# rejected.
ISOWEEKYEAR_ARGUMENT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "document_form_missing_date",
        expression={"$isoWeekYear": {"timezone": "UTC"}},
        error_code=ISO_DATE_MISSING_DATE_ERROR,
        msg="$isoWeekYear should error when the document form omits the date field",
    ),
    ExpressionTestCase(
        "extra_field",
        doc={"date": datetime(2024, 1, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "extra": 1}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$isoWeekYear should error for an unknown field in the document form",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"a": "$date"}},
        error_code=ISO_DATE_UNKNOWN_FIELD_ERROR,
        msg="$isoWeekYear should treat an object with an unknown key as an invalid document form",
    ),
    ExpressionTestCase(
        "invalid_array",
        expression={"$isoWeekYear": [1, 2]},
        error_code=ISO_DATE_INVALID_ARRAY_INPUT_ERROR,
        msg="$isoWeekYear should error for a multi-element operand array",
    ),
    ExpressionTestCase(
        "single_element_array",
        expression={"$isoWeekYear": [datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)]},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a single-element operand array as the date",
    ),
    ExpressionTestCase(
        "invalid_string",
        expression={"$isoWeekYear": "string"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoWeekYear should reject a literal string operand",
    ),
    ExpressionTestCase(
        "invalid_number",
        expression={"$isoWeekYear": 123},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoWeekYear should reject a literal number operand",
    ),
    ExpressionTestCase(
        "invalid_boolean",
        expression={"$isoWeekYear": True},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoWeekYear should reject a literal boolean operand",
    ),
]

# Property [Input Expression Types]: the operator accepts each expression type it can receive
# as the date argument (literal, field reference in shorthand and document form, an array
# expression holding a field reference, and a nested expression); a path or array expression
# that resolves to an array feeds the type contract and errors.
ISOWEEKYEAR_FIELD_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_date",
        expression={"$isoWeekYear": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expected=Int64(2024),
        msg="$isoWeekYear should return the ISO week-numbering year for a literal date operand",
    ),
    ExpressionTestCase(
        "field_ref_simple",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": "$d"},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a date from a shorthand field reference",
    ),
    ExpressionTestCase(
        "field_ref_object",
        doc={"d": datetime(2024, 6, 15, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$d"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a date field reference in the document form",
    ),
    ExpressionTestCase(
        "array_expression_field_ref",
        doc={"d": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": ["$d"]},
        expected=Int64(2024),
        msg="$isoWeekYear should unwrap a single-element array expression with a field reference",
    ),
    ExpressionTestCase(
        "nested_field_path",
        doc={"a": {"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}},
        expression={"$isoWeekYear": "$a.b"},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a date resolved from a nested field path",
    ),
    ExpressionTestCase(
        "nested_field_path_doc",
        doc={"doc": {"date": datetime(2024, 6, 15, tzinfo=timezone.utc)}},
        expression={"$isoWeekYear": "$doc.date"},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a date resolved from a nested document field path",
    ),
    ExpressionTestCase(
        "missing_nested_field",
        doc={"doc": {"x": 1}},
        expression={"$isoWeekYear": "$doc.missing"},
        expected=None,
        msg="$isoWeekYear should return null when a nested field path is missing",
    ),
    ExpressionTestCase(
        "oid_field_ref",
        doc={"oid": oid_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$isoWeekYear": "$oid"},
        expected=Int64(2024),
        msg="$isoWeekYear should accept an ObjectId from a shorthand field reference",
    ),
    ExpressionTestCase(
        "oid_field_ref_object",
        doc={"oid": oid_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$isoWeekYear": {"date": "$oid"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept an ObjectId field reference in the document form",
    ),
    ExpressionTestCase(
        "ts_field_ref",
        doc={"ts": ts_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$isoWeekYear": "$ts"},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a Timestamp from a shorthand field reference",
    ),
    ExpressionTestCase(
        "ts_field_ref_object",
        doc={"ts": ts_from_args(2024, 6, 15, 0, 0, 0)},
        expression={"$isoWeekYear": {"date": "$ts"}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept a Timestamp field reference in the document form",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)}]},
        expression={"$isoWeekYear": "$a.0.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoWeekYear should error when an array-index path resolves to an array",
    ),
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
                {"b": datetime(2024, 7, 15, tzinfo=timezone.utc)},
            ]
        },
        expression={"$isoWeekYear": "$a.b"},
        error_code=TYPE_MISMATCH_DATE_ERROR,
        msg="$isoWeekYear should error when a path over an array of objects resolves to an array",
    ),
    ExpressionTestCase(
        "timezone_from_field",
        doc={"date": datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc), "tz": "America/New_York"},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "$tz"}},
        expected=Int64(2023),
        msg="$isoWeekYear should apply a timezone resolved from a field reference",
    ),
    ExpressionTestCase(
        "missing_tz_field_ref",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$isoWeekYear": {"date": "$date", "timezone": "$tz"}},
        expected=None,
        msg="$isoWeekYear should return null when the timezone field reference is missing",
    ),
    ExpressionTestCase(
        "expression_as_input",
        expression={"$isoWeekYear": {"$dateFromString": {"dateString": "2024-06-15T00:00:00Z"}}},
        expected=Int64(2024),
        msg="$isoWeekYear should accept the result of a nested expression as the date",
    ),
]

# Property [Return Type]: $isoWeekYear returns a value of BSON type long.
ISOWEEKYEAR_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type",
        doc={"date": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)},
        expression={"$type": {"$isoWeekYear": "$date"}},
        expected="long",
        msg="$isoWeekYear should return a long",
    ),
]

ISOWEEKYEAR_EXPRESSION_TESTS: list[ExpressionTestCase] = (
    ISOWEEKYEAR_ARGUMENT_TESTS + ISOWEEKYEAR_FIELD_PATH_TESTS + ISOWEEKYEAR_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ISOWEEKYEAR_EXPRESSION_TESTS))
def test_isoWeekYear_expressions(collection, test_case: ExpressionTestCase):
    """Test $isoWeekYear argument forms, field paths, expression input, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
