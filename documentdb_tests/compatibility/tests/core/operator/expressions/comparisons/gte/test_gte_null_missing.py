"""
Tests for $gte null and missing field handling.

Covers null propagation, missing field behavior, and null/missing equivalence.
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

NULL_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_null", expression={"$gte": [None, None]}, expected=True, msg="null >= null"
    ),
    ExpressionTestCase(
        "null_int", expression={"$gte": [None, 1]}, expected=False, msg="null not >= int"
    ),
    ExpressionTestCase(
        "int_null", expression={"$gte": [1, None]}, expected=True, msg="int >= null"
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_LITERAL_TESTS))
def test_gte_null_literals(collection, test):
    """Test $gte with null literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_pos1",
        expression={"$gte": ["$a", "$b"]},
        doc={"b": 5},
        expected=False,
        msg="missing in position 1 → null not >= 5",
    ),
    ExpressionTestCase(
        "missing_pos2",
        expression={"$gte": ["$a", "$b"]},
        doc={"a": 5},
        expected=True,
        msg="missing in position 2 → 5 >= null",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$gte": ["$a", "$b"]},
        doc={},
        expected=True,
        msg="both missing → null >= null (equal)",
    ),
]

NULL_MISSING_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_field_vs_missing",
        expression={"$gte": ["$a", "$nonexistent"]},
        doc={"a": None},
        expected=True,
        msg="null field >= missing (null == missing → equal → true)",
    ),
    ExpressionTestCase(
        "missing_vs_null_literal",
        expression={"$gte": ["$nonexistent", None]},
        doc={},
        expected=False,
        msg="missing not >= null literal",
    ),
    ExpressionTestCase(
        "null_vs_null_fields",
        expression={"$gte": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=True,
        msg="null field >= null field (equal)",
    ),
]

ALL_TESTS = MISSING_FIELD_TESTS + NULL_MISSING_EQUIV_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_null_missing(collection, test):
    """Test $gte null and missing field handling."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
