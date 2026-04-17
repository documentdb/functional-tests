"""
Tests for $ifNull evaluation order and error propagation.

Covers eager evaluation of all inputs (no short-circuiting),
multi-arg fallback behavior, and error propagation from input expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.parametrize import pytest_params

EAGER_EVALUATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "eager_eval_divide_by_zero",
        expression={"$ifNull": ["$a", {"$divide": [1, 0]}, "default"]},
        doc={"a": 1},
        error_code=BAD_VALUE_ERROR,
        msg="$ifNull evaluates all inputs; divide-by-zero errors even when first input is non-null",
    ),
    ExpressionTestCase(
        "eager_eval_array_elem_at",
        expression={"$ifNull": ["$a", {"$arrayElemAt": ["$nonexistent", 99]}, "default"]},
        doc={"a": 1},
        expected=1,
        msg="$arrayElemAt on missing field resolves to missing, first non-null returned",
    ),
    ExpressionTestCase(
        "eager_eval_size_on_null",
        expression={"$ifNull": ["$a", {"$size": "$b"}, "default"]},
        doc={"a": "exists", "b": None},
        expected="exists",
        msg="$size on null resolves to null (not an error), first non-null returned",
    ),
]

ERROR_PROPAGATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_then_divide_by_zero",
        expression={"$ifNull": ["$a", {"$divide": [1, "$b"]}, "default"]},
        doc={"a": None, "b": 0},
        error_code=BAD_VALUE_ERROR,
        msg="Divide by zero errors even in $ifNull",
    ),
    ExpressionTestCase(
        "divide_by_zero_first_input",
        expression={"$ifNull": [{"$divide": [1, 0]}, "default"]},
        doc={},
        error_code=BAD_VALUE_ERROR,
        msg="Should propagate divide-by-zero error from first input",
    ),
]

ALL_TESTS = EAGER_EVALUATION_TESTS + ERROR_PROPAGATION_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ifNull_evaluation_order(collection, test):
    """Test $ifNull eager evaluation order and error propagation."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
