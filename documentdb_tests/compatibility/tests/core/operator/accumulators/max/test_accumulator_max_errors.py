"""Tests for $max accumulator error cases: expression errors and arity rejection."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONVERSION_FAILURE_ERROR,
    DIVIDE_BY_ZERO_V2_ERROR,
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
    MODULO_BY_ZERO_V2_ERROR,
    MODULO_ZERO_REMAINDER_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ===========================================================================
# 1. Expression Error Propagation
# ===========================================================================

# Property [Expression Error Propagation]: errors in sub-expressions used as
# $max operand propagate as errors.

MAX_EXPRESSION_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid_group",
        docs=[{"v": "not_a_number"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$toInt": "$v"}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt sub-expression in $group",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_group",
        docs=[{"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$divide": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$max should propagate divide-by-zero error in $group",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_group",
        docs=[{"v": 10}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$mod": ["$v", 0]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$max should propagate mod-by-zero error in $group",
    ),
]

MAX_EXPRESSION_ERROR_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid_bucket",
        docs=[{"v": "not_a_number"}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": {"$toInt": "$v"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt sub-expression in $bucket",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_bucket",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": {"$divide": ["$v", 0]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=DIVIDE_BY_ZERO_V2_ERROR,
        msg="$max should propagate divide-by-zero error in $bucket",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": {"$mod": ["$v", 0]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=MODULO_BY_ZERO_V2_ERROR,
        msg="$max should propagate mod-by-zero error in $bucket",
    ),
]

# $bucketAuto wraps divide-by-zero and mod-by-zero differently
MAX_EXPRESSION_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "error_toInt_invalid_bucket_auto",
        docs=[{"v": "not_a_number"}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": {"$toInt": "$v"}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=CONVERSION_FAILURE_ERROR,
        msg="$max should propagate conversion error from $toInt in $bucketAuto",
    ),
    AccumulatorTestCase(
        "error_divide_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": {"$divide": ["$v", 0]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$max should propagate divide-by-zero error in $bucketAuto (wrapped as BAD_VALUE)",
    ),
    AccumulatorTestCase(
        "error_mod_by_zero_bucket_auto",
        docs=[{"v": 10}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": {"$mod": ["$v", 0]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=MODULO_ZERO_REMAINDER_ERROR,
        msg="$max should propagate mod-by-zero error in $bucketAuto (wrapped as 16610)",
    ),
]

MAX_EXPRESSION_ERROR_TESTS = (
    MAX_EXPRESSION_ERROR_GROUP_TESTS
    + MAX_EXPRESSION_ERROR_BUCKET_TESTS
    + MAX_EXPRESSION_ERROR_BUCKET_AUTO_TESTS
)


# ===========================================================================
# 2. Arity Rejection
# ===========================================================================

# Property [Arity]: $max in accumulator context is a unary operator and
# rejects array syntax in $group, $bucket, and $bucketAuto.
MAX_ARITY_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": []}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": [1]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": ["$v"]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": [1, 2, 3]}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($group)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_group",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$max": {"$add": [1, 2], "$multiply": [3, 4]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($group)",
    ),
]

MAX_ARITY_ERROR_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": []}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": [1]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": ["$v"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": [1, 2, 3]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($bucket)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_bucket",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$max": {"$add": [1, 2], "$multiply": [3, 4]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($bucket)",
    ),
]

MAX_ARITY_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": []}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject empty array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_single_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": [1]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single-element literal array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": ["$v"]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject single field ref in array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_multi_element_array_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": [1, 2, 3]}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$max should reject multi-element array in accumulator context ($bucketAuto)",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression_object_bucket_auto",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$max": {"$add": [1, 2], "$multiply": [3, 4]}}},
                }
            },
            {"$project": {"_id": 0, "result": 1}},
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$max should reject multi-key expression object ($bucketAuto)",
    ),
]

MAX_ARITY_ERROR_TESTS = (
    MAX_ARITY_ERROR_GROUP_TESTS + MAX_ARITY_ERROR_BUCKET_TESTS + MAX_ARITY_ERROR_BUCKET_AUTO_TESTS
)


# ===========================================================================
# Test functions
# ===========================================================================


@pytest.mark.parametrize("test_case", pytest_params(MAX_EXPRESSION_ERROR_TESTS))
def test_accumulator_max_expression_errors(collection, test_case):
    """Test $max expression error propagation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)


@pytest.mark.parametrize("test_case", pytest_params(MAX_ARITY_ERROR_TESTS))
def test_accumulator_max_arity_errors(collection, test_case):
    """Test $max arity rejection across all three stages."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
