"""Tests for $merge whenMatched string-mode behavior."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    DUPLICATE_KEY_ERROR,
    IMMUTABLE_FIELD_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [whenMatched Merge Shallow]: whenMatched "merge" performs a
# shallow merge where source fields are added to or replace fields in the
# target; nested objects and arrays are replaced entirely, not deep-merged.
MERGE_WHEN_MATCHED_MERGE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "merge_adds_new_field",
        target_docs=[{"_id": 1, "a": 10}],
        docs=[{"_id": 1, "b": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected=[{"_id": 1, "a": 10, "b": 20}],
        msg="$merge merge should add new fields from source to target",
    ),
    MergeTestCase(
        "merge_replaces_existing_field",
        target_docs=[{"_id": 1, "a": 10, "b": 2}],
        docs=[{"_id": 1, "a": 99}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected=[{"_id": 1, "a": 99, "b": 2}],
        msg="$merge merge should replace existing fields with source values",
    ),
    MergeTestCase(
        "merge_nested_object_replaced",
        target_docs=[{"_id": 1, "nested": {"x": 1, "y": 2}}],
        docs=[{"_id": 1, "nested": {"z": 3}}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected=[{"_id": 1, "nested": {"z": 3}}],
        msg="$merge merge should replace nested objects entirely, not deep-merge",
    ),
    MergeTestCase(
        "merge_array_replaced",
        target_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        docs=[{"_id": 1, "arr": [4]}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected=[{"_id": 1, "arr": [4]}],
        msg="$merge merge should replace arrays entirely, not concatenate or deep-merge",
    ),
    MergeTestCase(
        "merge_field_order_target_first",
        target_docs=[{"_id": 1, "z": 1, "a": 2}],
        docs=[{"_id": 1, "b": 3, "a": 99}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "merge"}}],
        expected=[{"_id": 1, "z": 1, "a": 99, "b": 3}],
        msg="$merge merge should preserve target field order and append new source fields",
    ),
]

# Property [whenMatched keepExisting]: whenMatched "keepExisting" keeps the
# existing target document unchanged regardless of the source document content.
MERGE_WHEN_MATCHED_KEEP_EXISTING_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "keep_existing_ignores_source_fields",
        target_docs=[{"_id": 1, "a": 10}],
        docs=[{"_id": 1, "b": 20, "c": 30}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "keepExisting"}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge keepExisting should ignore all source fields",
    ),
    MergeTestCase(
        "keep_existing_preserves_all_target_fields",
        target_docs=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        docs=[{"_id": 1, "a": 99, "x": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "keepExisting"}}],
        expected=[{"_id": 1, "a": 10, "b": 20, "c": 30}],
        msg="$merge keepExisting should preserve all existing target fields unchanged",
    ),
    MergeTestCase(
        "keep_existing_unmatched_inserted",
        target_docs=[{"_id": 1, "a": 10}],
        docs=[{"_id": 1, "a": 99}, {"_id": 2, "b": 50}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "keepExisting"}}],
        expected=[{"_id": 1, "a": 10}, {"_id": 2, "b": 50}],
        msg="$merge keepExisting should still insert unmatched documents",
    ),
]

# Property [whenMatched Replace]: whenMatched "replace" replaces the
# existing document entirely with the source document, preserving only the
# target's _id field.
MERGE_WHEN_MATCHED_REPLACE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "replace_removes_target_fields",
        target_docs=[{"_id": 1, "a": 10, "c": 30}],
        docs=[{"_id": 1, "b": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected=[{"_id": 1, "b": 20}],
        msg="$merge replace should remove all target fields not in the source document",
    ),
    MergeTestCase(
        "replace_preserves_target_id",
        target_docs=[{"_id": 1, "a": 10}],
        docs=[{"_id": 1, "x": 99}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "replace"}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge replace should preserve the _id from the target document",
    ),
]

# Property [_id Immutability Errors]: any whenMatched mode that would change
# an existing document's _id value produces IMMUTABLE_FIELD_ERROR.
MERGE_ID_IMMUTABILITY_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "id_immut_replace",
        target_docs=[{"_id": 1, "key": "a", "val": "old"}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 2, "key": "a", "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "replace"}}],
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$merge should reject replace when source _id differs from matched target _id",
    ),
    MergeTestCase(
        "id_immut_merge",
        target_docs=[{"_id": 1, "key": "a", "val": "old"}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 2, "key": "a", "val": "new"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$merge should reject merge when source _id differs from matched target _id",
    ),
    MergeTestCase(
        "id_immut_pipeline_replace_with",
        target_docs=[{"_id": 1, "key": "a", "val": "old"}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": "a", "val": "new"}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "on": "key",
                    "whenMatched": [{"$replaceWith": {"_id": 999, "key": "a", "val": "replaced"}}],
                }
            }
        ],
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$merge should reject pipeline $replaceWith producing a different _id",
    ),
    MergeTestCase(
        "id_immut_pipeline_set",
        target_docs=[{"_id": 1, "key": "a", "val": "old"}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": "a", "val": "new"}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "on": "key",
                    "whenMatched": [{"$set": {"_id": 999}}],
                }
            }
        ],
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$merge should reject pipeline $set that changes _id to a different value",
    ),
]

# Property [whenMatched Fail Error]: when a results document matches an
# existing document and whenMatched is "fail", the aggregation fails with a
# duplicate key error.
MERGE_WHEN_MATCHED_FAIL_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "fail_single_match_errors",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "fail"}}],
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge fail should produce duplicate key error when source matches target",
    ),
    MergeTestCase(
        "fail_with_unmatched_still_errors",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "fail"}}],
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge fail should error even when some source documents are unmatched",
    ),
]

# Property [whenMatched Fail No Rollback]: documents written before the
# failure (unmatched inserts) are not rolled back.
MERGE_WHEN_MATCHED_FAIL_NO_ROLLBACK_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "when_matched_fail_no_rollback",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "fail"}}],
        expected=[{"_id": 1, "x": 99}, {"_id": 2, "a": 20}],
        msg="$merge fail should not roll back unmatched documents inserted before the error",
    ),
]

MERGE_WHEN_MATCHED_CASES = (
    MERGE_WHEN_MATCHED_MERGE_TESTS
    + MERGE_WHEN_MATCHED_KEEP_EXISTING_TESTS
    + MERGE_WHEN_MATCHED_REPLACE_TESTS
    + MERGE_ID_IMMUTABILITY_ERROR_TESTS
    + MERGE_WHEN_MATCHED_FAIL_ERROR_TESTS
    + MERGE_WHEN_MATCHED_FAIL_NO_ROLLBACK_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_WHEN_MATCHED_CASES))
def test_stages_merge_when_matched(collection, test_case: MergeTestCase):
    """Test $merge whenMatched string-mode behavior and _id immutability."""
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
