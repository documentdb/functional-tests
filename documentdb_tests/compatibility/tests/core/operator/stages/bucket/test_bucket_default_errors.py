"""Tests for $bucket aggregation stage — default value range validation errors."""

from __future__ import annotations

import pytest
from bson import (
    Decimal128,
    Int64,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BUCKET_DEFAULT_RANGE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_MIN_SUBNORMAL,
    DOUBLE_NEGATIVE_ZERO,
)

# Property [Default Range Check]: the 'default' value must be less than the
# lowest boundary or greater than or equal to the highest boundary.
BUCKET_DEFAULT_RANGE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "default_within_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": 5,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject default value within boundary range",
    ),
    StageTestCase(
        "default_at_lowest_boundary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": 0,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject default equal to the lowest boundary",
    ),
    StageTestCase(
        "default_negative_zero_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DOUBLE_NEGATIVE_ZERO,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject -0.0 as default when 0 is the lowest boundary",
    ),
    StageTestCase(
        "default_decimal128_negative_zero_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_NEGATIVE_ZERO,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject Decimal128 -0 as default when 0 is the lowest boundary",
    ),
    StageTestCase(
        "default_subnormal_positive_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DOUBLE_MIN_SUBNORMAL,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject positive subnormal double within boundary range",
    ),
    StageTestCase(
        "default_decimal128_subnormal_positive_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": DECIMAL128_MIN_POSITIVE,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject Decimal128 min positive within boundary range",
    ),
    StageTestCase(
        "default_cross_type_float_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": 5.0,
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject float default within int boundary range",
    ),
    StageTestCase(
        "default_cross_type_int64_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Int64(5),
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject Int64 default within int boundary range",
    ),
    StageTestCase(
        "default_cross_type_decimal128_in_range",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": Decimal128("5"),
                }
            }
        ],
        error_code=BUCKET_DEFAULT_RANGE_ERROR,
        msg="$bucket should reject Decimal128 default within int boundary range",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_DEFAULT_RANGE_TESTS))
def test_bucket_default_errors(collection, test_case: StageTestCase):
    """Test $bucket default value range validation errors."""
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
