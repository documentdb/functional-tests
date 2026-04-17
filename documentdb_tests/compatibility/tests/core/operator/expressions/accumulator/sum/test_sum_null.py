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
from documentdb_tests.framework.test_constants import (
    MISSING,
)

# Property [Null Handling]: $sum treats null and missing values as zero,
# returning 0 when all inputs are null or missing.
SUM_NULL_SOLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_sole",
        expression={"$sum": "$a"},
        doc={"a": None},
        expected=0,
        msg="$sum should return 0 when sole operand is null",
    ),
    ExpressionTestCase(
        "missing_sole",
        expression={"$sum": MISSING},
        expected=0,
        msg="$sum should return 0 when sole operand is a missing field",
    ),
]

# Property [Null and Missing - Exclusion]: null and missing values among numeric operands are
# ignored.
SUM_NULL_EXCLUSION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "null_first_with_values",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": None, "b": 1, "c": 2},
        expected=3,
        msg="$sum should ignore leading null and sum remaining values",
    ),
    ExpressionTestCase(
        "missing_first_with_values",
        expression={"$sum": [MISSING, "$a", "$b"]},
        doc={"a": 5, "b": 3},
        expected=8,
        msg="$sum should ignore leading missing and sum remaining values",
    ),
    ExpressionTestCase(
        "null_last_with_values",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": 1, "b": 2, "c": None},
        expected=3,
        msg="$sum should ignore trailing null and sum remaining values",
    ),
    ExpressionTestCase(
        "missing_last_with_values",
        expression={"$sum": ["$a", "$b", MISSING]},
        doc={"a": 5, "b": 3},
        expected=8,
        msg="$sum should ignore trailing missing and sum remaining values",
    ),
    ExpressionTestCase(
        "null_middle_with_values",
        expression={"$sum": ["$a", "$b", "$c"]},
        doc={"a": 1, "b": None, "c": 2},
        expected=3,
        msg="$sum should ignore middle null and sum remaining values",
    ),
    ExpressionTestCase(
        "missing_middle_with_values",
        expression={"$sum": ["$a", MISSING, "$b"]},
        doc={"a": 5, "b": 3},
        expected=8,
        msg="$sum should ignore middle missing and sum remaining values",
    ),
]

# Property [Null and Missing - All]: when every operand is null or missing, the result is int32 0.
SUM_ALL_NULL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_null_two",
        expression={"$sum": ["$a", "$b"]},
        doc={"a": None, "b": None},
        expected=0,
        msg="$sum should return 0 when all operands are null",
    ),
    ExpressionTestCase(
        "all_missing_two",
        expression={"$sum": [MISSING, MISSING]},
        expected=0,
        msg="$sum should return 0 when all operands are missing",
    ),
    ExpressionTestCase(
        "null_and_missing",
        expression={"$sum": ["$a", MISSING]},
        doc={"a": None},
        expected=0,
        msg="$sum should return 0 for cross-combination of null and missing",
    ),
    ExpressionTestCase(
        "missing_and_null",
        expression={"$sum": [MISSING, "$a"]},
        doc={"a": None},
        expected=0,
        msg="$sum should return 0 for cross-combination of missing and null",
    ),
]

SUM_NULL_TESTS = SUM_NULL_SOLE_TESTS + SUM_NULL_EXCLUSION_TESTS + SUM_ALL_NULL_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUM_NULL_TESTS))
def test_sum_null(collection, test_case: ExpressionTestCase):
    """Test $sum null and missing handling."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc or {})
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
