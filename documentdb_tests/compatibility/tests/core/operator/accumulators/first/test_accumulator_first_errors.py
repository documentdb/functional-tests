"""Tests for $first accumulator error cases: arity rejection and expression error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity]: $first in accumulator context is a unary operator and
# rejects array syntax.
FIRST_ARITY_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": []}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$first should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": [1]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$first should reject single-element literal array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": ["$v"]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$first should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": [1, 2, 3]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$first should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$first": {"$add": [1, 2], "$multiply": [3, 4]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$first should reject multi-key expression object",
    ),
]

# Property [Expression Error Propagation]: errors raised during sub-expression
# evaluation propagate through the accumulator without being caught.
FIRST_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "expr_error_divide_by_zero",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": {"$divide": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$first should propagate $divide by zero error",
    ),
    AccumulatorTestCase(
        "expr_error_divide_by_zero_field_path",
        docs=[{"_id": 0, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": {"$divide": [1, "$v"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$first should propagate $divide by zero when divisor comes from field path",
    ),
    AccumulatorTestCase(
        "expr_error_divide_by_zero_first_doc",
        docs=[{"_id": 0, "v": 1}, {"_id": 1, "v": 0}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$first": {"$divide": [1, "$v"]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$first should propagate error even when failing doc is not the first",
    ),
    AccumulatorTestCase(
        "expr_error_to_int_invalid_string",
        docs=[{"v": "abc"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$first": {"$toInt": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$first should propagate $toInt conversion error from expression",
    ),
]

FIRST_ERROR_TESTS = FIRST_ARITY_ERROR_TESTS + FIRST_EXPRESSION_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(FIRST_ERROR_TESTS))
def test_accumulator_first_errors(collection, test_case):
    """Test $first accumulator error cases."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
