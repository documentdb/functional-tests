"""Tests for $sum accumulator: syntax validation, arity errors, and error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
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

# Property [Arity Errors]: array syntax is rejected in accumulator context,
# and multi-key expression objects produce an expression parsing error.
SUM_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$sum should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": [1]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$sum should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$sum should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$sum": [1, 2, 3]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$sum should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$sum": {"$add": [1, 2], "$multiply": [3, 4]}}}}
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$sum should reject multi-key expression object",
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
    + SUM_ARITY_ERROR_TESTS
    + SUM_EXPRESSION_ERROR_PROPAGATION_TESTS
    + SUM_EXPRESSION_ERROR_DIVIDE_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUM_ERROR_TESTS))
def test_accumulator_sum_errors(collection, test_case):
    """Test $sum error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
