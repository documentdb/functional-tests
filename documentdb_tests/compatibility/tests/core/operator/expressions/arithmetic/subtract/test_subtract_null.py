import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

pytestmark = pytest.mark.aggregate

# Property [Null propagation]: $subtract returns null when either operand is null or missing.
# Property [Null short-circuit]: a null/missing operand short-circuits evaluation before type
# checking.
SUBTRACT_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_subtrahend",
        doc={"a": 10, "b": None},
        expression={"$subtract": ["$a", "$b"]},
        expected=None,
        msg="$subtract should return null when the subtrahend is null",
    ),
    ExpressionTestCase(
        "null_minuend",
        doc={"a": None, "b": 5},
        expression={"$subtract": ["$a", "$b"]},
        expected=None,
        msg="$subtract should return null when the minuend is null",
    ),
    ExpressionTestCase(
        "both_null",
        doc={"a": None, "b": None},
        expression={"$subtract": ["$a", "$b"]},
        expected=None,
        msg="$subtract should return null when both operands are null",
    ),
    ExpressionTestCase(
        "missing_subtrahend",
        doc={"a": 10},
        expression={"$subtract": ["$a", MISSING]},
        expected=None,
        msg="$subtract should return null when the subtrahend field is missing",
    ),
    ExpressionTestCase(
        "missing_minuend",
        doc={"b": 5},
        expression={"$subtract": [MISSING, "$b"]},
        expected=None,
        msg="$subtract should return null when the minuend field is missing",
    ),
    ExpressionTestCase(
        "null_with_non_numeric",
        doc={"a": None},
        expression={"$subtract": ["$a", "string"]},
        expected=None,
        msg="$subtract should return null when a null minuend short-circuits type checking",
    ),
    ExpressionTestCase(
        "missing_with_non_numeric",
        doc={},
        expression={"$subtract": [MISSING, True]},
        expected=None,
        msg="$subtract should return null when a missing minuend short-circuits type checking",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_NULL_TESTS))
def test_subtract_null(collection, test_case: ExpressionTestCase):
    """Test $subtract null and missing field propagation."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
