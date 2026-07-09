"""$dateDiff field-reference and expression operands, array-resolving paths, and return type."""

from datetime import datetime, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import INVALID_DATE_VALUE_ERROR
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Field Reference Operands]: the startDate, endDate, unit, and timezone operands
# resolve from field references, including a nested path, and a missing timezone reference
# returns null.
DATEDIFF_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_refs",
        doc={
            "s": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "e": datetime(2024, 1, 6, tzinfo=timezone.utc),
        },
        expression={"$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day"}},
        expected=Int64(5),
        msg="$dateDiff should resolve startDate and endDate from field references",
    ),
    ExpressionTestCase(
        "field_ref_unit",
        doc={"u": "day"},
        expression={
            "$dateDiff": {
                "startDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "endDate": datetime(2024, 1, 6, tzinfo=timezone.utc),
                "unit": "$u",
            }
        },
        expected=Int64(5),
        msg="$dateDiff should resolve the unit from a field reference",
    ),
    ExpressionTestCase(
        "nested_field_path",
        doc={
            "a": {
                "s": datetime(2021, 1, 1, tzinfo=timezone.utc),
                "e": datetime(2021, 1, 2, tzinfo=timezone.utc),
            }
        },
        expression={"$dateDiff": {"startDate": "$a.s", "endDate": "$a.e", "unit": "day"}},
        expected=Int64(1),
        msg="$dateDiff should resolve date operands from a nested field path",
    ),
    ExpressionTestCase(
        "timezone_field_ref",
        doc={
            "s": datetime(2021, 12, 31, 23, 0, 0, tzinfo=timezone.utc),
            "e": datetime(2022, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            "tz": "+02:00",
        },
        expression={
            "$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "year", "timezone": "$tz"}
        },
        expected=INT64_ZERO,
        msg="$dateDiff should resolve the timezone from a field reference",
    ),
    ExpressionTestCase(
        "missing_timezone_field_ref",
        doc={
            "s": datetime(2021, 1, 1, tzinfo=timezone.utc),
            "e": datetime(2021, 1, 2, tzinfo=timezone.utc),
        },
        expression={
            "$dateDiff": {"startDate": "$s", "endDate": "$e", "unit": "day", "timezone": "$tz"}
        },
        expected=None,
        msg="$dateDiff should return null for a missing timezone field reference",
    ),
]

# Property [Array-Resolving Path]: a field path that resolves to an array is delivered to the
# operator, which rejects it under its date type contract.
DATEDIFF_ARRAY_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "composite_array_path",
        doc={
            "a": [
                {"b": datetime(2021, 1, 1, tzinfo=timezone.utc)},
                {"b": datetime(2021, 6, 1, tzinfo=timezone.utc)},
            ]
        },
        expression={
            "$dateDiff": {
                "startDate": "$a.b",
                "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateDiff should reject a composite array field path as startDate",
    ),
    ExpressionTestCase(
        "single_element_array_path",
        doc={"a": [{"b": datetime(2021, 6, 15, tzinfo=timezone.utc)}]},
        expression={
            "$dateDiff": {
                "startDate": "$a.b",
                "endDate": datetime(2021, 6, 16, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateDiff should reject a single-element array field path as startDate",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": datetime(2021, 1, 1, tzinfo=timezone.utc)}]},
        expression={
            "$dateDiff": {
                "startDate": "$a.0.b",
                "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                "unit": "day",
            }
        },
        error_code=INVALID_DATE_VALUE_ERROR,
        msg="$dateDiff should reject an array-index field path resolving to an array as startDate",
    ),
]

DATEDIFF_EXPRESSION_TESTS = DATEDIFF_FIELD_REF_TESTS + DATEDIFF_ARRAY_PATH_TESTS


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_EXPRESSION_TESTS))
def test_dateDiff_expressions(collection, test_case: ExpressionTestCase):
    """Test $dateDiff field-reference and expression operands."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )


# Property [Return Type]: $dateDiff returns a long regardless of the unit.
DATEDIFF_RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_day",
        expression={
            "$type": {
                "$dateDiff": {
                    "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                    "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                    "unit": "day",
                }
            }
        },
        expected="long",
        msg="$dateDiff should return a long for a day difference",
    ),
    ExpressionTestCase(
        "return_type_millisecond",
        expression={
            "$type": {
                "$dateDiff": {
                    "startDate": datetime(2021, 1, 1, tzinfo=timezone.utc),
                    "endDate": datetime(2021, 1, 2, tzinfo=timezone.utc),
                    "unit": "millisecond",
                }
            }
        },
        expected="long",
        msg="$dateDiff should return a long for a millisecond difference",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(DATEDIFF_RETURN_TYPE_TESTS))
def test_dateDiff_return_type(collection, test_case: ExpressionTestCase):
    """Test $dateDiff return type."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
