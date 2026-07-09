"""Tests for $bucketAuto aggregation stage — output field validation errors."""

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
    BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
    BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
    BUCKET_OUTPUT_DOT_ERROR,
    BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
)


def _out(value):
    return [{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "output": value}}]


# Property [Output Type Rejection]: the 'output' field must be an object; all
# non-object types are rejected.
BUCKET_AUTO_OUTPUT_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_string",
        docs=[{"_id": 1}],
        pipeline=_out("bad"),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject string output",
    ),
    StageTestCase(
        "output_int32",
        docs=[{"_id": 1}],
        pipeline=_out(42),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject int32 output",
    ),
    StageTestCase(
        "output_int64",
        docs=[{"_id": 1}],
        pipeline=_out(Int64(42)),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject int64 output",
    ),
    StageTestCase(
        "output_double",
        docs=[{"_id": 1}],
        pipeline=_out(3.14),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject double output",
    ),
    StageTestCase(
        "output_decimal128",
        docs=[{"_id": 1}],
        pipeline=_out(DECIMAL128_ZERO),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Decimal128 output",
    ),
    StageTestCase(
        "output_bool",
        docs=[{"_id": 1}],
        pipeline=_out(True),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject bool output",
    ),
    StageTestCase(
        "output_null",
        docs=[{"_id": 1}],
        pipeline=_out(None),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject null output",
    ),
    StageTestCase(
        "output_array",
        docs=[{"_id": 1}],
        pipeline=_out([1]),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject array output",
    ),
    StageTestCase(
        "output_objectid",
        docs=[{"_id": 1}],
        pipeline=_out(ObjectId("000000000000000000000001")),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject ObjectId output",
    ),
    StageTestCase(
        "output_datetime",
        docs=[{"_id": 1}],
        pipeline=_out(datetime(2024, 1, 1, tzinfo=timezone.utc)),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject datetime output",
    ),
    StageTestCase(
        "output_timestamp",
        docs=[{"_id": 1}],
        pipeline=_out(Timestamp(1, 1)),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Timestamp output",
    ),
    StageTestCase(
        "output_binary",
        docs=[{"_id": 1}],
        pipeline=_out(Binary(b"hi")),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Binary output",
    ),
    StageTestCase(
        "output_regex",
        docs=[{"_id": 1}],
        pipeline=_out(Regex("abc")),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Regex output",
    ),
    StageTestCase(
        "output_code",
        docs=[{"_id": 1}],
        pipeline=_out(Code("function(){}")),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Code output",
    ),
    StageTestCase(
        "output_minkey",
        docs=[{"_id": 1}],
        pipeline=_out(MinKey()),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject MinKey output",
    ),
    StageTestCase(
        "output_maxkey",
        docs=[{"_id": 1}],
        pipeline=_out(MaxKey()),
        error_code=BUCKET_AUTO_OUTPUT_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject MaxKey output",
    ),
]

# Property [Output Field Dollar Prefix Rejection]: output field names starting
# with $ are rejected.
BUCKET_AUTO_OUTPUT_DOLLAR_PREFIX_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_dollar_prefixed",
        docs=[{"_id": 1}],
        pipeline=_out({"$foo": {"$sum": 1}}),
        error_code=BUCKET_OUTPUT_DOLLAR_PREFIX_ERROR,
        msg="$bucketAuto should reject $-prefixed output field name",
    ),
]

# Property [Output Field Dot Rejection]: output field names containing a dot
# are rejected.
BUCKET_AUTO_OUTPUT_DOT_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_dot_middle",
        docs=[{"_id": 1}],
        pipeline=_out({"a.b": {"$sum": 1}}),
        error_code=BUCKET_OUTPUT_DOT_ERROR,
        msg="$bucketAuto should reject output field name containing a dot",
    ),
]

# Property [Output Field Not Accumulator]: output field values must be
# accumulator objects; non-accumulator values are rejected.
BUCKET_AUTO_OUTPUT_NOT_ACCUMULATOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "output_field_int_value",
        docs=[{"_id": 1}],
        pipeline=_out({"f": 42}),
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="$bucketAuto should reject non-accumulator int value in output",
    ),
    StageTestCase(
        "output_field_string_value",
        docs=[{"_id": 1}],
        pipeline=_out({"f": "hello"}),
        error_code=BUCKET_OUTPUT_NOT_ACCUMULATOR_ERROR,
        msg="$bucketAuto should reject non-accumulator string value in output",
    ),
]

BUCKET_AUTO_OUTPUT_ERROR_TESTS = (
    BUCKET_AUTO_OUTPUT_TYPE_TESTS
    + BUCKET_AUTO_OUTPUT_DOLLAR_PREFIX_TESTS
    + BUCKET_AUTO_OUTPUT_DOT_TESTS
    + BUCKET_AUTO_OUTPUT_NOT_ACCUMULATOR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_OUTPUT_ERROR_TESTS))
def test_bucketAuto_output_errors(collection, test_case: StageTestCase):
    """Test $bucketAuto output field validation errors."""
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
