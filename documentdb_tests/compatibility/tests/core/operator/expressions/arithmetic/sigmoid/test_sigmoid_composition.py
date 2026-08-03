"""
arithmetic $sigmoid tests.

Nested-expression composition and field-path lookup tests for $sigmoid.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

SIGMOID_NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_sigmoid_2",
        expression={"$sigmoid": {"$sigmoid": 0}},
        expected=pytest.approx(0.6224593312018546),
        msg="Should evaluate nested $sigmoid",
    ),
    ExpressionTestCase(
        "nested_sigmoid_3",
        expression={"$sigmoid": {"$sigmoid": {"$sigmoid": 0}}},
        expected=pytest.approx(0.6507776782147005),
        msg="Should evaluate triple-nested $sigmoid",
    ),
]


SIGMOID_FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field",
        expression={"$sigmoid": "$a.b"},
        doc={"a": {"b": 1}},
        expected=pytest.approx(0.7310585786300049),
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        "nonexistent_field",
        expression={"$sigmoid": "$a.nonexistent"},
        doc={"a": {"missing": 1}},
        expected=None,
        msg="Should return null for nonexistent field path",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$sigmoid": "$a.b.c.d"},
        doc={"a": {"b": {"c": {"d": -1}}}},
        expected=pytest.approx(0.2689414213699951),
        msg="Should resolve deeply nested field path",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SIGMOID_NESTED_TESTS))
def test_sigmoid_nested_expression(collection, test):
    """Test $sigmoid can take an expression as input"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(SIGMOID_FIELD_LOOKUP_TESTS))
def test_sigmoid_field_lookup(collection, test):
    """Test $sigmoid with field path lookups"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
