"""Tests for $merge unique index requirements and violations."""

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
    MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [Unique Index Requirements]: a unique index covering exactly the
# on fields is required; index properties unrelated to field coverage do not
# prevent acceptance.
MERGE_UNIQUE_INDEX_REQUIREMENTS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "unique_idx_exact_fields",
        target_docs=[{"_id": 1, "key": "a", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[{"_id": 1, "key": "a", "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[{"_id": 1, "key": "a", "old": True, "val": "src"}],
        msg="$merge should accept a unique index with exactly the on fields",
    ),
    MergeTestCase(
        "unique_idx_field_order_irrelevant",
        target_docs=[{"_id": 1, "x": 10, "y": 20, "old": True}],
        target_indexes=[IndexModel([("y", 1), ("x", 1)], unique=True)],
        docs=[{"_id": 1, "x": 10, "y": 20, "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["x", "y"], "whenMatched": "merge"}}],
        expected=[{"_id": 1, "x": 10, "y": 20, "old": True, "val": "src"}],
        msg="$merge should accept a unique index regardless of field order",
    ),
    MergeTestCase(
        "unique_idx_sparse",
        target_docs=[{"_id": 1, "key": "a", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True, sparse=True)],
        docs=[{"_id": 1, "key": "a", "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[{"_id": 1, "key": "a", "old": True, "val": "src"}],
        msg="$merge should accept a sparse unique index",
    ),
    MergeTestCase(
        "unique_idx_ttl",
        target_docs=[{"_id": 1, "key": "a", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True, expireAfterSeconds=3600)],
        docs=[{"_id": 1, "key": "a", "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[{"_id": 1, "key": "a", "old": True, "val": "src"}],
        msg="$merge should accept a TTL unique index",
    ),
    MergeTestCase(
        "unique_idx_descending",
        target_docs=[{"_id": 1, "key": "a", "old": True}],
        target_indexes=[IndexModel([("key", -1)], unique=True)],
        docs=[{"_id": 1, "key": "a", "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        expected=[{"_id": 1, "key": "a", "old": True, "val": "src"}],
        msg="$merge should accept a descending unique index",
    ),
    MergeTestCase(
        "unique_idx_mixed_direction",
        target_docs=[{"_id": 1, "x": 10, "y": 20, "old": True}],
        target_indexes=[IndexModel([("x", 1), ("y", -1)], unique=True)],
        docs=[{"_id": 1, "x": 10, "y": 20, "val": "src"}],
        pipeline=[{"$merge": {"into": TARGET, "on": ["x", "y"], "whenMatched": "merge"}}],
        expected=[{"_id": 1, "x": 10, "y": 20, "old": True, "val": "src"}],
        msg="$merge should accept a mixed-direction unique index",
    ),
]

# Property [on Unique Index Requirement Errors]: an index that does not
# satisfy the unique index requirement for the on fields produces the unique
# index not found error.
MERGE_ON_UNIQUE_INDEX_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "unique_idx_err_missing",
        target_docs=[{"_id": 1, "key": "a"}],
        target_indexes=None,
        docs=[{"_id": 1, "key": "a"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge should reject on field when no unique index exists",
    ),
    MergeTestCase(
        "unique_idx_err_partial",
        target_docs=[{"_id": 1, "key": "a"}],
        target_indexes=[IndexModel([("key", 1), ("extra", 1)], unique=True)],
        docs=[{"_id": 1, "key": "a"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge should reject a partial unique index with extra keys",
    ),
    MergeTestCase(
        "unique_idx_err_text",
        target_docs=[{"_id": 1, "key": "hello"}],
        target_indexes=[IndexModel([("key", "text")])],
        docs=[{"_id": 1, "key": "hello"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge should reject a text index on the on field",
    ),
    MergeTestCase(
        "unique_idx_err_wildcard",
        target_docs=[{"_id": 1, "key": "a"}],
        target_indexes=[IndexModel([("$**", 1)])],
        docs=[{"_id": 1, "key": "a"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge should reject a wildcard index on the on field",
    ),
    MergeTestCase(
        "unique_idx_err_collation_mismatch",
        target_docs=[{"_id": 1, "key": "a"}],
        target_indexes=[
            IndexModel([("key", 1)], unique=True, collation={"locale": "en", "strength": 2})
        ],
        docs=[{"_id": 1, "key": "a"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge should reject an index with different collation than the aggregation",
    ),
]

# Property [Non-on Unique Index Violation Errors]: writing a document that
# violates a unique index other than the on index produces
# DUPLICATE_KEY_ERROR.
MERGE_NON_ON_UNIQUE_INDEX_VIOLATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "non_on_idx_insert",
        target_docs=[],
        target_indexes=[
            IndexModel([("key", 1)], unique=True),
            IndexModel([("other", 1)], unique=True),
        ],
        docs=[{"_id": 1, "key": "a", "other": "x"}, {"_id": 2, "key": "b", "other": "x"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenNotMatched": "insert"}}],
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge should produce duplicate key error when insert violates a non-on unique index",
    ),
    MergeTestCase(
        "non_on_idx_replace",
        target_docs=[
            {"_id": 1, "key": "a", "other": "original"},
            {"_id": 2, "key": "b", "other": "conflict"},
        ],
        target_indexes=[
            IndexModel([("key", 1)], unique=True),
            IndexModel([("other", 1)], unique=True),
        ],
        docs=[{"_id": 1, "key": "a", "other": "conflict"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "replace"}}],
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge should produce duplicate key error when replace violates a non-on unique index",
    ),
    MergeTestCase(
        "non_on_idx_merge",
        target_docs=[
            {"_id": 1, "key": "a", "other": "original"},
            {"_id": 2, "key": "b", "other": "conflict"},
        ],
        target_indexes=[
            IndexModel([("key", 1)], unique=True),
            IndexModel([("other", 1)], unique=True),
        ],
        docs=[{"_id": 1, "key": "a", "other": "conflict"}],
        pipeline=[{"$merge": {"into": TARGET, "on": "key", "whenMatched": "merge"}}],
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge should produce duplicate key error when merge violates a non-on unique index",
    ),
    MergeTestCase(
        "non_on_idx_pipeline",
        target_docs=[
            {"_id": 1, "key": "a", "other": "original"},
            {"_id": 2, "key": "b", "other": "conflict"},
        ],
        target_indexes=[
            IndexModel([("key", 1)], unique=True),
            IndexModel([("other", 1)], unique=True),
        ],
        docs=[{"_id": 1, "key": "a", "val": "new"}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "on": "key",
                    "whenMatched": [{"$set": {"other": "conflict"}}],
                }
            }
        ],
        error_code=DUPLICATE_KEY_ERROR,
        msg="$merge should error when pipeline update violates a non-on unique index",
    ),
]

MERGE_UNIQUE_INDEX_CASES = (
    MERGE_UNIQUE_INDEX_REQUIREMENTS_TESTS
    + MERGE_ON_UNIQUE_INDEX_ERROR_TESTS
    + MERGE_NON_ON_UNIQUE_INDEX_VIOLATION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_UNIQUE_INDEX_CASES))
def test_stages_merge_unique_index(collection, test_case: MergeTestCase):
    """Test $merge unique index requirements and violations."""
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
