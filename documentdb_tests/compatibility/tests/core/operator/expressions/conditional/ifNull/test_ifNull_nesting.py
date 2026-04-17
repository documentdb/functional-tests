"""
Tests for $ifNull nesting and composition.

Covers $ifNull nested inside $ifNull, including inner-null fallthrough,
inner-non-null passthrough, and deep (3-level) nesting.
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

NESTED_IFNULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "inner_null_outer_falls_through",
        doc={"a": None, "b": None, "c": 3},
        expression={"$ifNull": [{"$ifNull": ["$a", "$b"]}, "$c", "default"]},
        expected=3,
        msg="Inner returns null, outer falls to $c",
    ),
    ExpressionTestCase(
        "inner_non_null",
        doc={"a": None, "b": 2},
        expression={"$ifNull": [{"$ifNull": ["$a", "$b"]}, "default"]},
        expected=2,
        msg="Inner returns 2 (non-null), outer returns it",
    ),
    ExpressionTestCase(
        "deep_nesting",
        expression={"$ifNull": [{"$ifNull": [{"$ifNull": [None, None]}, None]}, "deep_default"]},
        expected="deep_default",
        msg="Should resolve through deep nesting",
    ),
]

ALL_INSERT_TESTS = [t for t in NESTED_IFNULL_TESTS if t.doc is not None]
ALL_LITERAL_TESTS = [t for t in NESTED_IFNULL_TESTS if t.doc is None]


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_ifNull_nesting_insert(collection, test):
    """Test $ifNull nesting with expressions requiring document insert."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_LITERAL_TESTS))
def test_ifNull_nesting_literal(collection, test):
    """Test $ifNull nesting with literal expressions (no document insert)."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
