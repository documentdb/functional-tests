"""
Tests for $lt null and missing field handling.

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
        "null_null", expression={"$lt": [None, None]}, expected=False, msg="null not < null"
    ),
    ExpressionTestCase("null_int", expression={"$lt": [None, 1]}, expected=True, msg="null < int"),
    ExpressionTestCase(
        "int_null", expression={"$lt": [1, None]}, expected=False, msg="int not < null"
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_LITERAL_TESTS))
def test_lt_null_missing_literal(collection, test):
    """Test $lt null literal comparisons."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_pos1",
        expression={"$lt": ["$a", "$b"]},
        doc={"b": 5},
        expected=True,
        msg="missing in position 1 → null < 5",
    ),
    ExpressionTestCase(
        "missing_pos2",
        expression={"$lt": ["$a", "$b"]},
        doc={"a": 5},
        expected=False,
        msg="missing in position 2 → 5 not < null",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$lt": ["$a", "$b"]},
        doc={},
        expected=False,
        msg="both missing → null not < null",
    ),
]


NULL_MISSING_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_field_vs_missing",
        expression={"$lt": ["$a", "$nonexistent"]},
        doc={"a": None},
        expected=False,
        msg="null field not < missing",
    ),
    ExpressionTestCase(
        "missing_vs_null_literal",
        expression={"$lt": ["$nonexistent", None]},
        doc={},
        expected=True,
        msg="missing field < null literal in expression context",
    ),
    ExpressionTestCase(
        "null_vs_null_fields",
        expression={"$lt": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=False,
        msg="null field not < null field",
    ),
]


ALL_INSERT_TESTS = MISSING_FIELD_TESTS + NULL_MISSING_EQUIV_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_INSERT_TESTS))
def test_lt_null_missing_insert(collection, test):
    """Test $lt null and missing field handling with documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
