"""Tests for $merge let variable name validation."""

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
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)

# Property [let Variable Name Wiring]: $merge forwards let variable names to the
# let-binding mechanism, accepting valid names and rejecting invalid ones.
# Comprehensive variable-name validation is foundational and tested with the
# $let operator; these are representative wiring cases.
MERGE_LET_VARIABLE_NAME_VALID_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "varname_single_char",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$a"}}],
                    "let": {"a": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept a single lowercase character as variable name",
    ),
]

# Property [let Variable Name Validation Errors]: variable names that violate
# identifier rules are rejected.
MERGE_LET_VARIABLE_NAME_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "varname_err_dollar",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"$var": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject a dollar sign in a variable name",
    ),
]

MERGE_LET_NAMES_CASES = MERGE_LET_VARIABLE_NAME_VALID_TESTS + MERGE_LET_VARIABLE_NAME_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_LET_NAMES_CASES))
def test_stages_merge_let_names(collection, test_case: MergeTestCase):
    """Test $merge let variable name validation."""
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
