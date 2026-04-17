"""
Tests for $switch argument handling and error code validation.

Covers structural validation of $switch arguments: branches field,
branch objects, default field, and top-level argument format.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.error_codes import (
    SWITCH_BRANCH_NOT_OBJECT_ERROR,
    SWITCH_BRANCHES_NOT_ARRAY_ERROR,
    SWITCH_EMPTY_BRANCHES_ERROR,
    SWITCH_MISSING_CASE_ERROR,
    SWITCH_MISSING_THEN_ERROR,
    SWITCH_NO_MATCH_NO_DEFAULT_ERROR,
    SWITCH_NON_OBJECT_ARG_ERROR,
    SWITCH_UNKNOWN_BRANCH_FIELD_ERROR,
    SWITCH_UNKNOWN_TOP_LEVEL_FIELD_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# --- Non-object argument ---
NON_OBJECT_ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arg_string",
        expression={"$switch": "hello"},
        error_code=SWITCH_NON_OBJECT_ARG_ERROR,
        msg="Should error when argument is string",
    ),
    ExpressionTestCase(
        "arg_int",
        expression={"$switch": 1},
        error_code=SWITCH_NON_OBJECT_ARG_ERROR,
        msg="Should error when argument is int",
    ),
    ExpressionTestCase(
        "arg_bool_true",
        expression={"$switch": True},
        error_code=SWITCH_NON_OBJECT_ARG_ERROR,
        msg="Should error when argument is true",
    ),
    ExpressionTestCase(
        "arg_null",
        expression={"$switch": None},
        error_code=SWITCH_NON_OBJECT_ARG_ERROR,
        msg="Should error when argument is null",
    ),
    ExpressionTestCase(
        "arg_array",
        expression={"$switch": [{"branches": []}]},
        error_code=SWITCH_NON_OBJECT_ARG_ERROR,
        msg="Should error when argument is array",
    ),
]

# --- Branches not array ---
BRANCHES_NOT_ARRAY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "branches_string",
        expression={"$switch": {"branches": "not array"}},
        error_code=SWITCH_BRANCHES_NOT_ARRAY_ERROR,
        msg="Should error when branches is string",
    ),
    ExpressionTestCase(
        "branches_int",
        expression={"$switch": {"branches": 1}},
        error_code=SWITCH_BRANCHES_NOT_ARRAY_ERROR,
        msg="Should error when branches is int",
    ),
    ExpressionTestCase(
        "branches_null",
        expression={"$switch": {"branches": None}},
        error_code=SWITCH_BRANCHES_NOT_ARRAY_ERROR,
        msg="Should error when branches is null",
    ),
    ExpressionTestCase(
        "branches_object",
        expression={"$switch": {"branches": {"case": True, "then": 1}}},
        error_code=SWITCH_BRANCHES_NOT_ARRAY_ERROR,
        msg="Should error when branches is object",
    ),
]

# --- Branch element not object ---
BRANCH_NOT_OBJECT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "branch_string",
        expression={"$switch": {"branches": ["not object"]}},
        error_code=SWITCH_BRANCH_NOT_OBJECT_ERROR,
        msg="Should error when branch element is string",
    ),
    ExpressionTestCase(
        "branch_int",
        expression={"$switch": {"branches": [1]}},
        error_code=SWITCH_BRANCH_NOT_OBJECT_ERROR,
        msg="Should error when branch element is int",
    ),
    ExpressionTestCase(
        "branch_bool",
        expression={"$switch": {"branches": [True]}},
        error_code=SWITCH_BRANCH_NOT_OBJECT_ERROR,
        msg="Should error when branch element is bool",
    ),
    ExpressionTestCase(
        "branch_null",
        expression={"$switch": {"branches": [None]}},
        error_code=SWITCH_BRANCH_NOT_OBJECT_ERROR,
        msg="Should error when branch element is null",
    ),
    ExpressionTestCase(
        "branch_array",
        expression={"$switch": {"branches": [[1, 2]]}},
        error_code=SWITCH_BRANCH_NOT_OBJECT_ERROR,
        msg="Should error when branch element is array",
    ),
]

# --- Unknown branch field ---
UNKNOWN_BRANCH_FIELD_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "extra_field",
        expression={"$switch": {"branches": [{"case": True, "then": 1, "extra": 1}]}},
        error_code=SWITCH_UNKNOWN_BRANCH_FIELD_ERROR,
        msg="Should error when branch has extra field",
    ),
    ExpressionTestCase(
        "unknown_string_key",
        expression={"$switch": {"branches": [{"case": True, "then": 1, "unknown": 1}]}},
        error_code=SWITCH_UNKNOWN_BRANCH_FIELD_ERROR,
        msg="Should error when branch has unknown string key",
    ),
]

# --- Missing case ---
MISSING_CASE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_branch_object",
        expression={"$switch": {"branches": [{}]}},
        error_code=SWITCH_MISSING_CASE_ERROR,
        msg="Should error when branch is empty object",
    ),
    ExpressionTestCase(
        "branch_only_then",
        expression={"$switch": {"branches": [{"then": "value"}]}},
        error_code=SWITCH_MISSING_CASE_ERROR,
        msg="Should error when branch has only then",
    ),
]

# --- Missing then ---
MISSING_THEN_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "branch_only_case",
        expression={"$switch": {"branches": [{"case": True}]}},
        error_code=SWITCH_MISSING_THEN_ERROR,
        msg="Should error when branch has only case",
    ),
]

# --- No match without default ---
NO_MATCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_match_single",
        expression={"$switch": {"branches": [{"case": False, "then": "x"}]}},
        error_code=SWITCH_NO_MATCH_NO_DEFAULT_ERROR,
        msg="Should error when no case matches and no default",
    ),
    ExpressionTestCase(
        "no_match_multiple",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "a"},
                    {"case": False, "then": "b"},
                    {"case": False, "then": "c"},
                ]
            }
        },
        error_code=SWITCH_NO_MATCH_NO_DEFAULT_ERROR,
        msg="Should error when no case matches among multiple branches",
    ),
    ExpressionTestCase(
        "all_null_cases_no_default_errors",
        expression={
            "$switch": {
                "branches": [
                    {"case": None, "then": "a"},
                    {"case": None, "then": "b"},
                ]
            }
        },
        error_code=SWITCH_NO_MATCH_NO_DEFAULT_ERROR,
        msg="All null cases with no default should error",
    ),
]

# --- Unknown top-level argument ---
UNKNOWN_TOP_LEVEL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "unknown_top_level",
        expression={"$switch": {"branches": [{"case": True, "then": 1}], "unknown": 1}},
        error_code=SWITCH_UNKNOWN_TOP_LEVEL_FIELD_ERROR,
        msg="Should error with unknown top-level field",
    ),
    ExpressionTestCase(
        "unknown_top_level_with_default",
        expression={
            "$switch": {"branches": [{"case": True, "then": 1}], "default": "d", "unknown": 1}
        },
        error_code=SWITCH_UNKNOWN_TOP_LEVEL_FIELD_ERROR,
        msg="Should error with unknown top-level field alongside default",
    ),
]

# --- Empty/missing branches ---
EMPTY_BRANCHES_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_branches",
        expression={"$switch": {"branches": []}},
        error_code=SWITCH_EMPTY_BRANCHES_ERROR,
        msg="Should error when branches is empty array",
    ),
    ExpressionTestCase(
        "empty_object_no_branches",
        expression={"$switch": {}},
        error_code=SWITCH_EMPTY_BRANCHES_ERROR,
        msg="Should error when no branches field",
    ),
    ExpressionTestCase(
        "only_default_no_branches",
        expression={"$switch": {"default": "x"}},
        error_code=SWITCH_EMPTY_BRANCHES_ERROR,
        msg="Should error when only default, no branches",
    ),
    ExpressionTestCase(
        "empty_branches_with_default",
        expression={"$switch": {"branches": [], "default": "x"}},
        error_code=SWITCH_EMPTY_BRANCHES_ERROR,
        msg="Should error when branches empty even with default",
    ),
]

ALL_ERROR_TESTS = (
    NON_OBJECT_ARG_TESTS
    + BRANCHES_NOT_ARRAY_TESTS
    + BRANCH_NOT_OBJECT_TESTS
    + UNKNOWN_BRANCH_FIELD_TESTS
    + MISSING_CASE_TESTS
    + MISSING_THEN_TESTS
    + NO_MATCH_TESTS
    + UNKNOWN_TOP_LEVEL_TESTS
    + EMPTY_BRANCHES_TESTS
)

# --- Success cases ---
SUCCESS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_branch_no_match_default",
        expression={
            "$switch": {"branches": [{"case": False, "then": "matched"}], "default": "default_val"}
        },
        expected="default_val",
        msg="Should return default when case is false",
    ),
    ExpressionTestCase(
        "default_ignored_when_match",
        expression={
            "$switch": {"branches": [{"case": True, "then": "matched"}], "default": "default_val"}
        },
        expected="matched",
        msg="Should return then, not default, when case matches",
    ),
    ExpressionTestCase(
        "no_default_branch_matches",
        expression={"$switch": {"branches": [{"case": True, "then": "matched"}]}},
        expected="matched",
        msg="Should succeed without default when case matches",
    ),
]

ALL_TESTS = ALL_ERROR_TESTS + SUCCESS_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_switch_argument_handling(collection, test):
    """Test $switch argument validation and basic handling."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
