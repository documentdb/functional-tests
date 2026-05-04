"""Tests for $bucket aggregation stage — argument and option validation errors."""

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
    BUCKET_ARG_NOT_OBJECT_ERROR,
    BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
    BUCKET_MISSING_REQUIRED_ERROR,
    BUCKET_UNRECOGNIZED_OPTION_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
)

# Property [Argument Type Rejection]: $bucket rejects all non-object BSON
# types as its argument.
BUCKET_ARG_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arg_type_string",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": "hello"}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject string argument",
    ),
    StageTestCase(
        "arg_type_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": 42}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject int32 argument",
    ),
    StageTestCase(
        "arg_type_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": Int64(42)}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject int64 argument",
    ),
    StageTestCase(
        "arg_type_double",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": 3.14}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject double argument",
    ),
    StageTestCase(
        "arg_type_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": DECIMAL128_ZERO}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject Decimal128 argument",
    ),
    StageTestCase(
        "arg_type_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": True}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject boolean argument",
    ),
    StageTestCase(
        "arg_type_null",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": None}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject null argument",
    ),
    StageTestCase(
        "arg_type_array",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": [1, 2]}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject array argument",
    ),
    StageTestCase(
        "arg_type_objectid",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": ObjectId("000000000000000000000001")}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject ObjectId argument",
    ),
    StageTestCase(
        "arg_type_datetime",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject datetime argument",
    ),
    StageTestCase(
        "arg_type_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": Timestamp(1, 1)}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject Timestamp argument",
    ),
    StageTestCase(
        "arg_type_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": Binary(b"hello")}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject Binary argument",
    ),
    StageTestCase(
        "arg_type_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": Regex("abc")}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject Regex argument",
    ),
    StageTestCase(
        "arg_type_code",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": Code("function(){}")}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject Code argument",
    ),
    StageTestCase(
        "arg_type_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": Code("function(){}", {"x": 1})}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject Code with scope argument",
    ),
    StageTestCase(
        "arg_type_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": MinKey()}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject MinKey argument",
    ),
    StageTestCase(
        "arg_type_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": MaxKey()}],
        error_code=BUCKET_ARG_NOT_OBJECT_ERROR,
        msg="$bucket should reject MaxKey argument",
    ),
]

# Property [Unrecognized Option Rejection]: $bucket rejects any key that is
# not one of the four recognized options (groupBy, boundaries, default,
# output), including case-variant spellings.
BUCKET_UNRECOGNIZED_OPTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "extra_key",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "boundaries": [0, 10], "extra": 1}}],
        error_code=BUCKET_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucket should reject unrecognized option 'extra'",
    ),
    StageTestCase(
        "case_GroupBy",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"GroupBy": "$x", "boundaries": [0, 10]}}],
        error_code=BUCKET_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucket should reject case-variant 'GroupBy'",
    ),
    StageTestCase(
        "case_Boundaries",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x", "Boundaries": [0, 10]}}],
        error_code=BUCKET_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucket should reject case-variant 'Boundaries'",
    ),
    StageTestCase(
        "case_Default",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "Default": "other",
                }
            }
        ],
        error_code=BUCKET_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucket should reject case-variant 'Default'",
    ),
    StageTestCase(
        "case_Output",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "Output": {},
                }
            }
        ],
        error_code=BUCKET_UNRECOGNIZED_OPTION_ERROR,
        msg="$bucket should reject case-variant 'Output'",
    ),
]

# Property [Missing Required Fields]: $bucket requires both 'groupBy' and
# 'boundaries' to be specified.
BUCKET_MISSING_REQUIRED_TESTS: list[StageTestCase] = [
    StageTestCase(
        "missing_groupBy",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"boundaries": [0, 10]}}],
        error_code=BUCKET_MISSING_REQUIRED_ERROR,
        msg="$bucket should reject missing 'groupBy'",
    ),
    StageTestCase(
        "missing_boundaries",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "$x"}}],
        error_code=BUCKET_MISSING_REQUIRED_ERROR,
        msg="$bucket should reject missing 'boundaries'",
    ),
    StageTestCase(
        "missing_both",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {}}],
        error_code=BUCKET_MISSING_REQUIRED_ERROR,
        msg="$bucket should reject empty object with no required fields",
    ),
]

# Property [GroupBy Expression Rejection]: the 'groupBy' field must be a
# $-prefixed path or an expression object; all other types and non-$-prefixed
# strings are rejected.
BUCKET_GROUPBY_TYPE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "groupBy_string_no_dollar",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": "x", "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject non-$-prefixed string groupBy",
    ),
    StageTestCase(
        "groupBy_int32",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": 42, "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject int32 groupBy",
    ),
    StageTestCase(
        "groupBy_int64",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": Int64(42), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject int64 groupBy",
    ),
    StageTestCase(
        "groupBy_double",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": 3.14, "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject double groupBy",
    ),
    StageTestCase(
        "groupBy_decimal128",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": DECIMAL128_ZERO, "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject Decimal128 groupBy",
    ),
    StageTestCase(
        "groupBy_bool",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": True, "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject bool groupBy",
    ),
    StageTestCase(
        "groupBy_null",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": None, "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject null groupBy",
    ),
    StageTestCase(
        "groupBy_array",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": [1], "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject array groupBy",
    ),
    StageTestCase(
        "groupBy_objectid",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": ObjectId("000000000000000000000001"),
                    "boundaries": [0, 10],
                }
            }
        ],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject ObjectId groupBy",
    ),
    StageTestCase(
        "groupBy_datetime",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": datetime(2024, 1, 1, tzinfo=timezone.utc),
                    "boundaries": [0, 10],
                }
            }
        ],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject datetime groupBy",
    ),
    StageTestCase(
        "groupBy_timestamp",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": Timestamp(1, 1), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject Timestamp groupBy",
    ),
    StageTestCase(
        "groupBy_binary",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": Binary(b"hi"), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject Binary groupBy",
    ),
    StageTestCase(
        "groupBy_regex",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": Regex("abc"), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject Regex groupBy",
    ),
    StageTestCase(
        "groupBy_code",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": Code("function(){}"), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject Code groupBy",
    ),
    StageTestCase(
        "groupBy_code_with_scope",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": Code("function(){}", {"x": 1}),
                    "boundaries": [0, 10],
                }
            }
        ],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject Code with scope groupBy",
    ),
    StageTestCase(
        "groupBy_minkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": MinKey(), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject MinKey groupBy",
    ),
    StageTestCase(
        "groupBy_maxkey",
        docs=[{"_id": 1}],
        pipeline=[{"$bucket": {"groupBy": MaxKey(), "boundaries": [0, 10]}}],
        error_code=BUCKET_GROUPBY_NOT_EXPRESSION_ERROR,
        msg="$bucket should reject MaxKey groupBy",
    ),
]

BUCKET_ARG_ERROR_TESTS = (
    BUCKET_ARG_TYPE_TESTS
    + BUCKET_UNRECOGNIZED_OPTION_TESTS
    + BUCKET_MISSING_REQUIRED_TESTS
    + BUCKET_GROUPBY_TYPE_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_ARG_ERROR_TESTS))
def test_bucket_arg_errors(collection, test_case: StageTestCase):
    """Test $bucket argument and option validation errors."""
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
