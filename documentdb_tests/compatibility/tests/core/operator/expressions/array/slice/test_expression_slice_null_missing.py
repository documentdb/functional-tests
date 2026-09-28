"""
Null and missing field handling tests for $slice expression.

Tests that a null or missing array, n, or position (2-arg and 3-arg forms) propagates
to null, via both field references and literal arguments.
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
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Propagation]: a null array, null n, or null position (3-arg) yields null.
NULL_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_array_2arg",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": None, "n": 2},
        expected=None,
        msg="$slice should return null for a null array in the 2-arg form",
    ),
    ExpressionTestCase(
        "null_array_3arg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": None, "pos": 0, "n": 2},
        expected=None,
        msg="$slice should return null for a null array in the 3-arg form",
    ),
    ExpressionTestCase(
        "null_n_2arg",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": None},
        expected=None,
        msg="$slice should return null for a null n",
    ),
    ExpressionTestCase(
        "null_pos_3arg",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": None, "n": 2},
        expected=None,
        msg="$slice should return null for a null position in the 3-arg form",
    ),
]

# Property [Null Literal Propagation]: null literal arguments yield null.
NULL_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_array_2arg_literal",
        expression={"$slice": [None, 2]},
        expected=None,
        msg="$slice should return null for a literal null array in the 2-arg form",
    ),
    ExpressionTestCase(
        "null_array_3arg_literal",
        expression={"$slice": [None, 0, 2]},
        expected=None,
        msg="$slice should return null for a literal null array in the 3-arg form",
    ),
    ExpressionTestCase(
        "null_n_2arg_literal",
        expression={"$slice": [[1, 2, 3], None]},
        expected=None,
        msg="$slice should return null for a literal null n",
    ),
    ExpressionTestCase(
        "null_pos_3arg_literal",
        expression={"$slice": [[1, 2, 3], None, 2]},
        expected=None,
        msg="$slice should return null for a literal null position in the 3-arg form",
    ),
    ExpressionTestCase(
        "null_n_3arg_literal",
        expression={"$slice": [[1, 2, 3], 0, None]},
        expected=None,
        msg="$slice should return null for a literal null n in the 3-arg form",
    ),
]

# Property [Missing Field Propagation]: a missing field reference in any argument yields null.
MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_array_2arg",
        expression={"$slice": [MISSING, 2]},
        expected=None,
        msg="$slice should return null for a missing array",
    ),
    ExpressionTestCase(
        "missing_n_2arg",
        expression={"$slice": [[1, 2, 3], MISSING]},
        expected=None,
        msg="$slice should return null for a missing n in the 2-arg form",
    ),
    ExpressionTestCase(
        "missing_pos_3arg",
        expression={"$slice": [[1, 2, 3], MISSING, 2]},
        expected=None,
        msg="$slice should return null for a missing position in the 3-arg form",
    ),
    ExpressionTestCase(
        "missing_n_3arg",
        expression={"$slice": [[1, 2, 3], 0, MISSING]},
        expected=None,
        msg="$slice should return null for a missing n in the 3-arg form",
    ),
]

LITERAL_TESTS = NULL_LITERAL_TESTS + MISSING_TESTS


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_slice_literal(collection, test):
    """Test $slice null/missing with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(NULL_INSERT_TESTS))
def test_slice_insert(collection, test):
    """Test $slice null with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
