"""Tests for $last accumulator: arity rejection and expression error propagation."""

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
LAST_SYNTAX_VALIDATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "syntax_bare_dollar",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": "$"}}}],
        error_code=INVALID_DOLLAR_FIELD_PATH,
        msg="$last should reject '$' as an invalid FieldPath",
    ),
]

# Property [Arity Rejection]: $last rejects array syntax in accumulator
# context ($group, $bucket, $bucketAuto), and multi-key expression objects
# produce an expression parsing error.
LAST_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_group",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject empty array in $group",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": [1]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_group",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": [1, 2, 3]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject multi-element array in $group",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$last": {"$add": [1, 2], "$multiply": [3, 4]}},
                }
            }
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$last should reject multi-key expression object",
    ),
    AccumulatorTestCase(
        "arity_empty_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$last": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject empty array in $bucket",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$last": [1, 2, 3]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject multi-element array in $bucket",
    ),
    AccumulatorTestCase(
        "arity_empty_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$last": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject empty array in $bucketAuto",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$last": [1, 2, 3]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$last should reject multi-element array in $bucketAuto",
    ),
]

# Property [Expression Error Propagation]: when the accumulator expression
# errors for any document in the group, the error propagates to the caller.
LAST_EXPRESSION_ERROR_PROPAGATION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_to_int_invalid_string",
        docs=[{"v": "abc"}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": {"$toInt": "$v"}}}}],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$last should propagate $toInt conversion error from expression",
    ),
    AccumulatorTestCase(
        "expr_error_divide_by_zero",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$last": {"$divide": ["$v", 0]}}}}],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$last should propagate $divide by zero error",
    ),
]

LAST_ERROR_TESTS = (
    LAST_SYNTAX_VALIDATION_TESTS + LAST_ARITY_ERROR_TESTS + LAST_EXPRESSION_ERROR_PROPAGATION_TESTS
)


def _run(collection, test_case: AccumulatorTestCase):
    """Insert docs and execute the pipeline."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )


@pytest.mark.parametrize("test_case", pytest_params(LAST_ERROR_TESTS))
def test_last_errors(collection, test_case: AccumulatorTestCase):
    """Test $last error cases."""
    result = _run(collection, test_case)
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
