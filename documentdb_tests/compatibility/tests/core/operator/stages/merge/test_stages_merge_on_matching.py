"""Tests for $merge on field matching behavior and value constraints."""

from __future__ import annotations

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.son import SON
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    IMMUTABLE_FIELD_ERROR,
    MERGE_ARRAY_ON_FIELD_ERROR,
    MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
    MERGE_SPARSE_NULL_ON_FIELD_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
)

# Property [on Field Matching Behavior]: matching uses the unique index on
# the on fields to determine whether a source document corresponds to an
# existing target document.
MERGE_ON_FIELD_MATCHING_TESTS: list[MergeTestCase] = [
    # Representative identity matching for each BSON type
    *[
        MergeTestCase(
            f"on_match_{tid}",
            target_docs=[{"_id": 1, "key": val, "old": True}],
            target_indexes=[IndexModel([("key", 1)], unique=True)],
            docs=[{"_id": 1, "key": val, "val": "src"}],
            pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
            expected=[{"_id": 1, "key": expected, "old": True, "val": "src"}],
            msg=f"$merge on field should match {tid} key values",
        )
        for tid, val, expected in [
            ("null", None, None),
            ("bool", True, True),
            ("int32", 42, 42),
            ("int64", Int64(42), Int64(42)),
            ("double", 3.14, 3.14),
            ("decimal128", Decimal128("3.14"), Decimal128("3.14")),
            ("string", "hello", "hello"),
            (
                "objectid",
                ObjectId("507f1f77bcf86cd799439011"),
                ObjectId("507f1f77bcf86cd799439011"),
            ),
            ("datetime", DATE_EPOCH, DATE_EPOCH),
            ("timestamp", Timestamp(100, 1), Timestamp(100, 1)),
            ("binary", Binary(b"\x01\x02\x03"), b"\x01\x02\x03"),
            ("regex", Regex("abc", "i"), Regex("abc", "i")),
            ("minkey", MinKey(), MinKey()),
            ("maxkey", MaxKey(), MaxKey()),
            ("object", {"a": 1, "b": 2}, {"a": 1, "b": 2}),
            ("code", Code("function(){}"), Code("function(){}")),
        ]
    ],
    # Numeric coercion: one representative cross-type match
    MergeTestCase(
        "on_numeric_coercion",
        target_docs=[{"_id": 1, "key": Int64(5), "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": 5.0, "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[{"_id": 1, "key": 5.0, "old": True, "val": "src"}],
        msg="$merge on field should match across numeric types via coercion",
    ),
    # Structural matching behavior
    MergeTestCase(
        "on_object_different_key_order_no_match",
        target_docs=[{"_id": 2, "key": SON([("a", 1), ("b", 2)]), "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": SON([("b", 2), ("a", 1)]), "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[
            {"_id": 1, "key": SON([("b", 2), ("a", 1)]), "val": "src"},
            {"_id": 2, "key": SON([("a", 1), ("b", 2)]), "old": True},
        ],
        msg="$merge on field should not match objects with different key order",
    ),
    MergeTestCase(
        "on_no_unicode_normalization",
        target_docs=[{"_id": 2, "key": "e\u0301", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": "\u00e9", "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[
            {"_id": 1, "key": "\u00e9", "val": "src"},
            {"_id": 2, "key": "e\u0301", "old": True},
        ],
        msg="$merge on field should not apply Unicode normalization during matching",
    ),
    MergeTestCase(
        "on_field_name_case_sensitive",
        target_docs=[{"_id": 2, "key": "abc", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "Key": "abc", "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[
            {"_id": 1, "key": None, "Key": "abc", "val": "src"},
            {"_id": 2, "key": "abc", "old": True},
        ],
        msg="$merge on field name matching should be case-sensitive",
    ),
    MergeTestCase(
        "on_dotted_path",
        target_docs=[{"_id": 1, "a": {"b": 42}, "old": True}],
        target_indexes=[IndexModel([("a.b", 1)], unique=True)],
        docs=[{"_id": 1, "a": {"b": 42}, "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "a.b", "whenMatched": "merge"}}],
        expected=[{"_id": 1, "a": {"b": 42}, "old": True, "val": "src"}],
        msg="$merge on field should support dotted paths for nested field matching",
    ),
    MergeTestCase(
        "on_compound_dotted_paths",
        target_docs=[{"_id": 1, "a": {"b": 1}, "c": {"d": 2}, "old": True}],
        target_indexes=[IndexModel([("a.b", 1), ("c.d", 1)], unique=True)],
        docs=[{"_id": 1, "a": {"b": 1}, "c": {"d": 2}, "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["a.b", "c.d"], "whenMatched": "merge"}}],
        expected=[{"_id": 1, "a": {"b": 1}, "c": {"d": 2}, "old": True, "val": "src"}],
        msg="$merge on field should support compound dotted paths with compound indexes",
    ),
]

# Property [on Field Value Constraints]: certain values in an on field
# produce errors at execution time rather than at parse time.
MERGE_ON_FIELD_VALUE_CONSTRAINT_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "on_value_array_error",
        target_docs=[{"_id": 99, "key": "x"}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": [1, 2, 3]}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        error_code=MERGE_ARRAY_ON_FIELD_ERROR,
        msg="$merge should reject array value in an on field at execution time",
    ),
    MergeTestCase(
        "on_value_sparse_null_error",
        target_docs=[{"_id": 99, "key": "x"}],
        target_indexes=[IndexModel([("key", 1)], unique=True, sparse=True)],
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        error_code=MERGE_SPARSE_NULL_ON_FIELD_ERROR,
        msg="$merge should reject null/missing on field with a sparse unique index",
    ),
    MergeTestCase(
        "on_value_duplicate_null_error",
        target_docs=[],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1}, {"_id": 2}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$merge should produce an immutable field error when two documents have null"
        " in the on field with a non-sparse index",
    ),
]

# Property [on Must Be _id For New Collection]: when the output collection
# does not exist, the on identifier must be _id.
MERGE_ON_NEW_COLLECTION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "on_requires_id_for_new_collection",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "on": "x"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge should reject non-_id on field when target collection does not exist",
    ),
]

MERGE_ON_MATCHING_CASES = (
    MERGE_ON_FIELD_MATCHING_TESTS
    + MERGE_ON_FIELD_VALUE_CONSTRAINT_TESTS
    + MERGE_ON_NEW_COLLECTION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_ON_MATCHING_CASES))
def test_stages_merge_on_matching(collection, test_case: MergeTestCase):
    """Test $merge on field matching behavior and value constraints."""
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
