"""Tests for $dateFromString field references, expression inputs, array paths, and return type."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import CONVERSION_FAILURE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH

# Property [Literal Input]: an inline literal dateString parses to the correct date.
DATEFROMSTRING_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_dateString",
        expression={"$dateFromString": {"dateString": "2024-06-15"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should parse the correct date from an inline literal dateString",
    ),
]

# Property [Field References]: each argument may be supplied through a field-path reference.
DATEFROMSTRING_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_dateString",
        doc={"ds": "2024-06-15"},
        expression={"$dateFromString": {"dateString": "$ds"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a dateString from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_format",
        doc={"ds": "06-15-2018", "fmt": "%m-%d-%Y"},
        expression={"$dateFromString": {"dateString": "$ds", "format": "$fmt"}},
        expected=datetime(2018, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a format from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_timezone",
        doc={"tz": "America/New_York"},
        expression={
            "$dateFromString": {"dateString": "2017-02-08T12:10:40.787", "timezone": "$tz"}
        },
        expected=datetime(2017, 2, 8, 17, 10, 40, 787000, tzinfo=timezone.utc),
        msg="$dateFromString should accept a timezone from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_onError",
        doc={"fallback": "error_value"},
        expression={"$dateFromString": {"dateString": "bad", "onError": "$fallback"}},
        expected="error_value",
        msg="$dateFromString should accept an onError value from a field reference",
    ),
    ExpressionTestCase(
        "field_ref_onNull",
        doc={"default": DATE_EPOCH},
        expression={"$dateFromString": {"dateString": None, "onNull": "$default"}},
        expected=DATE_EPOCH,
        msg="$dateFromString should accept an onNull value from a field reference",
    ),
    ExpressionTestCase(
        "nested_field",
        doc={"doc": {"ds": "2024-06-15"}},
        expression={"$dateFromString": {"dateString": "$doc.ds"}},
        expected=datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should accept a dateString from a nested-object path",
    ),
]

# Property [Missing Field References]: a reference to an absent field resolves to null.
DATEFROMSTRING_MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_dateString_onNull",
        doc={"other": 1},
        expression={"$dateFromString": {"dateString": "$nonexistent", "onNull": "default"}},
        expected="default",
        msg="$dateFromString should trigger onNull when the dateString field is absent",
    ),
    ExpressionTestCase(
        "missing_timezone_null",
        doc={"other": 1},
        expression={"$dateFromString": {"dateString": "2024-06-15", "timezone": "$tz"}},
        expected=None,
        msg="$dateFromString should return null when the timezone field is absent",
    ),
    ExpressionTestCase(
        "missing_format_null",
        doc={"other": 1},
        expression={"$dateFromString": {"dateString": "2024-06-15", "format": "$fmt"}},
        expected=None,
        msg="$dateFromString should return null when the format field is absent",
    ),
]

# Property [Expression Inputs]: an argument may be computed by a sub-expression.
DATEFROMSTRING_EXPRESSION_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "expression_as_dateString",
        expression={"$dateFromString": {"dateString": {"$concat": ["2017", "-02-08"]}}},
        expected=datetime(2017, 2, 8, 0, 0, 0, tzinfo=timezone.utc),
        msg="$dateFromString should evaluate a sub-expression for its dateString",
    ),
]

# Property [Array-Valued Path]: a dateString path resolving to an array fails conversion.
DATEFROMSTRING_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={"a": [{"b": "2024-01-01"}, {"b": "2024-06-15"}]},
        expression={"$dateFromString": {"dateString": "$a.b"}},
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$dateFromString should reject a dateString path that resolves to an array",
    ),
]

# Property [Return Type]: the parsed value is a date.
DATEFROMSTRING_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_date",
        doc={"ds": "2024-06-15"},
        expression={"$type": {"$dateFromString": {"dateString": "$ds"}}},
        expected="date",
        msg="$dateFromString should return a date",
    ),
]

DATEFROMSTRING_EXPRESSIONS_TESTS: list[ExpressionTestCase] = (
    DATEFROMSTRING_LITERAL_TESTS
    + DATEFROMSTRING_FIELD_REF_TESTS
    + DATEFROMSTRING_MISSING_FIELD_TESTS
    + DATEFROMSTRING_EXPRESSION_INPUT_TESTS
    + DATEFROMSTRING_ARRAY_PATH_TESTS
    + DATEFROMSTRING_RETURN_TYPE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(DATEFROMSTRING_EXPRESSIONS_TESTS))
def test_dateFromString_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateFromString field references, expression inputs, and return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
