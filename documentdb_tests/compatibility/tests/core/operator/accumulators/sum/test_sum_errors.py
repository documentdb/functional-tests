"""Tests for $sum accumulator: syntax validation and error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    INVALID_DOLLAR_FIELD_PATH,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Syntax Validation]: "$" by itself is not a valid FieldPath and
# produces an error.
SUM_SYNTAX_VALIDATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "syntax_bare_dollar",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": "$"}}}],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$sum should reject '$' as an invalid FieldPath",
    ),
]

# Property [Expression Error Propagation]: when the accumulator expression
# errors for any document in the group, the error propagates to the caller.
SUM_EXPRESSION_ERROR_PROPAGATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_to_int_invalid_string",
        docs=[{"v": "abc"}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$sum should propagate $toInt conversion error from expression",
    ),
]

# Property [Expression Error Propagation - Divide by Zero]: $divide by zero
# errors propagate through $sum.
SUM_EXPRESSION_ERROR_DIVIDE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_divide_by_zero",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": {"$divide": ["$v", 0]}}}}],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$sum should propagate $divide by zero error",
    ),
]

SUM_ERROR_TESTS = (
    SUM_SYNTAX_VALIDATION_TESTS
    + SUM_EXPRESSION_ERROR_PROPAGATION_TESTS
    + SUM_EXPRESSION_ERROR_DIVIDE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_ERROR_TESTS))
def test_sum_errors(collection, test_case):
    """Test $sum error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
