"""
Tests for $gt field lookup variations.

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
        expression={"$gt": ["$a", 5]},
        doc={"a": 10},
        expected=True,
        msg="Simple field 10 > 5",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$gt": ["$a", 5]},
        doc={"x": 1},
        expected=False,
        msg="Missing field not > 5",
    ),
]

NESTED_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$gt": ["$a.b", 5]},
        doc={"a": {"b": 10}},
        expected=True,
        msg="Nested field a.b=10 > 5",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$gt": ["$a.b.c.d", 5]},
        doc={"a": {"b": {"c": {"d": 10}}}},
        expected=True,
        msg="Deeply nested a.b.c.d=10 > 5",
    ),
    ExpressionTestCase(
        "deeply_nested_self",
        expression={"$gt": ["$a.b.c.d", "$a.b.c.d"]},
        doc={"a": {"b": {"c": {"d": 10}}}},
        expected=False,
        msg="Same deeply nested field not > itself",
    ),
]

ARRAY_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_field_vs_array",
        expression={"$gt": ["$a", [1, 2]]},
        doc={"a": [1, 2, 3]},
        expected=True,
        msg="[1,2,3] > [1,2]",
    ),
]

ALL_TESTS = SIMPLE_FIELD_TESTS + NESTED_FIELD_TESTS + ARRAY_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gt_field_lookup(collection, test):
    """Test $gt field lookup variations."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
