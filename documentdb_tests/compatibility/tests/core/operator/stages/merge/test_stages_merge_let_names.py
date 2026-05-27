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

# Property [let Variable Name Validation]: variable names follow identifier
# rules for the first character and subsequent characters, with acceptance of
# long names.
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
    MergeTestCase(
        "varname_nbsp_start",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$\u00a0var"}}],
                    "let": {"\u00a0var": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept non-breaking space (U+00A0) as first character",
    ),
    MergeTestCase(
        "varname_cjk_start",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$\u4e16\u754c"}}],
                    "let": {"\u4e16\u754c": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept CJK characters as variable name",
    ),
    MergeTestCase(
        "varname_mixed_subsequent_chars",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$aBC_123"}}],
                    "let": {"aBC_123": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept uppercase, digits, and underscore as subsequent characters",
    ),
    MergeTestCase(
        "varname_non_ascii_subsequent",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$a\u4e16\u754c"}}],
                    "let": {"a\u4e16\u754c": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept non-ASCII Unicode as subsequent characters",
    ),
    MergeTestCase(
        "varname_current_uppercase",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$CURRENT"}}],
                    "let": {"CURRENT": "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept CURRENT as a special-cased uppercase variable name",
    ),
    MergeTestCase(
        "varname_long_10000_chars",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$" + "a" * 10_000}}],
                    "let": {"a" * 10_000: "$a"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 10}],
        msg="$merge let should accept variable names up to 10,000 characters long",
    ),
]

# Property [let Variable Name Validation Errors]: variable names that violate
# identifier rules are rejected.
MERGE_LET_VARIABLE_NAME_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "varname_err_empty",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject an empty variable name",
    ),
    MergeTestCase(
        "varname_err_dot",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"a.b": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject a dot in a variable name",
    ),
    MergeTestCase(
        "varname_err_space",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"a b": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject a space in a variable name",
    ),
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
    MergeTestCase(
        "varname_err_hyphen",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"a-b": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject a hyphen in a variable name",
    ),
    MergeTestCase(
        "varname_err_at",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"a@b": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject an at sign in a variable name",
    ),
    MergeTestCase(
        "varname_err_hash",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"a#b": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject a hash in a variable name",
    ),
    MergeTestCase(
        "varname_err_exclamation",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"a!b": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject an exclamation mark in a variable name",
    ),
    MergeTestCase(
        "varname_err_uppercase_start",
        docs=[{"_id": 1}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"x": 1}}],
                    "let": {"Abc": "$a"},
                }
            }
        ],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$merge let should reject uppercase-starting names other than CURRENT",
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
