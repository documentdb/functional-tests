"""Tests for $merge let whenMatched mode restriction."""

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
    MERGE_LET_WITH_STRING_MODE_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [let whenMatched Mode Restriction - Error]: let as a non-null
# document (even empty {}) with any string whenMatched mode produces the
# let-with-string-mode error.
MERGE_LET_MODE_RESTRICTION_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        f"let_mode_{let_id}_{mode_id}",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": mode,
                    "let": let_val,
                }
            }
        ],
        error_code=MERGE_LET_WITH_STRING_MODE_ERROR,
        msg=f"$merge should reject let {let_id} with whenMatched '{mode}'",
    )
    for let_id, let_val in [
        ("nonempty_doc", {"myvar": "$a"}),
        ("empty_doc", {}),
    ]
    for mode_id, mode in [
        ("merge", "merge"),
        ("replace", "replace"),
        ("keep_existing", "keepExisting"),
        ("fail", "fail"),
    ]
]

# Property [let whenMatched Mode Restriction - Null Bypass]: let: null
# bypasses the mode restriction and works with all string whenMatched modes.
MERGE_LET_MODE_RESTRICTION_NULL_BYPASS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "let_mode_null_merge",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": "merge",
                    "let": None,
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "a": 10}],
        msg="$merge should accept let: null with whenMatched 'merge'",
    ),
    MergeTestCase(
        "let_mode_null_replace",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": "replace",
                    "let": None,
                }
            }
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge should accept let: null with whenMatched 'replace'",
    ),
    MergeTestCase(
        "let_mode_null_keep_existing",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": "keepExisting",
                    "let": None,
                }
            }
        ],
        expected=[{"_id": 1, "x": 99}],
        msg="$merge should accept let: null with whenMatched 'keepExisting'",
    ),
    MergeTestCase(
        "let_mode_null_fail",
        target_docs=[],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": "fail",
                    "let": None,
                }
            }
        ],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge should accept let: null with whenMatched 'fail'",
    ),
]

# Property [let whenMatched Mode Restriction - Pipeline Bypass]: let as a
# non-null document (including empty {}) is accepted when whenMatched is a
# pipeline.
MERGE_LET_MODE_RESTRICTION_PIPELINE_BYPASS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "let_mode_empty_doc_pipeline",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"merged": True}}],
                    "let": {},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "merged": True}],
        msg="$merge should accept empty let document with pipeline whenMatched",
    ),
    MergeTestCase(
        "let_mode_nonempty_doc_pipeline",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge should accept non-empty let document with pipeline whenMatched",
    ),
]

MERGE_LET_MODE_RESTRICTION_CASES = (
    MERGE_LET_MODE_RESTRICTION_ERROR_TESTS
    + MERGE_LET_MODE_RESTRICTION_NULL_BYPASS_TESTS
    + MERGE_LET_MODE_RESTRICTION_PIPELINE_BYPASS_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_LET_MODE_RESTRICTION_CASES))
def test_stages_merge_let_mode_restriction(collection, test_case: MergeTestCase):
    """Test $merge let whenMatched mode restriction behavior."""
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
