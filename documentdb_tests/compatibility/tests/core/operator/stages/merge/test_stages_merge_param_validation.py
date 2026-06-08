"""Tests for $merge mode combinations."""

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
    MERGE_UNSUPPORTED_MODE_COMBINATION_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [Invalid Mode Combinations]: certain combinations of string
# whenMatched and whenNotMatched modes produce an invalid mode combination
# error at parse time.
MERGE_INVALID_MODE_COMBINATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "invalid_combo_keep_existing_discard",
        docs=[{"_id": 1}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": "keepExisting", "whenNotMatched": "discard"}}
        ],
        error_code=MERGE_UNSUPPORTED_MODE_COMBINATION_ERROR,
        msg="$merge should reject keepExisting + discard combination",
    ),
    MergeTestCase(
        "invalid_combo_keep_existing_fail",
        docs=[{"_id": 1}],
        pipeline=[
            {"$merge": {"into": TARGET, "whenMatched": "keepExisting", "whenNotMatched": "fail"}}
        ],
        error_code=MERGE_UNSUPPORTED_MODE_COMBINATION_ERROR,
        msg="$merge should reject keepExisting + fail combination",
    ),
    MergeTestCase(
        "invalid_combo_fail_discard",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "fail", "whenNotMatched": "discard"}}],
        error_code=MERGE_UNSUPPORTED_MODE_COMBINATION_ERROR,
        msg="$merge should reject fail + discard combination",
    ),
    MergeTestCase(
        "invalid_combo_fail_fail",
        docs=[{"_id": 1}],
        pipeline=[{"$merge": {"into": TARGET, "whenMatched": "fail", "whenNotMatched": "fail"}}],
        error_code=MERGE_UNSUPPORTED_MODE_COMBINATION_ERROR,
        msg="$merge should reject fail + fail combination",
    ),
]

# Property [Pipeline whenMatched Mode Combination Exception]: when
# whenMatched is a pipeline (array), no whenNotMatched value produces an
# invalid combination error; modes that are invalid with string whenMatched
# are accepted.
MERGE_PIPELINE_VALID_COMBINATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "valid_combo_pipeline_with_discard",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"merged": True}}],
                    "whenNotMatched": "discard",
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "merged": True}],
        msg="$merge pipeline + discard should update matched and discard unmatched",
    ),
    MergeTestCase(
        "valid_combo_pipeline_with_fail_all_match",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"merged": True}}],
                    "whenNotMatched": "fail",
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "merged": True}],
        msg="$merge pipeline + fail should succeed when all documents match",
    ),
]

MERGE_PARAM_VALIDATION_CASES = (
    MERGE_INVALID_MODE_COMBINATION_TESTS + MERGE_PIPELINE_VALID_COMBINATION_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_PARAM_VALIDATION_CASES))
def test_stages_merge_param_validation(collection, test_case: MergeTestCase):
    """Test $merge mode combination validation."""
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
