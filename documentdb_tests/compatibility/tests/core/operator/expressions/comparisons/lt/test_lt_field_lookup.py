"""
Tests for $lt field lookup variations.

Covers simple, nested, array, non-existent, composite array, array index,
deeply nested paths, and field resolving to array vs scalar.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

SIMPLE_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "simple_field",
        expression={"$lt": ["$a", 10]},
        doc={"a": 5},
        expected=True,
        msg="Simple field 5 < 10",
    ),
    ExpressionTestCase(
        "simple_field_equal",
        expression={"$lt": ["$a", 5]},
        doc={"a": 5},
        expected=False,
        msg="Simple field 5 not < 5",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$lt": ["$a", 5]},
        doc={"x": 1},
        expected=True,
        msg="Missing field (null) < 5",
    ),
]

NESTED_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$lt": ["$a.b", 10]},
        doc={"a": {"b": 5}},
        expected=True,
        msg="Nested field a.b=5 < 10",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$lt": ["$a.b.c.d", 10]},
        doc={"a": {"b": {"c": {"d": 5}}}},
        expected=True,
        msg="Deeply nested a.b.c.d=5 < 10",
    ),
    ExpressionTestCase(
        "deeply_nested_equal",
        expression={"$lt": ["$a.b.c.d", 5]},
        doc={"a": {"b": {"c": {"d": 5}}}},
        expected=False,
        msg="Deeply nested 5 not < 5 (equal)",
    ),
]

NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_vs_null",
        expression={"$lt": ["$nonexistent", None]},
        doc={},
        expected=True,
        msg="missing < null literal",
    ),
]

ARRAY_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_field_vs_array",
        expression={"$lt": ["$a", [1, 2, 3]]},
        doc={"a": [1, 2, 3]},
        expected=False,
        msg="array not < same array",
    ),
]

ALL_TESTS = SIMPLE_FIELD_TESTS + NESTED_FIELD_TESTS + NULL_MISSING_TESTS + ARRAY_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lt_field_lookup(collection, test):
    """Test $lt field lookup variations."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
