"""Tests for $bucketAuto aggregation stage — accumulator error propagation."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Accumulator Error Propagation]: errors raised by an accumulator
# sub-expression propagate out of $bucketAuto.
BUCKET_AUTO_ACCUMULATOR_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "conversion_error_field_driven",
        docs=[{"_id": 1, "x": 1, "v": "notnum"}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"r": {"$sum": {"$add": ["$v", 1]}}},
                }
            }
        ],
        error_code=TYPE_MISMATCH_ERROR,
        msg="$bucketAuto should propagate a field-driven accumulator conversion error",
    ),
    StageTestCase(
        "divide_by_zero_literal_driven",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[
            {
                "$bucketAuto": {
                    "groupBy": "$x",
                    "buckets": 1,
                    "output": {"r": {"$sum": {"$divide": [1, 0]}}},
                }
            }
        ],
        error_code=BAD_VALUE_ERROR,
        msg="$bucketAuto should propagate a literal-driven divide-by-zero error",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_ACCUMULATOR_ERROR_TESTS))
def test_bucketAuto_accumulator_errors(collection, test_case: StageTestCase):
    """Test $bucketAuto accumulator error propagation."""
    populate_collection(collection, test_case)
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
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
