"""Tests for $bucket aggregation stage — boundary validation errors."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BUCKET_BOUNDARIES_MIN_LENGTH_ERROR,
    BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
    BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
    BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
)

# Property [Boundaries Type Rejection]: the 'boundaries' field must be an
# array; all non-array types are rejected.
BUCKET_BOUNDARIES_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "boundaries_string",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": "abc"}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject string boundaries",
    ),
    StageTestCase(
        "boundaries_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": 42}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject int32 boundaries",
    ),
    StageTestCase(
        "boundaries_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": Int64(42)}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject int64 boundaries",
    ),
    StageTestCase(
        "boundaries_double",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": 3.14}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject double boundaries",
    ),
    StageTestCase(
        "boundaries_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": DECIMAL128_ZERO}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject Decimal128 boundaries",
    ),
    StageTestCase(
        "boundaries_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": True}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject boolean boundaries",
    ),
    StageTestCase(
        "boundaries_null",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": None}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject null boundaries",
    ),
    StageTestCase(
        "boundaries_object",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": {"a": 1}}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject object boundaries",
    ),
    StageTestCase(
        "boundaries_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": ObjectId("000000000000000000000001")}}
        ],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject ObjectId boundaries",
    ),
    StageTestCase(
        "boundaries_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": datetime(2024, 1, 1, tzinfo=timezone.utc)}}
        ],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject datetime boundaries",
    ),
    StageTestCase(
        "boundaries_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": Timestamp(1, 1)}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject Timestamp boundaries",
    ),
    StageTestCase(
        "boundaries_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": Binary(b"hi")}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject Binary boundaries",
    ),
    StageTestCase(
        "boundaries_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": Regex("abc")}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject Regex boundaries",
    ),
    StageTestCase(
        "boundaries_code",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": Code("function(){}")}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject Code boundaries",
    ),
    StageTestCase(
        "boundaries_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": Code("function(){}", {"x": 1})}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject Code with scope boundaries",
    ),
    StageTestCase(
        "boundaries_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": MinKey()}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject MinKey boundaries",
    ),
    StageTestCase(
        "boundaries_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": MaxKey()}}],
        error_code=BUCKET_BOUNDARIES_NOT_ARRAY_ERROR,
        msg="$bucket should reject MaxKey boundaries",
    ),
]

# Property [Boundaries Minimum Length]: the 'boundaries' array must contain
# at least 2 values.
BUCKET_BOUNDARIES_LENGTH_TESTS: list[StageTestCase] = [
    StageTestCase(
        "boundaries_empty",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": []}}],
        error_code=BUCKET_BOUNDARIES_MIN_LENGTH_ERROR,
        msg="$bucket should reject empty boundaries array",
    ),
    StageTestCase(
        "boundaries_one_element",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [1]}}],
        error_code=BUCKET_BOUNDARIES_MIN_LENGTH_ERROR,
        msg="$bucket should reject boundaries array with one element",
    ),
]

# Property [Boundaries Sort Order]: the 'boundaries' array must be in
# strictly ascending order; duplicates are treated as a sort violation.
BUCKET_BOUNDARIES_SORT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "boundaries_unsorted",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [10, 5, 20]}}],
        error_code=BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
        msg="$bucket should reject unsorted boundaries",
    ),
    StageTestCase(
        "boundaries_duplicate",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 5, 5, 10]}}],
        error_code=BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
        msg="$bucket should reject duplicate boundary values",
    ),
    StageTestCase(
        "boundaries_descending_negative",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [-5, -10, 0]}}],
        error_code=BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
        msg="$bucket should reject descending negative boundaries",
    ),
    StageTestCase(
        "boundaries_duplicate_negative",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [-5, -5, 0]}}],
        error_code=BUCKET_BOUNDARIES_NOT_SORTED_ERROR,
        msg="$bucket should reject duplicate negative boundary values",
    ),
]

# Property [Boundaries Type Homogeneity]: all values in the 'boundaries'
# array must have the same type.
BUCKET_BOUNDARIES_MIXED_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "boundaries_mixed_int_string",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, "abc", 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and string",
    ),
    StageTestCase(
        "boundaries_mixed_int_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, True, 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and bool",
    ),
    StageTestCase(
        "boundaries_mixed_int_null",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, None, 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and null",
    ),
    StageTestCase(
        "boundaries_mixed_int_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, ObjectId("000000000000000000000001"), 10],
                }
            }
        ],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and ObjectId",
    ),
    StageTestCase(
        "boundaries_mixed_int_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, datetime(2024, 1, 1, tzinfo=timezone.utc), 10],
                }
            }
        ],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and datetime",
    ),
    StageTestCase(
        "boundaries_mixed_int_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, Timestamp(1, 1), 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and Timestamp",
    ),
    StageTestCase(
        "boundaries_mixed_int_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, Binary(b"hi"), 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and Binary",
    ),
    StageTestCase(
        "boundaries_mixed_int_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, Regex("abc"), 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and Regex",
    ),
    StageTestCase(
        "boundaries_mixed_int_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, Code("function(){}"), 10],
                }
            }
        ],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and Code",
    ),
    StageTestCase(
        "boundaries_mixed_int_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, Code("function(){}", {"x": 1}), 10],
                }
            }
        ],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and Code with scope",
    ),
    StageTestCase(
        "boundaries_mixed_int_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, MinKey(), 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and MinKey",
    ),
    StageTestCase(
        "boundaries_mixed_int_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, MaxKey(), 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and MaxKey",
    ),
    StageTestCase(
        "boundaries_mixed_int_array",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, [1], 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and array",
    ),
    StageTestCase(
        "boundaries_mixed_int_object",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, {"a": 1}, 10]}}],
        error_code=BUCKET_BOUNDARIES_MIXED_TYPES_ERROR,
        msg="$bucket should reject boundaries mixing int and object",
    ),
]

BUCKET_BOUNDARY_ERROR_TESTS = (
    BUCKET_BOUNDARIES_TYPE_TESTS
    + BUCKET_BOUNDARIES_LENGTH_TESTS
    + BUCKET_BOUNDARIES_SORT_TESTS
    + BUCKET_BOUNDARIES_MIXED_TYPE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_BOUNDARY_ERROR_TESTS))
def test_bucket_boundary_errors(collection, test_case: StageTestCase):
    """Test $bucket boundary validation errors."""
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
