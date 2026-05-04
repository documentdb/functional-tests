"""Tests for $bucket aggregation stage — output field validation errors."""

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
    BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
    BUCKET_OUTPUT_DOT_ERROR,
    BUCKET_OUTPUT_ID_RESERVED_ERROR,
    BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
    BUCKET_OUTPUT_NOT_OBJECT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
)

# Property [Output Type Rejection]: the 'output' field must be an object;
# all non-object types are rejected.
BUCKET_OUTPUT_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_string",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": "bad"}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject string output",
    ),
    StageTestCase(
        "output_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": 42}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject int32 output",
    ),
    StageTestCase(
        "output_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": Int64(42)}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject int64 output",
    ),
    StageTestCase(
        "output_double",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": 3.14}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject double output",
    ),
    StageTestCase(
        "output_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": DECIMAL128_ZERO}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject Decimal128 output",
    ),
    StageTestCase(
        "output_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": True}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject bool output",
    ),
    StageTestCase(
        "output_null",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": None}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject null output",
    ),
    StageTestCase(
        "output_array",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": [1]}}],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject array output",
    ),
    StageTestCase(
        "output_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": ObjectId("000000000000000000000001"),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject ObjectId output",
    ),
    StageTestCase(
        "output_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": datetime(2024, 1, 1, tzinfo=timezone.utc),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject datetime output",
    ),
    StageTestCase(
        "output_timestamp",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": Timestamp(1, 1),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject Timestamp output",
    ),
    StageTestCase(
        "output_binary",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": Binary(b"hi"),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject Binary output",
    ),
    StageTestCase(
        "output_regex",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": Regex("abc"),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject Regex output",
    ),
    StageTestCase(
        "output_code",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": Code("function(){}"),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject Code output",
    ),
    StageTestCase(
        "output_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": Code("function(){}", {"x": 1}),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject Code with scope output",
    ),
    StageTestCase(
        "output_minkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": MinKey(),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject MinKey output",
    ),
    StageTestCase(
        "output_maxkey",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": MaxKey(),
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucket should reject MaxKey output",
    ),
]

# Property [Output Field Dollar Prefix Rejection]: output field names
# starting with $ are rejected.
BUCKET_OUTPUT_DOLLAR_PREFIX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_dollar_bare",
        docs=[{"_id": 1}],
        pipeline=[
            {"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "output": {"$": {"$sum": 1}}}}
        ],
        error_code=BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
        msg="$bucket should reject output field name '$'",
    ),
    StageTestCase(
        "output_field_dollar_prefixed",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"$foo": {"$sum": 1}},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
        msg="$bucket should reject $-prefixed output field name",
    ),
    StageTestCase(
        "output_field_double_dollar",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"$$var": {"$sum": 1}},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
        msg="$bucket should reject $$-prefixed output field name",
    ),
]

# Property [Output Field Dot Rejection]: output field names containing a
# dot are rejected.
BUCKET_OUTPUT_DOT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_dot_middle",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"a.b": {"$sum": 1}},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_DOT_ERROR,
        msg="$bucket should reject output field name containing dot",
    ),
    StageTestCase(
        "output_field_dot_start",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {".a": {"$sum": 1}},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_DOT_ERROR,
        msg="$bucket should reject output field name starting with dot",
    ),
    StageTestCase(
        "output_field_dot_end",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"a.": {"$sum": 1}},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_DOT_ERROR,
        msg="$bucket should reject output field name ending with dot",
    ),
]

# Property [Output Field _id Rejection]: _id cannot be used as an output
# field name because it conflicts with the bucket _id.
BUCKET_OUTPUT_ID_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_id",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"_id": {"$sum": 1}},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_ID_RESERVED_ERROR,
        msg="$bucket should reject _id as output field name",
    ),
]

# Property [Output Field Not Accumulator]: output field values must be
# accumulator objects; non-accumulator values are rejected.
BUCKET_OUTPUT_NOT_ACCUMULATOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_int_value",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"f": 42},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="$bucket should reject non-accumulator int value in output",
    ),
    StageTestCase(
        "output_field_string_value",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"f": "hello"},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="$bucket should reject non-accumulator string value in output",
    ),
    StageTestCase(
        "output_field_null_value",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "output": {"f": None},
                }
            }
        ],
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="$bucket should reject non-accumulator null value in output",
    ),
]

BUCKET_OUTPUT_ERROR_TESTS = (
    BUCKET_OUTPUT_TYPE_TESTS
    + BUCKET_OUTPUT_DOLLAR_PREFIX_TESTS
    + BUCKET_OUTPUT_DOT_TESTS
    + BUCKET_OUTPUT_ID_TESTS
    + BUCKET_OUTPUT_NOT_ACCUMULATOR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_OUTPUT_ERROR_TESTS))
def test_bucket_output_errors(collection, test_case: StageTestCase):
    """Test $bucket output field validation errors."""
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
