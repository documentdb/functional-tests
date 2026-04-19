"""
Tests for $cmp field lookup and array index paths.

Covers array vs scalar in BSON order and deep nested path resolution.
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
        "array_vs_scalar",
        expression={"$cmp": ["$a", "$b"]},
        doc={"a": [1, 2, 3], "b": 5},
        expected=1,
        msg="Array > number in BSON order",
    ),
    ExpressionTestCase(
        "array_element_by_element",
        expression={"$cmp": ["$a", "$b"]},
        doc={"a": [1, 2, 3], "b": [1, 2, 4]},
        expected=-1,
        msg="[1,2,3] < [1,2,4] element-by-element",
    ),
    ExpressionTestCase(
        "deep_nested_path",
        expression={"$cmp": ["$a.b.c.d", 1]},
        doc={"a": {"b": {"c": {"d": 1}}}},
        expected=0,
        msg="Deep nested path $a.b.c.d resolves to 1",
    ),
    ExpressionTestCase(
        "deep_nested_missing",
        expression={"$cmp": ["$a.b.c.d", 1]},
        doc={"a": {"x": 1}},
        expected=-1,
        msg="Missing intermediate field in deep path treated as null",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cmp_field_lookup(collection, test):
    """Test $cmp field lookup and array index paths."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
