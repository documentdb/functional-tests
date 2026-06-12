"""Tests for $merge whenNotMatched mode behavior."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    MERGE_WHEN_NOT_MATCHED_FAIL_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [whenNotMatched Insert]: unmatched documents are inserted into
# the output collection, with _id auto-generated if missing from the results.
MERGE_WHEN_NOT_MATCHED_INSERT_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "insert_unmatched_added",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "insert"}}],
        expected=[{"_id": 1, "x": 99, "a": 10}, {"_id": 2, "a": 20}],
        msg="$merge insert should add unmatched documents to the target collection",
    ),
    MergeTestCase(
        "insert_all_unmatched",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 3, "a": 30}, {"_id": 4, "a": 40}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "insert"}}],
        expected=[{"_id": 1, "x": 99}, {"_id": 3, "a": 30}, {"_id": 4, "a": 40}],
        msg="$merge insert should insert all unmatched documents",
    ),
    MergeTestCase(
        "insert_into_empty_target",
        target_docs=[],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "insert"}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge insert should insert into an empty target collection",
    ),
]

# Property [whenNotMatched Discard]: whenNotMatched "discard" silently
# drops unmatched documents; no insertion occurs.
MERGE_WHEN_NOT_MATCHED_DISCARD_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "discard_unmatched_dropped",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "discard"}}],
        expected=[{"_id": 1, "x": 99, "a": 10}],
        msg="$merge discard should drop unmatched documents and not insert them",
    ),
    MergeTestCase(
        "discard_all_unmatched",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 3, "a": 30}, {"_id": 4, "a": 40}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "discard"}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge discard should leave target unchanged when all source docs are unmatched",
    ),
    MergeTestCase(
        "discard_matched_still_merged",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": "replace", "whenNotMatched": "discard"}}
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge discard should still process matched documents normally",
    ),
]

# Property [whenNotMatched Fail No Error When All Match]: if no documents
# are unmatched (empty source or all match), whenNotMatched "fail" produces
# no error.
MERGE_WHEN_NOT_MATCHED_FAIL_NO_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "fail_all_match_no_error",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "fail"}}],
        expected=[{"_id": 1, "x": 99, "a": 10}],
        msg="$merge whenNotMatched fail should not error when all docs match",
    ),
    MergeTestCase(
        "fail_empty_source_no_error",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "fail"}}],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge whenNotMatched fail should not error when source is empty",
    ),
]

# Property [whenNotMatched Fail Error]: when a results document does not
# match any existing document and whenNotMatched is "fail", the aggregation
# fails.
MERGE_WHEN_NOT_MATCHED_FAIL_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "fail_unmatched_single_doc",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "fail"}}],
        error_code=MERGE_WHEN_NOT_MATCHED_FAIL_ERROR,
        msg="$merge whenNotMatched fail should error when source doc does not match target",
    ),
    MergeTestCase(
        "fail_unmatched_among_matched",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "fail"}}],
        error_code=MERGE_WHEN_NOT_MATCHED_FAIL_ERROR,
        msg="$merge whenNotMatched fail should error even when some docs match",
    ),
]

# Property [whenNotMatched Fail No Rollback]: documents that matched and
# were processed before the failure are not rolled back.
MERGE_WHEN_NOT_MATCHED_FAIL_NO_ROLLBACK_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "when_not_matched_fail_no_rollback",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "fail"}}],
        expected=[{"_id": 1, "x": 99, "a": 10}],
        msg="$merge whenNotMatched fail should not roll back matched docs",
    ),
]

MERGE_WHEN_NOT_MATCHED_CASES = (
    MERGE_WHEN_NOT_MATCHED_INSERT_TESTS
    + MERGE_WHEN_NOT_MATCHED_DISCARD_TESTS
    + MERGE_WHEN_NOT_MATCHED_FAIL_NO_ERROR_TESTS
    + MERGE_WHEN_NOT_MATCHED_FAIL_ERROR_TESTS
    + MERGE_WHEN_NOT_MATCHED_FAIL_NO_ROLLBACK_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_WHEN_NOT_MATCHED_CASES))
def test_stages_merge_when_not_matched(collection, test_case: MergeTestCase):
    """Test $merge whenNotMatched insert/discard/fail behavior."""
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
