"""Tests for $merge default, form, and null/missing parameter behavior."""

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
    MERGE_INTO_TYPE_ERROR,
    MERGE_ON_TYPE_ERROR,
    MERGE_WHEN_MATCHED_TYPE_ERROR,
    MISSING_FIELD_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [Default Parameter Behavior]: when parameters are omitted, $merge
# uses _id for matching, shallow-merges matched documents, and inserts
# unmatched documents. The simplified form {$merge: <string>} is equivalent
# to {$merge: {into: <string>}} with all other parameters at their defaults.
MERGE_DEFAULTS_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "simplified_matches_document_form",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": TARGET}],
        expected=[{"_id": 1, "x": 99, "a": 10}],
        msg="$merge simplified form should merge fields into existing documents",
    ),
    MergeTestCase(
        "on_default_matches_by_id",
        target_docs=[{"_id": 1, "old": True}, {"_id": 2, "old": True}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET}}],
        expected=[{"_id": 1, "old": True, "a": 10}, {"_id": 2, "old": True, "a": 20}],
        msg="$merge should match on _id by default when on is omitted",
    ),
    MergeTestCase(
        "when_matched_default_merges_fields",
        target_docs=[{"_id": 1, "a": 5, "c": 30}],
        docs=[{"_id": 1, "a": 10, "b": 20}],
        pipeline=[{"$merge": {"into": TARGET}}],
        expected=[{"_id": 1, "a": 10, "c": 30, "b": 20}],
        msg="$merge should shallow-merge source fields into target when whenMatched is omitted",
    ),
    MergeTestCase(
        "when_not_matched_default_inserts",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 3, "a": 30}],
        pipeline=[{"$merge": {"into": TARGET}}],
        expected=[{"_id": 1, "x": 99}, {"_id": 3, "a": 30}],
        msg="$merge should insert unmatched documents when whenNotMatched is omitted",
    ),
]

# Property [Null and Missing Behavior]: null or missing values for optional
# parameters are treated as unspecified (defaults apply).
MERGE_NULL_MISSING_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "null_let_null_treated_as_unspecified",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "let": None,
                    "whenMatched": [{"$set": {"from_new": "$$new.a"}}],
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "from_new": 10}],
        msg="$merge should treat let: null as unspecified with $$new still available",
    ),
    MergeTestCase(
        "null_when_not_matched_null_inserts",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 2, "a": 20}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": None}}],
        expected=[{"_id": 1, "x": 99}, {"_id": 2, "a": 20}],
        msg="$merge should treat whenNotMatched: null as the default insert behavior",
    ),
    MergeTestCase(
        "null_db_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": {"db": None, "coll": TARGET}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge should use source database when db is null in document form",
    ),
    MergeTestCase(
        "null_db_empty_string",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": {"db": "", "coll": TARGET}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge should use source database when db is empty string in document form",
    ),
    MergeTestCase(
        "null_db_omitted",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": {"coll": TARGET}}}],
        expected=[{"_id": 1, "a": 10}],
        msg="$merge should use source database when db is omitted in document form",
    ),
]

# Property [Null and Missing Error Cases]: into: null, into omitted, on: null,
# and whenMatched: null produce errors rather than being treated as defaults.
MERGE_NULL_MISSING_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "null_err_into_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": None}}],
        error_code=MERGE_INTO_TYPE_ERROR,
        msg="$merge should reject into: null as an invalid type",
    ),
    MergeTestCase(
        "null_err_into_omitted",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {}}],
        error_code=MISSING_FIELD_ERROR,
        msg="$merge should reject a spec with the into field omitted entirely",
    ),
    MergeTestCase(
        "null_err_on_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "on": None}}],
        error_code=MERGE_ON_TYPE_ERROR,
        msg="$merge should reject on: null rather than treating it as default",
    ),
    MergeTestCase(
        "null_err_when_matched_null",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": None}}],
        error_code=MERGE_WHEN_MATCHED_TYPE_ERROR,
        msg="$merge should reject whenMatched: null rather than treating it as default",
    ),
]

MERGE_DEFAULTS_CASES = (
    MERGE_DEFAULTS_TESTS + MERGE_NULL_MISSING_TESTS + MERGE_NULL_MISSING_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_DEFAULTS_CASES))
def test_stages_merge_defaults(collection, test_case: MergeTestCase):
    """Test $merge default, simplified-form, and null/missing parameter behavior."""
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
