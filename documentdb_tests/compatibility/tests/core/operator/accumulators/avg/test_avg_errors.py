"""
Tests for $avg accumulator error handling.

Covers arity validation (rejects array syntax in $group, $bucket, $bucketAuto)
and expression error propagation ($toInt, $divide, $mod).
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity]: $avg in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
AVG_ARITY_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_multi_element_group",
        pipeline=[{"$group": {"_id": None, "result": {"$avg": ["$v", "$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject multi-element array syntax in $group",
    ),
    AccumulatorTestCase(
        "arity_empty_array_group",
        pipeline=[{"$group": {"_id": None, "result": {"$avg": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject empty array syntax in $group",
    ),
    AccumulatorTestCase(
        "arity_single_element_group",
        pipeline=[{"$group": {"_id": None, "result": {"$avg": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject single-element array syntax in $group",
    ),
    AccumulatorTestCase(
        "arity_multi_element_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$avg": ["$v", "$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject multi-element array syntax in $bucket",
    ),
    AccumulatorTestCase(
        "arity_empty_array_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$avg": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject empty array syntax in $bucket",
    ),
    AccumulatorTestCase(
        "arity_single_element_bucket",
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$v",
                    "boundaries": [0, 10],
                    "output": {"result": {"$avg": ["$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject single-element array syntax in $bucket",
    ),
    AccumulatorTestCase(
        "arity_multi_element_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$avg": ["$v", "$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject multi-element array syntax in $bucketAuto",
    ),
    AccumulatorTestCase(
        "arity_empty_array_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$avg": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject empty array syntax in $bucketAuto",
    ),
    AccumulatorTestCase(
        "arity_single_element_bucket_auto",
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$v",
                    "buckets": 1,
                    "output": {"result": {"$avg": ["$v"]}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$avg should reject single-element array syntax in $bucketAuto",
    ),
]

# Property [Expression Error Propagation]: errors from sub-expressions
# propagate through $avg without being caught or suppressed.
AVG_EXPRESSION_ERROR_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_prop_toint_non_convertible",
        docs=[{"v": "hello"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$toInt": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$avg should propagate $toInt conversion error for non-convertible value",
    ),
    AccumulatorTestCase(
        "error_prop_divide_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$divide": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$avg should propagate $divide by zero error",
    ),
    AccumulatorTestCase(
        "error_prop_mod_by_zero",
        docs=[{"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$mod": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$avg should propagate $mod by zero error",
    ),
]

AVG_ERROR_TESTS: list[AccumulatorTestCase] = AVG_ARITY_TESTS + AVG_EXPRESSION_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(AVG_ERROR_TESTS))
def test_avg_errors(collection, test_case: AccumulatorTestCase):
    """Test $avg accumulator error handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    else:
        collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
