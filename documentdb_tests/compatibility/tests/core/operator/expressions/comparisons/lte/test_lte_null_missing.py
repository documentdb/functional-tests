"""
Tests for $lte null and missing field behavior.

Covers null propagation, missing field resolution, and null vs BSON types.
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

NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_lte_int", expression={"$lte": [None, 1]}, expected=True, msg="null <= number"
    ),
    ExpressionTestCase(
        "int_lte_null", expression={"$lte": [1, None]}, expected=False, msg="number not <= null"
    ),
    ExpressionTestCase(
        "null_lte_null", expression={"$lte": [None, None]}, expected=True, msg="null <= null"
    ),
]

MISSING_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field_pos1",
        expression={"$lte": ["$missing_field", 5]},
        doc={"b": 5},
        expected=True,
        msg="missing field resolves to null, null <= 5",
    ),
    ExpressionTestCase(
        "missing_field_pos2",
        expression={"$lte": [5, "$missing_field"]},
        doc={"a": 5},
        expected=False,
        msg="5 not <= null (missing)",
    ),
    ExpressionTestCase(
        "both_missing",
        expression={"$lte": ["$missing1", "$missing2"]},
        doc={"x": 1},
        expected=True,
        msg="both missing resolve to null, null <= null",
    ),
]

NULL_MISSING_EQUIV_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_field_vs_missing",
        expression={"$lte": ["$a", "$nonexistent"]},
        doc={"a": None},
        expected=False,
        msg="null field not <= missing",
    ),
    ExpressionTestCase(
        "missing_vs_null_literal",
        expression={"$lte": ["$nonexistent", None]},
        doc={},
        expected=True,
        msg="missing field <= null literal",
    ),
    ExpressionTestCase(
        "null_vs_null_fields",
        expression={"$lte": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=True,
        msg="null field <= null field (equal)",
    ),
]

ALL_TESTS: list[ExpressionTestCase] = NULL_TESTS + MISSING_FIELD_TESTS + NULL_MISSING_EQUIV_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_null_missing(collection, test):
    """Test $lte null and missing field behavior."""
    if test.doc:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
