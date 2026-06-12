"""Tests for $merge on field type and array validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    FIELD_PATH_EMPTY_COMPONENT_ERROR,
    FIELD_PATH_EMPTY_ERROR,
    FIELD_PATH_NULL_BYTE_ERROR,
    FIELD_PATH_TRAILING_DOT_ERROR,
    MERGE_ON_ARRAY_ELEMENT_TYPE_ERROR,
    MERGE_ON_DUPLICATE_FIELDS_ERROR,
    MERGE_ON_EMPTY_ARRAY_ERROR,
    MERGE_ON_TYPE_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_ONE_AND_HALF,
)

# Property [on Type Strictness]: only string and array of strings are accepted
# for the on field; all other BSON types produce MERGE_ON_TYPE_ERROR.
MERGE_ON_TYPE_STRICTNESS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"on_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": val}}],
        error_code=MERGE_ON_TYPE_ERROR,
        msg=f"$merge should reject {tid} for the on field",
    )
    for tid, val in [
        ("null", None),
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("object", {"field": "value"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02")),
        ("regex", Regex("abc")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [on Array Element Type Strictness]: non-string elements within the
# on array produce MERGE_ON_ARRAY_ELEMENT_TYPE_ERROR.
MERGE_ON_ARRAY_ELEMENT_TYPE_TESTS: list[MergeTestCase] = [
    *[
        MergeTestCase(
            f"on_array_elem_{tid}",
            docs=[{"_id": 1}],
            pipeline=[{"$merge": {"into": TARGET, "on": [val]}}],
            error_code=MERGE_ON_ARRAY_ELEMENT_TYPE_ERROR,
            msg=f"$merge should reject {tid} element in the on array",
        )
        for tid, val in [
            ("int32", 123),
            ("int64", Int64(123)),
            ("double", 1.5),
            ("decimal128", DECIMAL128_ONE_AND_HALF),
            ("bool", True),
            ("null", None),
            ("array", ["nested"]),
            ("object", {"field": "value"}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("abc")),
            ("code", Code("function(){}")),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
    MergeTestCase(
        "on_array_elem_non_string_after_valid",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["valid", 123]}}],
        error_code=MERGE_ON_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$merge should reject non-string element even after valid string elements",
    ),
    MergeTestCase(
        "on_array_elem_non_string_before_valid",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": [123, "valid"]}}],
        error_code=MERGE_ON_ARRAY_ELEMENT_TYPE_ERROR,
        msg="$merge should reject non-string element even before valid string elements",
    ),
]

# Property [on Array Validation Errors]: the on array rejects structurally
# invalid inputs with distinct error codes.
MERGE_ON_ARRAY_VALIDATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "on_array_val_empty_array",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": []}}],
        error_code=MERGE_ON_EMPTY_ARRAY_ERROR,
        msg="$merge should reject an empty on array",
    ),
    MergeTestCase(
        "on_array_val_empty_string",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": [""]}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$merge should reject an empty string element in the on array",
    ),
    MergeTestCase(
        "on_array_val_dollar_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["$field"]}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$merge should reject a dollar-prefixed element in the on array",
    ),
    MergeTestCase(
        "on_array_val_trailing_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["field."]}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$merge should reject a trailing dot in an on array element",
    ),
    MergeTestCase(
        "on_array_val_leading_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": [".field"]}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$merge should reject a leading dot in an on array element",
    ),
    MergeTestCase(
        "on_array_val_consecutive_dots",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["a..b"]}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$merge should reject consecutive dots in an on array element",
    ),
    MergeTestCase(
        "on_array_val_null_byte",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["fie\x00ld"]}}],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$merge should reject a null byte in an on array element",
    ),
    MergeTestCase(
        "on_array_val_duplicate_fields",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["_id", "_id"]}}],
        error_code=MERGE_ON_DUPLICATE_FIELDS_ERROR,
        msg="$merge should reject duplicate fields in the on array",
    ),
]

# Property [on String Form Field Path Validation]: invalid field paths in the
# string form of on produce the same field path errors as the array form.
MERGE_ON_STRING_FORM_VALIDATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "on_string_val_empty_string",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ""}}],
        error_code=FIELD_PATH_EMPTY_ERROR,
        msg="$merge should reject an empty string in the on string form",
    ),
    MergeTestCase(
        "on_string_val_dollar_prefix",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": "$field"}}],
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="$merge should reject a dollar-prefixed on field in the string form",
    ),
    MergeTestCase(
        "on_string_val_trailing_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": "field."}}],
        error_code=FIELD_PATH_TRAILING_DOT_ERROR,
        msg="$merge should reject a trailing dot in the on string form",
    ),
    MergeTestCase(
        "on_string_val_leading_dot",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": ".field"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$merge should reject a leading dot in the on string form",
    ),
    MergeTestCase(
        "on_string_val_consecutive_dots",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": "a..b"}}],
        error_code=FIELD_PATH_EMPTY_COMPONENT_ERROR,
        msg="$merge should reject consecutive dots in the on string form",
    ),
    MergeTestCase(
        "on_string_val_null_byte",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": "fie\x00ld"}}],
        error_code=FIELD_PATH_NULL_BYTE_ERROR,
        msg="$merge should reject a null byte in the on string form",
    ),
]

MERGE_ON_VALIDATION_CASES = (
    MERGE_ON_TYPE_STRICTNESS_TESTS
    + MERGE_ON_ARRAY_ELEMENT_TYPE_TESTS
    + MERGE_ON_ARRAY_VALIDATION_TESTS
    + MERGE_ON_STRING_FORM_VALIDATION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_ON_VALIDATION_CASES))
def test_stages_merge_on_validation(collection, test_case: MergeTestCase):
    """Test $merge on field type and array validation."""
    target = test_case.prepare(collection)
    result = execute_command(collection, test_case.build_command(collection, target))
    if test_case.error_code is None:
        result = execute_command(collection, {"find": target, "filter": {}, "sort": {"_id": 1}})
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
