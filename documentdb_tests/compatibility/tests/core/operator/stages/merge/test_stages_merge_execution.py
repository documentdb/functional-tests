"""Tests for $merge execution semantics and explain mode."""

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
    MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [Partial Failure Semantics]: each document is processed
# independently; non-failing documents succeed regardless of other failures
# and the error is reported after all documents are processed.
MERGE_PARTIAL_FAILURE_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "partial_failure_unique_violation",
        target_docs=[{"_id": 10, "key": "dup"}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[
            {"_id": 1, "key": "dup", "val": "conflict"},
            {"_id": 2, "key": "ok", "val": "good"},
        ],
        pipeline=[{"$merge": {"into": TARGET}}],
        expected=[{"_id": 2, "key": "ok", "val": "good"}, {"_id": 10, "key": "dup"}],
        msg="$merge should still write non-conflicting documents despite unique violation",
    ),
    MergeTestCase(
        "partial_failure_sorted_first",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 3, "a": 30}, {"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$merge": {"into": TARGET, "whenMatched": "fail"}},
        ],
        expected=[{"_id": 1, "x": 99}, {"_id": 2, "a": 20}, {"_id": 3, "a": 30}],
        msg="$merge should process documents after a failing one sorted first via $sort",
    ),
]

# Property [Processing Order]: when multiple source documents update the
# same target, the last one in pipeline order wins; with an explicit $sort
# before $merge, the sort order determines which update is final.
MERGE_PROCESSING_ORDER_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "processing_order_sort_asc",
        target_docs=[{"_id": 1, "key": "x", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[
            {"_id": 10, "key": "x", "val": "first"},
            {"_id": 20, "key": "x", "val": "second"},
            {"_id": 30, "key": "x", "val": "third"},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$project": {"_id": 0, "key": 1, "val": 1}},
            {"$merge": {"into": TARGET, "on": "key", "whenMatched": "replace"}},
        ],
        expected=[{"_id": 1, "key": "x", "val": "third"}],
        msg="$merge should apply the last document in ascending sort order as the final update",
    ),
    MergeTestCase(
        "processing_order_sort_desc",
        target_docs=[{"_id": 1, "key": "x", "old": True}],
        target_indexes=[IndexModel([("key", 1)], unique=True)],
        docs=[
            {"_id": 10, "key": "x", "val": "first"},
            {"_id": 20, "key": "x", "val": "second"},
            {"_id": 30, "key": "x", "val": "third"},
        ],
        pipeline=[
            {"$sort": {"_id": -1}},
            {"$project": {"_id": 0, "key": 1, "val": 1}},
            {"$merge": {"into": TARGET, "on": "key", "whenMatched": "replace"}},
        ],
        expected=[{"_id": 1, "key": "x", "val": "first"}],
        msg="$merge should apply the last document in descending sort order as the final update",
    ),
]

# Property [Explain Mode]: $merge in explain mode validates parameters
# (including the on field) without executing writes.
MERGE_EXPLAIN_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "explain_no_write",
        target_docs=[{"_id": 1, "x": 99}],
        agg_options={"explain": True},
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge in explain mode should not execute writes",
    ),
    MergeTestCase(
        "explain_validates_on_field",
        target_docs=[],
        agg_options={"explain": True},
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "on": "nonexistent_field"}}],
        error_code=MERGE_NO_MATCHING_UNIQUE_INDEX_ERROR,
        msg="$merge in explain mode should validate the on field",
    ),
]

MERGE_EXECUTION_CASES = (
    MERGE_PARTIAL_FAILURE_TESTS + MERGE_PROCESSING_ORDER_TESTS + MERGE_EXPLAIN_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_EXECUTION_CASES))
def test_stages_merge_execution(collection, test_case: MergeTestCase):
    """Test $merge partial failure, processing order, and explain semantics."""
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
