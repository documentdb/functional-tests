"""Tests for $unwind stage — spec type and path type validation errors."""

from __future__ import annotations

from datetime import datetime

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
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
    UNWIND_PATH_TYPE_ERROR,
    UNWIND_SPEC_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Spec Type Shorthand Validation]: in shorthand form, all non-string,
# non-document BSON types are rejected as an invalid spec type.
UNWIND_SPEC_TYPE_SHORTHAND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_type_int32",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": 1}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject int32",
    ),
    StageTestCase(
        "spec_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Int64(1)}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Int64",
    ),
    StageTestCase(
        "spec_type_double",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": 1.5}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject double",
    ),
    StageTestCase(
        "spec_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Decimal128("1")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Decimal128",
    ),
    StageTestCase(
        "spec_type_bool",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": True}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject bool",
    ),
    StageTestCase(
        "spec_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": None}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject null",
    ),
    StageTestCase(
        "spec_type_array_empty",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": []}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject empty array",
    ),
    StageTestCase(
        "spec_type_array_with_field_ref",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": ["$a"]}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject array containing field reference",
    ),
    StageTestCase(
        "spec_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": ObjectId("000000000000000000000001")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject ObjectId",
    ),
    StageTestCase(
        "spec_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": datetime(2024, 1, 1)}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject datetime",
    ),
    StageTestCase(
        "spec_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Timestamp(1, 1)}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Timestamp",
    ),
    StageTestCase(
        "spec_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Binary(b"\x01")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Binary",
    ),
    StageTestCase(
        "spec_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Regex("^a")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Regex",
    ),
    StageTestCase(
        "spec_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Code("x")}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Code",
    ),
    StageTestCase(
        "spec_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": Code("x", {})}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject Code with scope",
    ),
    StageTestCase(
        "spec_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": MinKey()}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject MinKey",
    ),
    StageTestCase(
        "spec_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": MaxKey()}],
        error_code=UNWIND_SPEC_TYPE_ERROR,
        msg="$unwind shorthand should reject MaxKey",
    ),
]

# Property [Path Type Validation (Document Form)]: in document form, all
# non-string BSON types for path are rejected with a path type error.
UNWIND_PATH_TYPE_DOC_FORM_TESTS: list[StageTestCase] = [
    StageTestCase(
        "path_type_int32",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 1}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject int32 path",
    ),
    StageTestCase(
        "path_type_int64",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Int64(1)}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Int64 path",
    ),
    StageTestCase(
        "path_type_double",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": 1.5}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject double path",
    ),
    StageTestCase(
        "path_type_decimal128",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Decimal128("1")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Decimal128 path",
    ),
    StageTestCase(
        "path_type_bool",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": True}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject bool path",
    ),
    StageTestCase(
        "path_type_null",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": None}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject null path",
    ),
    StageTestCase(
        "path_type_array",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": ["$a"]}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject array path",
    ),
    StageTestCase(
        "path_type_objectid",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": ObjectId("000000000000000000000001")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject ObjectId path",
    ),
    StageTestCase(
        "path_type_datetime",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": datetime(2024, 1, 1)}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject datetime path",
    ),
    StageTestCase(
        "path_type_timestamp",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Timestamp(1, 1)}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Timestamp path",
    ),
    StageTestCase(
        "path_type_binary",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Binary(b"\x01")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Binary path",
    ),
    StageTestCase(
        "path_type_regex",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Regex("^a")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Regex path",
    ),
    StageTestCase(
        "path_type_code",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Code("x")}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Code path",
    ),
    StageTestCase(
        "path_type_code_with_scope",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": Code("x", {})}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject Code with scope path",
    ),
    StageTestCase(
        "path_type_minkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": MinKey()}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject MinKey path",
    ),
    StageTestCase(
        "path_type_maxkey",
        docs=[{"_id": 1, "a": [1]}],
        pipeline=[{"$unwind": {"path": MaxKey()}}],
        error_code=UNWIND_PATH_TYPE_ERROR,
        msg="$unwind document form should reject MaxKey path",
    ),
]

UNWIND_TYPE_VALIDATION_TESTS = UNWIND_SPEC_TYPE_SHORTHAND_TESTS + UNWIND_PATH_TYPE_DOC_FORM_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_TYPE_VALIDATION_TESTS))
def test_unwind_type_validation(collection, test_case: StageTestCase):
    """Test $unwind spec type and path type validation errors."""
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
