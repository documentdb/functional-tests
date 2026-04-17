"""
Tests for $ifNull expression type coverage (smoke tests).

Covers literal expressions, field type inputs (array, object),
nested $ifNull as replacement, and dotted path resolution into arrays.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_null_replacement",
        expression={"$ifNull": [None, "literal_replacement"]},
        expected="literal_replacement",
        msg="Should return literal replacement for null input",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_ifNull_expressions_literal(collection, test):
    """Test $ifNull with literal expressions (no document insert)."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


FIELD_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expression_input",
        expression={"$ifNull": ["$x", "default"]},
        doc={"x": [1, 2, 3]},
        expected=[1, 2, 3],
        msg="Should return array field value",
    ),
    ExpressionTestCase(
        "object_expression_input",
        expression={"$ifNull": ["$x", "default"]},
        doc={"x": {"key": "val"}},
        expected={"key": "val"},
        msg="Should return object field value",
    ),
]

NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_as_replacement",
        expression={"$ifNull": ["$a", {"$ifNull": ["$a", "inner_default"]}]},
        doc={"a": None},
        expected="inner_default",
        msg="Should evaluate nested $ifNull as replacement",
    ),
]

DOTTED_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "dotted_path_resolves_to_array",
        expression={"$ifNull": ["$a.b.c", "default"]},
        doc={"a": [{"b": {"c": "1"}}, {"b": {"c": "2"}}]},
        expected=["1", "2"],
        msg=(
            "Dotted path into array with missing subfield returns empty array"
            " (not null), so $ifNull returns [] rather than default"
        ),
    ),
    ExpressionTestCase(
        "dotted_path_array_with_missing_subfield",
        expression={"$ifNull": ["$a.b.d", "default"]},
        doc={"a": [{"b": {"c": "1"}}, {"b": {"c": "2"}}]},
        expected=[],
        msg="Dotted path into array with missing subfield returns",
    ),
    ExpressionTestCase(
        "dotted_path_array_partial_missing",
        expression={"$ifNull": ["$a.b.c", "default"]},
        doc={"a": [{"b": {"c": "1"}}, {"b": {"d": "2"}}]},
        expected=["1"],
        msg="$ifNull with dotted path where some subdocs lack field should return partial array",
    ),
]

ALL_INSERT_TESTS = FIELD_TYPE_TESTS + NESTED_TESTS + DOTTED_PATH_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_ifNull_expressions_insert(collection, test):
    """Test $ifNull with expressions requiring document insert."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
