"""Tests for $planCacheStats type errors."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BSON_FIELD_NOT_BOOL_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ZERO,
    DOUBLE_ZERO,
    INT64_ZERO,
)

# Property [Stage Argument Type Error]: non-document values as the stage
# argument produce a FAILED_TO_PARSE_ERROR.
STAGE_ARGUMENT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "arg_type_string",
        docs=[],
        pipeline=[{"$planCacheStats": "hello"}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject string argument",
    ),
    StageTestCase(
        "arg_type_int",
        docs=[],
        pipeline=[{"$planCacheStats": 42}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject int argument",
    ),
    StageTestCase(
        "arg_type_array",
        docs=[],
        pipeline=[{"$planCacheStats": [1, 2]}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject array argument",
    ),
    StageTestCase(
        "arg_type_null",
        docs=[],
        pipeline=[{"$planCacheStats": None}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject null argument",
    ),
    StageTestCase(
        "arg_type_bool",
        docs=[],
        pipeline=[{"$planCacheStats": True}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject bool argument",
    ),
    StageTestCase(
        "arg_type_double",
        docs=[],
        pipeline=[{"$planCacheStats": 3.14}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject double argument",
    ),
    StageTestCase(
        "arg_type_binary",
        docs=[],
        pipeline=[{"$planCacheStats": Binary(b"data")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Binary argument",
    ),
    StageTestCase(
        "arg_type_objectid",
        docs=[],
        pipeline=[{"$planCacheStats": ObjectId()}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject ObjectId argument",
    ),
    StageTestCase(
        "arg_type_datetime",
        docs=[],
        pipeline=[{"$planCacheStats": datetime(2024, 1, 1)}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject datetime argument",
    ),
    StageTestCase(
        "arg_type_regex",
        docs=[],
        pipeline=[{"$planCacheStats": Regex(".*")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Regex argument",
    ),
    StageTestCase(
        "arg_type_code",
        docs=[],
        pipeline=[{"$planCacheStats": Code("function(){}")}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Code argument",
    ),
    StageTestCase(
        "arg_type_code_with_scope",
        docs=[],
        pipeline=[{"$planCacheStats": Code("function(){}", {})}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Code with scope argument",
    ),
    StageTestCase(
        "arg_type_timestamp",
        docs=[],
        pipeline=[{"$planCacheStats": Timestamp(0, 0)}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Timestamp argument",
    ),
    StageTestCase(
        "arg_type_int64",
        docs=[],
        pipeline=[{"$planCacheStats": INT64_ZERO}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Int64 argument",
    ),
    StageTestCase(
        "arg_type_decimal128",
        docs=[],
        pipeline=[{"$planCacheStats": DECIMAL128_ZERO}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject Decimal128 argument",
    ),
    StageTestCase(
        "arg_type_minkey",
        docs=[],
        pipeline=[{"$planCacheStats": MinKey()}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject MinKey argument",
    ),
    StageTestCase(
        "arg_type_maxkey",
        docs=[],
        pipeline=[{"$planCacheStats": MaxKey()}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$planCacheStats should reject MaxKey argument",
    ),
]

# Property [allHosts Type Strictness Error]: non-boolean values for allHosts
# produce an error with no truthy/falsy coercion.
ALLHOSTS_TYPE_STRICTNESS_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "allhosts_type_int_0",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": 0}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: 0 (int) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_int_1",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": 1}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: 1 (int) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_empty_string",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": ""}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: '' (empty string) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_null",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": None}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: null should be rejected, not treated as omission",
    ),
    StageTestCase(
        "allhosts_type_double_0",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": DOUBLE_ZERO}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: 0.0 (double) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_double_1",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": 1.0}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: 1.0 (double) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_decimal128",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": DECIMAL128_ZERO}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Decimal128 should be rejected",
    ),
    StageTestCase(
        "allhosts_type_array_empty",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": []}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: [] (array) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_object_empty",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": {}}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: {} (object) should be rejected",
    ),
    StageTestCase(
        "allhosts_type_objectid",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": ObjectId()}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: ObjectId should be rejected",
    ),
    StageTestCase(
        "allhosts_type_datetime",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": datetime(2024, 1, 1)}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: datetime should be rejected",
    ),
    StageTestCase(
        "allhosts_type_timestamp",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": Timestamp(0, 0)}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Timestamp should be rejected",
    ),
    StageTestCase(
        "allhosts_type_binary",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": Binary(b"x")}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Binary should be rejected",
    ),
    StageTestCase(
        "allhosts_type_regex",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": Regex(".*")}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Regex should be rejected",
    ),
    StageTestCase(
        "allhosts_type_code",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": Code("function(){}")}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Code should be rejected",
    ),
    StageTestCase(
        "allhosts_type_code_with_scope",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": Code("function(){}", {})}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Code with scope should be rejected",
    ),
    StageTestCase(
        "allhosts_type_minkey",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": MinKey()}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: MinKey should be rejected",
    ),
    StageTestCase(
        "allhosts_type_maxkey",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": MaxKey()}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: MaxKey should be rejected",
    ),
    StageTestCase(
        "allhosts_type_int64_0",
        docs=[],
        pipeline=[{"$planCacheStats": {"allHosts": INT64_ZERO}}],
        error_code=BSON_FIELD_NOT_BOOL_ERROR,
        msg="allHosts: Int64(0) should be rejected",
    ),
]

PLANCACHESTATS_TYPE_ERROR_TESTS = (
    STAGE_ARGUMENT_TYPE_ERROR_TESTS + ALLHOSTS_TYPE_STRICTNESS_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(PLANCACHESTATS_TYPE_ERROR_TESTS))
def test_planCacheStats_type_errors(collection: Collection, test_case: StageTestCase):
    """Test $planCacheStats type error handling."""
    coll = populate_collection(collection, test_case)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
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
