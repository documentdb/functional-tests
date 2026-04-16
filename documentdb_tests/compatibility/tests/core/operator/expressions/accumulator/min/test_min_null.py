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
from documentdb_tests.framework.test_constants import MISSING

# Property [Null Handling]: $min treats null and missing values as absent,
# returning null only when all inputs are null or missing.
MIN_NULL_SOLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_sole",
        expression={"$min": ["$a"]},
        doc={"a": None},
        expected=None,
        msg="$min should return null when sole operand is null",
    ),
    ExpressionTestCase(
        "null_sole_unwrapped",
        expression={"$min": "$a"},
        doc={"a": None},
        expected=None,
        msg="$min should return null when unwrapped form references a null field",
    ),
    ExpressionTestCase(
        "missing_sole",
        expression={"$min": [MISSING]},
        expected=None,
        msg="$min should return null when sole operand is a missing field",
    ),
    ExpressionTestCase(
        "missing_sole_unwrapped",
        expression={"$min": MISSING},
        doc={},
        expected=None,
        msg="$min should return null when unwrapped form references a missing field",
    ),
]

# Property [Null Exclusion]: when null or missing values appear alongside
# non-null values in a list, they are excluded and the minimum of the
# non-null values is returned.
MIN_NULL_EXCLUSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first_with_values",
        expression={"$min": ["$a", "$b", "$c"]},
        doc={"a": None, "b": 5, "c": 3},
        expected=3,
        msg="$min should exclude null and return min of remaining values",
    ),
    ExpressionTestCase(
        "null_last_with_values",
        expression={"$min": ["$a", "$b", "$c"]},
        doc={"a": 5, "b": 3, "c": None},
        expected=3,
        msg="$min should exclude trailing null and return min of remaining values",
    ),
    ExpressionTestCase(
        "null_middle_with_values",
        expression={"$min": ["$a", "$b", "$c"]},
        doc={"a": 3, "b": None, "c": 5},
        expected=3,
        msg="$min should exclude middle null and return min of remaining values",
    ),
    ExpressionTestCase(
        "missing_first_with_values",
        expression={"$min": [MISSING, "$b", "$c"]},
        doc={"b": 5, "c": 3},
        expected=3,
        msg="$min should exclude missing and return min of remaining values",
    ),
    ExpressionTestCase(
        "missing_last_with_values",
        expression={"$min": ["$a", "$b", MISSING]},
        doc={"a": 5, "b": 3},
        expected=3,
        msg="$min should exclude trailing missing and return min of remaining values",
    ),
    ExpressionTestCase(
        "missing_middle_with_values",
        expression={"$min": ["$a", MISSING, "$b"]},
        doc={"a": 3, "b": 5},
        expected=3,
        msg="$min should exclude middle missing and return min of remaining values",
    ),
]

# Property [All Null or Missing]: when all operands are null, missing, or a
# mix of both, the result is null.
MIN_ALL_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_null_two",
        expression={"$min": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=None,
        msg="$min should return null when all operands are null",
    ),
    ExpressionTestCase(
        "all_missing_two",
        expression={"$min": [MISSING, MISSING]},
        expected=None,
        msg="$min should return null when all operands are missing",
    ),
    ExpressionTestCase(
        "null_and_missing",
        expression={"$min": ["$a", MISSING]},
        doc={"a": None},
        expected=None,
        msg="$min should return null for cross-combination of null and missing",
    ),
    ExpressionTestCase(
        "missing_and_null",
        expression={"$min": [MISSING, "$a"]},
        doc={"a": None},
        expected=None,
        msg="$min should return null for cross-combination of missing and null",
    ),
]

MIN_NULL_TESTS = MIN_NULL_SOLE_TESTS + MIN_NULL_EXCLUSION_TESTS + MIN_ALL_NULL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_NULL_TESTS))
def test_min_null_cases(collection, test_case: ExpressionTestCase):
    """Test $min null handling cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
