"""
Tests for $literal with special field names in objects.

Verifies $literal accepts objects with field names containing dots, dollar signs,
and empty strings — at both top-level and nested levels.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# All special field name tests (top-level and nested)
# ---------------------------------------------------------------------------
SPECIAL_FIELD_NAME_TESTS: list[ExpressionTestCase] = [
    # Top-level
    ExpressionTestCase(
        "dollar_prefix",
        expression={"$literal": {"$field": 1}},
        expected={"$field": 1},
        msg="Should accept field starting with $",
    ),
    ExpressionTestCase(
        "dot_prefix",
        expression={"$literal": {".field": 1}},
        expected={".field": 1},
        msg="Should accept field starting with .",
    ),
    ExpressionTestCase(
        "dot_suffix",
        expression={"$literal": {"field.": 1}},
        expected={"field.": 1},
        msg="Should accept field ending with .",
    ),
    ExpressionTestCase(
        "consecutive_dots",
        expression={"$literal": {"a..b": 1}},
        expected={"a..b": 1},
        msg="Should accept field with consecutive dots",
    ),
    ExpressionTestCase(
        "empty_field",
        expression={"$literal": {"": 1}},
        expected={"": 1},
        msg="Should accept empty field name",
    ),
    ExpressionTestCase(
        "dollar_dot",
        expression={"$literal": {"$a.b": 1}},
        expected={"$a.b": 1},
        msg="Should accept field starting with $ containing dot",
    ),
    ExpressionTestCase(
        "single_dot",
        expression={"$literal": {"a.b": 1}},
        expected={"a.b": 1},
        msg="Should accept field with single dot",
    ),
    ExpressionTestCase(
        "multiple_dots",
        expression={"$literal": {"a.b.c": 1}},
        expected={"a.b.c": 1},
        msg="Should accept field with multiple dots",
    ),
    # Nested
    ExpressionTestCase(
        "nested_dollar_prefix",
        expression={"$literal": {"outer": {"$field": 1}}},
        expected={"outer": {"$field": 1}},
        msg="Should accept nested field starting with $",
    ),
    ExpressionTestCase(
        "nested_dot_prefix",
        expression={"$literal": {"outer": {".field": 1}}},
        expected={"outer": {".field": 1}},
        msg="Should accept nested field starting with .",
    ),
    ExpressionTestCase(
        "nested_dot_suffix",
        expression={"$literal": {"outer": {"field.": 1}}},
        expected={"outer": {"field.": 1}},
        msg="Should accept nested field ending with .",
    ),
    ExpressionTestCase(
        "nested_consecutive_dots",
        expression={"$literal": {"outer": {"a..b": 1}}},
        expected={"outer": {"a..b": 1}},
        msg="Should accept nested field with consecutive dots",
    ),
    ExpressionTestCase(
        "nested_empty_field",
        expression={"$literal": {"outer": {"": 1}}},
        expected={"outer": {"": 1}},
        msg="Should accept nested empty field name",
    ),
    ExpressionTestCase(
        "nested_single_dot",
        expression={"$literal": {"outer": {"a.b": 1}}},
        expected={"outer": {"a.b": 1}},
        msg="Should accept nested field with single dot",
    ),
    ExpressionTestCase(
        "nested_multiple_dots",
        expression={"$literal": {"outer": {"a.b.c": 1}}},
        expected={"outer": {"a.b.c": 1}},
        msg="Should accept nested field with multiple dots",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPECIAL_FIELD_NAME_TESTS))
def test_literal_special_field_names(collection, test):
    """Test $literal accepts objects with special field names."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
