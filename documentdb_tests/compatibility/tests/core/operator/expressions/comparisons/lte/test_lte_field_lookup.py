"""
Tests for $lte field lookup variations.

Covers simple, nested, array, non-existent, composite array, deeply nested
field paths.
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

ALL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "simple_field",
        expression={"$lte": ["$a", "$b"]},
        doc={"a": 1, "b": 2},
        expected=True,
        msg="$a(1) <= $b(2)",
    ),
    ExpressionTestCase(
        "nested_field",
        expression={"$lte": ["$a.b", "$c"]},
        doc={"a": {"b": 1}, "c": 2},
        expected=True,
        msg="$a.b(1) <= $c(2)",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$lte": ["$a.b.c.d", 10]},
        doc={"a": {"b": {"c": {"d": 5}}}},
        expected=True,
        msg="deeply nested 5 <= 10",
    ),
    ExpressionTestCase(
        "deeply_nested_self",
        expression={"$lte": ["$a.b.c.d", 5]},
        doc={"a": {"b": {"c": {"d": 5}}}},
        expected=True,
        msg="deeply nested 5 <= 5 (equal)",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$lte": ["$nonexistent", 1]},
        doc={"a": 1},
        expected=True,
        msg="missing field (null) <= 1",
    ),
    ExpressionTestCase(
        "array_field_vs_array",
        expression={"$lte": ["$a", [1, 2, 3]]},
        doc={"a": [1, 2, 3]},
        expected=True,
        msg="array <= same array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_field_lookup(collection, test):
    """Test $lte field lookup variations."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
