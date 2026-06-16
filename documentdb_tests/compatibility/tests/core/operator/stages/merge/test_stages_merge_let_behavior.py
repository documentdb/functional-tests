"""Tests for $merge let parameter behavior and errors."""

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
    LET_UNDEFINED_VARIABLE_ERROR,
    MERGE_LET_RESERVED_NEW_ERROR,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.property_checks import (
    IsType,
)

# Property [let Parameter Behavior]: let defines variables accessible in the
# whenMatched pipeline, with values evaluated as expressions in the source
# document context; let variables override aggregate-level let variables of
# the same name.
MERGE_LET_BEHAVIOR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "let_field_ref_evaluated_in_source",
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
        msg="$merge let variable should evaluate field references in source document context",
    ),
    MergeTestCase(
        "let_nested_expression",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": {"$add": ["$a", 5]}},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": 15}],
        msg="$merge let variable should accept nested expressions",
    ),
    MergeTestCase(
        "let_system_variable_now",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "$$NOW"},
                }
            }
        ],
        expected={"got": IsType("date")},
        msg="$merge let variable should accept system variables like $$NOW",
    ),
    MergeTestCase(
        "let_root_variable",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "$$ROOT"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": {"_id": 1, "a": 10}}],
        msg="$merge let variable should accept $$ROOT as a value",
    ),
    MergeTestCase(
        "let_new_set_to_root",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"from_new": "$$new.a"}}],
                    "let": {"new": "$$ROOT"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "from_new": 10}],
        msg="$merge let should accept 'new' set to exactly '$$ROOT'",
    ),
    MergeTestCase(
        "let_aggregate_level_variable_as_value",
        target_docs=[{"_id": 1, "x": 99}],
        agg_options={"let": {"aggVar": "hello"}},
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "$$aggVar"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": "hello"}],
        msg="$merge let should accept aggregate-level let variables as expression values",
    ),
    MergeTestCase(
        "let_overrides_aggregate_let",
        target_docs=[{"_id": 1, "x": 99}],
        agg_options={"let": {"myvar": "aggregate_level"}},
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "override"},
                }
            }
        ],
        expected=[{"_id": 1, "x": 99, "got": "override"}],
        msg="$merge let variables should override aggregate-level let variables of the same name",
    ),
]

# Property [let Reserved Name Errors]: setting 'new' to any value other than
# the exact string '$$ROOT' produces the reserved-name error.
MERGE_LET_RESERVED_NAME_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "let_reserved_field_ref",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$new"}}],
                    "let": {"new": "$a"},
                }
            }
        ],
        error_code=MERGE_LET_RESERVED_NEW_ERROR,
        msg="$merge let should reject 'new' set to a field reference",
    ),
    MergeTestCase(
        "let_reserved_literal_expr",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$new"}}],
                    "let": {"new": {"$literal": "$$ROOT"}},
                }
            }
        ],
        error_code=MERGE_LET_RESERVED_NEW_ERROR,
        msg="$merge let should reject 'new' set to {$literal: '$$ROOT'}",
    ),
    MergeTestCase(
        "let_reserved_case_lower",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$new"}}],
                    "let": {"new": "$$root"},
                }
            }
        ],
        error_code=MERGE_LET_RESERVED_NEW_ERROR,
        msg="$merge let should reject 'new' set to '$$root' (case-sensitive match)",
    ),
    MergeTestCase(
        "let_reserved_case_mixed",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$new"}}],
                    "let": {"new": "$$Root"},
                }
            }
        ],
        error_code=MERGE_LET_RESERVED_NEW_ERROR,
        msg="$merge let should reject 'new' set to '$$Root' (case-sensitive match)",
    ),
    MergeTestCase(
        "let_reserved_null",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$new"}}],
                    "let": {"new": None},
                }
            }
        ],
        error_code=MERGE_LET_RESERVED_NEW_ERROR,
        msg="$merge let should reject 'new' set to null",
    ),
    MergeTestCase(
        "let_reserved_expression",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$new"}}],
                    "let": {"new": {"$concat": ["$$ROOT"]}},
                }
            }
        ],
        error_code=MERGE_LET_RESERVED_NEW_ERROR,
        msg="$merge let should reject 'new' set to an expression evaluating to $$ROOT",
    ),
]

# Property [let Parameter Errors]: let variable definitions that reference
# undefined variables produce an error when the variable is accessed.
MERGE_LET_ERROR_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "let_cross_reference",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$v1"}}],
                    "let": {"v1": "$$v2", "v2": "hello"},
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$merge let should reject cross-references between variables",
    ),
    MergeTestCase(
        "let_self_reference",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$v1"}}],
                    "let": {"v1": "$$v1"},
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$merge let should reject self-references in variable definitions",
    ),
    MergeTestCase(
        "let_remove_makes_undefined",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "$$REMOVE"},
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$merge let should make variable undefined when set to $$REMOVE",
    ),
    MergeTestCase(
        "let_missing_field_makes_undefined",
        target_docs=[{"_id": 1, "x": 99}],
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {
                "$merge": {
                    "into": TARGET,
                    "whenMatched": [{"$set": {"got": "$$myvar"}}],
                    "let": {"myvar": "$nonexistent"},
                }
            }
        ],
        error_code=LET_UNDEFINED_VARIABLE_ERROR,
        msg="$merge let should make variable undefined when field reference is missing",
    ),
]

MERGE_LET_BEHAVIOR_CASES = (
    MERGE_LET_BEHAVIOR_TESTS + MERGE_LET_RESERVED_NAME_TESTS + MERGE_LET_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_LET_BEHAVIOR_CASES))
def test_stages_merge_let_behavior(collection, test_case: MergeTestCase):
    """Test $merge let parameter behavior, errors, and reserved names."""
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
