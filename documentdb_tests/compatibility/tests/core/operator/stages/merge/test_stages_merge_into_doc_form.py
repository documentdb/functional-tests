"""Tests for $merge into document-form field validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    MERGE_INTO_COLL_NULL_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
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

# Property [into Document Form coll Type Strictness]: in the document form of
# into, the coll field only accepts string; all other BSON types produce
# TYPE_MISMATCH_ERROR.
MERGE_INTO_COLL_TYPE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"into_coll_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": {"coll": val}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$merge should reject {tid} for the coll field in document form",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["target"]),
        ("object", {"x": 1}),
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

# Property [into Document Form db Type Strictness]: in the document form of
# into, the db field accepts string and null; all other BSON types produce
# TYPE_MISMATCH_ERROR.
MERGE_INTO_DB_TYPE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"into_db_type_{tid}",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": {"db": val, "coll": "target"}}}],
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"$merge should reject {tid} for the db field in document form",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(123)),
        ("double", 1.5),
        ("decimal128", DECIMAL128_ONE_AND_HALF),
        ("bool", True),
        ("array", ["test"]),
        ("object", {"x": 1}),
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

# Property [into Document Form coll Null Error]: coll: null produces
# MERGE_INTO_COLL_NULL_ERROR rather than a type error.
MERGE_INTO_COLL_NULL_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "into_coll_null",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": {"coll": None}}}],
        error_code=MERGE_INTO_COLL_NULL_ERROR,
        msg="$merge should reject coll: null with a specific null/undefined error",
    ),
]

# Property [into Document Form Structural Validation Errors]: unknown fields
# in the document form of into produce an unrecognized field error.
MERGE_INTO_DOC_FORM_STRUCTURAL_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "into_struct_unknown_field",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": {"coll": "target", "extra": "x"}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$merge should reject unknown fields in the into document form",
    ),
    MergeTestCase(
        "into_struct_multiple_unknown_fields",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": {"coll": "target", "db": "test", "foo": 1, "bar": 2}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$merge should reject documents with multiple unknown fields",
    ),
    MergeTestCase(
        "into_struct_only_unknown_fields",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": {"$literal": "target"}}}],
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="$merge should treat {$literal: 'target'} as document form with unknown fields",
    ),
]

MERGE_INTO_DOC_FORM_CASES = (
    MERGE_INTO_COLL_TYPE_TESTS
    + MERGE_INTO_DB_TYPE_TESTS
    + MERGE_INTO_COLL_NULL_TESTS
    + MERGE_INTO_DOC_FORM_STRUCTURAL_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_INTO_DOC_FORM_CASES))
def test_stages_merge_into_doc_form(collection, test_case: MergeTestCase):
    """Test $merge into document-form field validation."""
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
