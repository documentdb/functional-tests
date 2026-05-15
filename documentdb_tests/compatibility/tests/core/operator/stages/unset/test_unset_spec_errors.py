"""Tests for $unset stage specification errors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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
    UNSET_ARRAY_ELEMENT_TYPE_ERROR,
    UNSET_EMPTY_ARRAY_ERROR,
    UNSET_SPEC_TYPE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_TRAILING_ZERO

# Property [Spec Type Error]: a non-string, non-array $unset specification
# produces a type error.
UNSET_SPEC_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "spec_type_error_int32",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": 123}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with int32 spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_int64",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": Int64(1)}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with Int64 spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_double",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": 1.5}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with double spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_decimal128",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": DECIMAL128_TRAILING_ZERO}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with Decimal128 spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_bool_true",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": True}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with bool true spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_bool_false",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": False}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with bool false spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": None}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with null spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_object",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": {"x": 1}}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with object spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_objectid",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ObjectId("507f1f77bcf86cd799439011")}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with ObjectId spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_datetime",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with datetime spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_timestamp",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": Timestamp(1, 1)}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with Timestamp spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_binary",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": Binary(b"\x01")}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with Binary spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_regex",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": Regex("a")}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with Regex spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_code",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": Code("function(){}")}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with Code spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_code_with_scope",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": Code("function(){}", {"x": 1})}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with CodeWithScope spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_minkey",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": MinKey()}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with MinKey spec should produce a type error",
    ),
    StageTestCase(
        "spec_type_error_maxkey",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": MaxKey()}],
        error_code=UNSET_SPEC_TYPE_ERROR,
        msg="$unset with MaxKey spec should produce a type error",
    ),
]

# Property [Array Element Type Error]: an array containing any non-string
# element produces an array element type error.
UNSET_ARRAY_ELEMENT_TYPE_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "array_element_type_error_int32",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [123]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with int32 element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_int64",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [Int64(1)]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with Int64 element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_double",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [1.5]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with double element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_decimal128",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [DECIMAL128_TRAILING_ZERO]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with Decimal128 element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_bool",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [True]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with bool element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [None]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with null element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_object",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [{"x": 1}]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with object element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_objectid",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [ObjectId("507f1f77bcf86cd799439011")]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with ObjectId element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_datetime",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [datetime(2024, 1, 1, tzinfo=timezone.utc)]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with datetime element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_timestamp",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [Timestamp(1, 1)]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with Timestamp element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_binary",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [Binary(b"\x01")]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with Binary element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_regex",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [Regex("a")]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with Regex element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_code",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [Code("function(){}")]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with Code element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_code_with_scope",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [Code("function(){}", {"x": 1})]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with CodeWithScope element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_minkey",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [MinKey()]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with MinKey element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_maxkey",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [MaxKey()]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with MaxKey element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_nested_array",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": [["a"]]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$unset array with nested array element should produce an array element type error",
    ),
    StageTestCase(
        "array_element_type_error_mixed",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": ["a", 123]}],
        error_code=UNSET_ARRAY_ELEMENT_TYPE_ERROR,
        msg=(
            "$unset array with mixed string and non-string"
            " elements should produce an array element type error"
        ),
    ),
]

# Property [Empty Array Error]: an empty array specification produces an
# empty array error.
UNSET_EMPTY_ARRAY_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_array_error",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$unset": []}],
        error_code=UNSET_EMPTY_ARRAY_ERROR,
        msg="$unset with an empty array should produce an empty array error",
    ),
]

UNSET_SPEC_ERROR_TESTS = (
    UNSET_SPEC_TYPE_ERROR_TESTS
    + UNSET_ARRAY_ELEMENT_TYPE_ERROR_TESTS
    + UNSET_EMPTY_ARRAY_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNSET_SPEC_ERROR_TESTS))
def test_unset_spec_errors(collection: Any, test_case: StageTestCase) -> None:
    """Test $unset stage specification errors."""
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
        ignore_doc_order=True,
    )
