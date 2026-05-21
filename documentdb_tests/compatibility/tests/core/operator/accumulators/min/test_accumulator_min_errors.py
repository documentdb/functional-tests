"""Tests for $min accumulator error cases: arity rejection."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
    GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Arity Rejection]: $min in accumulator context is unary and rejects
# array syntax in $group, $bucket, and $bucketAuto.
MIN_ARITY_ERROR_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "arity_empty_array",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": []}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject empty array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_element",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": [1]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_single_field_ref",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": ["$v"]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject single field ref in array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_element",
        docs=[{"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": [1, 2, 3]}}}],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min should reject multi-element array in accumulator context",
    ),
    AccumulatorTestCase(
        "arity_multi_key_expression",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$min": {"$add": [1, 2], "$multiply": [3, 4]}}}}
        ],
        error_code=EXPRESSION_OBJECT_MULTIPLE_FIELDS_ERROR,
        msg="$min should reject multi-key expression object",
    ),
]

MIN_ARITY_ERROR_BUCKET_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_arity_rejection",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": 0},
                    "boundaries": [-1, 1],
                    "output": {"result": {"$min": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min in $bucket should reject array syntax",
    ),
]

MIN_ARITY_ERROR_BUCKET_AUTO_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bucket_auto_arity_rejection",
        docs=[{"v": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": {"$literal": 0},
                    "buckets": 1,
                    "output": {"result": {"$min": []}},
                }
            }
        ],
        error_code=GROUP_ACCUMULATOR_ARRAY_ARGUMENT_ERROR,
        msg="$min in $bucketAuto should reject array syntax",
    ),
]

MIN_ARITY_ERROR_TESTS = (
    MIN_ARITY_ERROR_GROUP_TESTS + MIN_ARITY_ERROR_BUCKET_TESTS + MIN_ARITY_ERROR_BUCKET_AUTO_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(MIN_ARITY_ERROR_TESTS))
def test_accumulator_min_errors(collection, test_case):
    """Test $min accumulator error cases: arity rejection."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertFailureCode(result, test_case.error_code, msg=test_case.msg)
