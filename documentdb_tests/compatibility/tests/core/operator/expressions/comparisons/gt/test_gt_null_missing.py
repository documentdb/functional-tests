"""
Tests for $gt null and missing field handling.

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
        "null_null", expression={"$gt": [None, None]}, expected=False, msg="null not > null"
    ),
    ExpressionTestCase(
        "null_int", expression={"$gt": [None, 1]}, expected=False, msg="null not > int"
    ),
    ExpressionTestCase("int_null", expression={"$gt": [1, None]}, expected=True, msg="int > null"),
]


@pytest.mark.parametrize("test", pytest_params(NULL_LITERAL_TESTS))
def test_gt_null_literals(collection, test):
    """Test $gt with null literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_pos1",
        expression={"$gt": ["$a", "$b"]},
        doc={"b": 5},
        expected=False,
        msg="missing in position 1 → null not > 5",
    ),
    ExpressionTestCase(
        "missing_pos2",
        expression={"$gt": ["$a", "$b"]},
        doc={"a": 5},
        expected=True,
        msg="missing in position 2 → 5 > null",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$gt": ["$a", "$b"]},
        doc={},
        expected=False,
        msg="both missing → null not > null",
    ),
]

NULL_MISSING_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_field_vs_missing",
        expression={"$gt": ["$a", "$nonexistent"]},
        doc={"a": None},
        expected=True,
        msg="null field > missing (null vs missing differs in $gt)",
    ),
    ExpressionTestCase(
        "missing_vs_null_literal",
        expression={"$gt": ["$nonexistent", None]},
        doc={},
        expected=False,
        msg="missing not > null literal",
    ),
    ExpressionTestCase(
        "null_vs_null_fields",
        expression={"$gt": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=False,
        msg="null field vs null field",
    ),
]


ALL_DOC_TESTS = MISSING_FIELD_TESTS + NULL_MISSING_EQUIV_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_DOC_TESTS))
def test_gt_null_missing(collection, test):
    """Test $gt with missing fields and null/missing equivalence."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
