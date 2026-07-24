"""Tests for $bucketAuto aggregation stage — argument and option validation errors."""

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
    BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
    BUCKET_AUTO_MISSING_REQUIRED_ERROR,
    BUCKET_AUTO_UNRECOGNIZED_OPTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
)

# Property [Argument Type Rejection]: $bucketAuto rejects all non-object BSON
# types as its argument.
BUCKET_AUTO_ARG_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arg_type_string",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": "hello"}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject string argument",
    ),
    StageTestCase(
        "arg_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": 42}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject int32 argument",
    ),
    StageTestCase(
        "arg_type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": Int64(42)}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject int64 argument",
    ),
    StageTestCase(
        "arg_type_double",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": 3.14}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject double argument",
    ),
    StageTestCase(
        "arg_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": DECIMAL128_ZERO}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Decimal128 argument",
    ),
    StageTestCase(
        "arg_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": True}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject boolean argument",
    ),
    StageTestCase(
        "arg_type_null",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": None}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject null argument",
    ),
    StageTestCase(
        "arg_type_array",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": [1, 2]}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject array argument",
    ),
    StageTestCase(
        "arg_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": ObjectId("000000000000000000000001")}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject ObjectId argument",
    ),
    StageTestCase(
        "arg_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject datetime argument",
    ),
    StageTestCase(
        "arg_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": Timestamp(1, 1)}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Timestamp argument",
    ),
    StageTestCase(
        "arg_type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": Binary(b"hello")}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Binary argument",
    ),
    StageTestCase(
        "arg_type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": Regex("abc")}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Regex argument",
    ),
    StageTestCase(
        "arg_type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": Code("function(){}")}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject Code argument",
    ),
    StageTestCase(
        "arg_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": MinKey()}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject MinKey argument",
    ),
    StageTestCase(
        "arg_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": MaxKey()}],
        error_code=BUCKET_AUTO_ARG_NOT_OBJECT_ERROR,
        msg="$bucketAuto should reject MaxKey argument",
    ),
]

# Property [Unrecognized Option Rejection]: $bucketAuto rejects any key that is
# not one of the four recognized options (groupBy, buckets, output,
# granularity), including case-variant spellings.
BUCKET_AUTO_UNRECOGNIZED_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "extra_key",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "extra": 1}}],
        error_code=BUCKET_AUTO_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucketAuto should reject unrecognized option 'extra'",
    ),
    StageTestCase(
        "case_GroupBy",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"GroupBy": "$x", "buckets": 2}}],
        error_code=BUCKET_AUTO_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucketAuto should reject case-variant 'GroupBy'",
    ),
    StageTestCase(
        "case_Buckets",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "Buckets": 2}}],
        error_code=BUCKET_AUTO_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucketAuto should reject case-variant 'Buckets'",
    ),
    StageTestCase(
        "case_Output",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "Output": {}}}],
        error_code=BUCKET_AUTO_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucketAuto should reject case-variant 'Output'",
    ),
    StageTestCase(
        "case_Granularity",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x", "buckets": 2, "Granularity": "R5"}}],
        error_code=BUCKET_AUTO_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucketAuto should reject case-variant 'Granularity'",
    ),
]

# Property [Missing Required Fields]: $bucketAuto requires both 'groupBy' and
# 'buckets' to be specified.
BUCKET_AUTO_MISSING_REQUIRED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "missing_groupBy",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"buckets": 2}}],
        error_code=BUCKET_AUTO_MISSING_REQUIRED_ERROR,
        msg="$bucketAuto should reject missing 'groupBy'",
    ),
    StageTestCase(
        "missing_buckets",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {"groupBy": "$x"}}],
        error_code=BUCKET_AUTO_MISSING_REQUIRED_ERROR,
        msg="$bucketAuto should reject missing 'buckets'",
    ),
    StageTestCase(
        "missing_both",
        docs=[{"_id": 1}],
        pipeline=[{"$bucketAuto": {}}],
        error_code=BUCKET_AUTO_MISSING_REQUIRED_ERROR,
        msg="$bucketAuto should reject empty object with no required fields",
    ),
]

BUCKET_AUTO_ARG_ERROR_TESTS = (
    BUCKET_AUTO_ARG_TYPE_TESTS
    + BUCKET_AUTO_UNRECOGNIZED_OPTION_TESTS
    + BUCKET_AUTO_MISSING_REQUIRED_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_AUTO_ARG_ERROR_TESTS))
def test_bucketAuto_arg_errors(collection, test_case: StageTestCase):
    """Test $bucketAuto argument and option validation errors."""
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
