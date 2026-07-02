"""Null and missing field tests for the $subtract operator."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null Propagation]: $subtract returns null when either operand is null or missing.
SUBTRACT_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_subtrahend",
        doc={"a": 10},
        expression={"$subtract": ["$a", None]},
        expected=None,
        msg="Should return null when subtrahend is null",
    ),
    ExpressionTestCase(
        "null_minuend",
        doc={"a": 5},
        expression={"$subtract": [None, "$a"]},
        expected=None,
        msg="Should return null when minuend is null",
    ),
    ExpressionTestCase(
        "missing_subtrahend",
        doc={"a": 10},
        expression={"$subtract": ["$a", "$missing"]},
        expected=None,
        msg="Should return null when subtrahend is missing",
    ),
    ExpressionTestCase(
        "missing_minuend",
        doc={"a": 5},
        expression={"$subtract": ["$missing", "$a"]},
        expected=None,
        msg="Should return null when minuend is missing",
    ),
    ExpressionTestCase(
        "both_null",
        doc={},
        expression={"$subtract": [None, None]},
        expected=None,
        msg="Should return null when both operands are null",
    ),
    ExpressionTestCase(
        "missing_minuend_invalid_subtrahend",
        doc={"a": True},
        expression={"$subtract": ["$missing", "$a"]},
        expected=None,
        msg="Should return null when minuend is missing (null propagates before type check)",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_NULL_TESTS))
def test_subtract_null(collection, test_case: ExpressionTestCase):
    """Test $subtract null and missing field cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
