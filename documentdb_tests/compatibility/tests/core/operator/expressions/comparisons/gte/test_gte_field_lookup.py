"""
Tests for $gte field lookup variations.

Covers simple, nested, and non-existent field paths.
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
        expression={"$gte": ["$a", 5]},
        doc={"a": 10},
        expected=True,
        msg="Simple field 10 >= 5",
    ),
    ExpressionTestCase(
        "simple_field_equal",
        expression={"$gte": ["$a", 10]},
        doc={"a": 10},
        expected=True,
        msg="Simple field 10 >= 10 (equal)",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$gte": ["$a", 5]},
        doc={"x": 1},
        expected=False,
        msg="Missing field not >= 5",
    ),
]

NESTED_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$gte": ["$a.b", 10]},
        doc={"a": {"b": 10}},
        expected=True,
        msg="Nested field a.b=10 >= 10 (equal)",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$gte": ["$a.b.c.d", 10]},
        doc={"a": {"b": {"c": {"d": 10}}}},
        expected=True,
        msg="Deeply nested a.b.c.d=10 >= 10 (equal)",
    ),
    ExpressionTestCase(
        "deeply_nested_self",
        expression={"$gte": ["$a.b.c.d", "$a.b.c.d"]},
        doc={"a": {"b": {"c": {"d": 10}}}},
        expected=True,
        msg="Same deeply nested field >= itself (equal)",
    ),
]

ARRAY_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_field_vs_array",
        expression={"$gte": ["$a", [1, 2]]},
        doc={"a": [1, 2, 3]},
        expected=True,
        msg="[1,2,3] >= [1,2]",
    ),
]

NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_field_vs_missing",
        expression={"$gte": ["$a", "$nonexistent"]},
        doc={"a": None},
        expected=True,
        msg="null field >= missing (null == missing → equal → true)",
    ),
    ExpressionTestCase(
        "missing_vs_null",
        expression={"$gte": ["$nonexistent", None]},
        doc={},
        expected=False,
        msg="missing field not >= null literal",
    ),
]

ALL_TESTS = SIMPLE_FIELD_TESTS + NESTED_FIELD_TESTS + ARRAY_FIELD_TESTS + NULL_MISSING_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_field_lookup(collection, test):
    """Test $gte field lookup variations."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
