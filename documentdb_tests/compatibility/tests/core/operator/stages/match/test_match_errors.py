"""Tests for $match argument validation and restricted operator errors."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MATCH_FILTER_NOT_OBJECT_ERROR,
    MATCH_TEXT_NOT_FIRST_STAGE_ERROR,
    NEAR_NOT_ALLOWED_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Argument Validation Errors]: non-document arguments to $match
# produce an error.
MATCH_ARGUMENT_VALIDATION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arg_error_string",
        pipeline=[{"$match": "hello"}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a string argument",
    ),
    StageTestCase(
        "arg_error_int",
        pipeline=[{"$match": 42}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject an integer argument",
    ),
    StageTestCase(
        "arg_error_float",
        pipeline=[{"$match": 3.14}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a float argument",
    ),
    StageTestCase(
        "arg_error_bool",
        pipeline=[{"$match": True}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a boolean argument",
    ),
    StageTestCase(
        "arg_error_null",
        pipeline=[{"$match": None}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a null argument",
    ),
    StageTestCase(
        "arg_error_array",
        pipeline=[{"$match": [1, 2]}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject an array argument",
    ),
    StageTestCase(
        "arg_error_int64",
        pipeline=[{"$match": Int64(42)}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject an int64 argument",
    ),
    StageTestCase(
        "arg_error_decimal128",
        pipeline=[{"$match": Decimal128("3.14")}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a decimal128 argument",
    ),
    StageTestCase(
        "arg_error_objectid",
        pipeline=[{"$match": ObjectId()}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject an ObjectId argument",
    ),
    StageTestCase(
        "arg_error_datetime",
        pipeline=[{"$match": datetime(2024, 1, 1)}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a datetime argument",
    ),
    StageTestCase(
        "arg_error_binary",
        pipeline=[{"$match": Binary(b"\x00\x01")}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a binary argument",
    ),
    StageTestCase(
        "arg_error_regex",
        pipeline=[{"$match": Regex("^abc")}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a regex argument",
    ),
    StageTestCase(
        "arg_error_timestamp",
        pipeline=[{"$match": Timestamp(0, 0)}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a timestamp argument",
    ),
    StageTestCase(
        "arg_error_minkey",
        pipeline=[{"$match": MinKey()}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a MinKey argument",
    ),
    StageTestCase(
        "arg_error_maxkey",
        pipeline=[{"$match": MaxKey()}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a MaxKey argument",
    ),
    StageTestCase(
        "arg_error_code",
        pipeline=[{"$match": Code("function(){}")}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a JavaScript code argument",
    ),
    StageTestCase(
        "arg_error_code_with_scope",
        pipeline=[{"$match": Code("function(){}", {"x": 1})}],
        error_code=MATCH_FILTER_NOT_OBJECT_ERROR,
        msg="$match should reject a JavaScript code with scope argument",
    ),
]

# Property [Restricted Operator Errors]: $where, $near, $nearSphere, and
# unknown $-prefixed top-level operators are rejected inside $match; $text is
# rejected when $match is not the first pipeline stage.
MATCH_RESTRICTED_OPERATOR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "restricted_where",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$match": {"$where": "true"}}],
        error_code=BAD_VALUE_ERROR,
        msg="$match should reject $where in the predicate",
    ),
    StageTestCase(
        "restricted_near",
        docs=[{"_id": 1, "loc": [0, 0]}],
        pipeline=[{"$match": {"loc": {"$near": [0, 0]}}}],
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$match should reject $near in the predicate",
    ),
    StageTestCase(
        "restricted_near_sphere",
        docs=[{"_id": 1, "loc": [0, 0]}],
        pipeline=[{"$match": {"loc": {"$nearSphere": [0, 0]}}}],
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$match should reject $nearSphere in the predicate",
    ),
    StageTestCase(
        "restricted_geo_near",
        docs=[{"_id": 1, "loc": [0, 0]}],
        pipeline=[{"$match": {"loc": {"$geoNear": {"near": [0, 0]}}}}],
        error_code=NEAR_NOT_ALLOWED_ERROR,
        msg="$match should reject $geoNear in the predicate",
    ),
    StageTestCase(
        "restricted_text_non_first_stage",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$project": {"a": 1}},
            {"$match": {"$text": {"$search": "hello"}}},
        ],
        error_code=MATCH_TEXT_NOT_FIRST_STAGE_ERROR,
        msg="$match should reject $text when it is not the first pipeline stage",
    ),
    StageTestCase(
        "restricted_unknown_dollar_operator",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$match": {"$fakeOperator": 1}}],
        error_code=BAD_VALUE_ERROR,
        msg="$match should reject an unknown $-prefixed top-level operator",
    ),
]

MATCH_ERROR_TESTS_ALL = MATCH_ARGUMENT_VALIDATION_TESTS + MATCH_RESTRICTED_OPERATOR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MATCH_ERROR_TESTS_ALL))
def test_match_error_cases(collection, test_case: StageTestCase):
    """Test $match argument validation and restricted operator errors."""
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
