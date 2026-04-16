"""
Tests for $switch evaluation order, short-circuit behavior, and edge cases.

Covers first-match semantics, short-circuit evaluation, large branch counts,
degenerate cases, multiple documents, and key order independence.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    SWITCH_NO_MATCH_NO_DEFAULT_ERROR,
)

# --- First match wins ---
FIRST_MATCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "first_match_wins_two_true",
        expression={
            "$switch": {
                "branches": [
                    {"case": True, "then": "first"},
                    {"case": True, "then": "second"},
                ]
            }
        },
        expected="first",
        msg="First matching branch should win",
    ),
    ExpressionTestCase(
        "second_match",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "first"},
                    {"case": True, "then": "second"},
                    {"case": True, "then": "third"},
                ]
            }
        },
        expected="second",
        msg="Second branch should match",
    ),
    ExpressionTestCase(
        "three_true_first_wins",
        expression={
            "$switch": {
                "branches": [
                    {"case": True, "then": "first"},
                    {"case": True, "then": "second"},
                    {"case": True, "then": "third"},
                ]
            }
        },
        expected="first",
        msg="First of three true branches should win",
    ),
    ExpressionTestCase(
        "only_middle_true",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "first"},
                    {"case": True, "then": "second"},
                    {"case": False, "then": "third"},
                ]
            }
        },
        expected="second",
        msg="Only middle true branch should match",
    ),
    ExpressionTestCase(
        "only_last_true",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "first"},
                    {"case": False, "then": "second"},
                    {"case": True, "then": "third"},
                ]
            }
        },
        expected="third",
        msg="Only last true branch should match",
    ),
]

# --- Short-circuit ---
SHORT_CIRCUIT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "later_case_not_evaluated",
        expression={
            "$switch": {
                "branches": [
                    {"case": True, "then": "ok"},
                    {"case": {"$gt": [{"$divide": [1, 0]}, 0]}, "then": "error"},
                ]
            }
        },
        expected="ok",
        msg="Should short-circuit and not evaluate divide by zero in later case",
    ),
    ExpressionTestCase(
        "default_evaluated_at_optimization",
        expression={
            "$switch": {"branches": [{"case": True, "then": "ok"}], "default": {"$divide": [1, 0]}}
        },
        error_code=BAD_VALUE_ERROR,
        msg="Default with divide by zero errors at optimization time",
    ),
    ExpressionTestCase(
        "default_evaluated_at_optimization_field_ref",
        expression={
            "$switch": {
                "branches": [{"case": True, "then": "ok"}],
                "default": {"$divide": ["$a", 0]},
            }
        },
        doc={"a": 1},
        expected="ok",
        msg="Default with field ref divide by zero errors at optimization time",
    ),
    ExpressionTestCase(
        "unmatched_then_not_evaluated",
        expression={
            "$switch": {"branches": [{"case": False, "then": {"$divide": [1, 0]}}], "default": "ok"}
        },
        expected="ok",
        msg="Should short-circuit and not evaluate divide by zero in unmatched then",
    ),
]

# --- Large number of branches ---
LARGE_BRANCH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "50_branches_last_matches",
        expression={
            "$switch": {
                "branches": [
                    *[{"case": False, "then": f"branch_{i}"} for i in range(49)],
                    {"case": True, "then": "last_branch"},
                ]
            }
        },
        expected="last_branch",
        msg="Last of 50 branches should match",
    ),
    ExpressionTestCase(
        "100_branches_first_matches",
        expression={
            "$switch": {
                "branches": [
                    {"case": True, "then": "first_branch"},
                    *[{"case": True, "then": f"branch_{i}"} for i in range(1, 100)],
                ]
            }
        },
        expected="first_branch",
        msg="First of 100 branches should match",
    ),
    ExpressionTestCase(
        "50_branches_none_match_default",
        expression={
            "$switch": {
                "branches": [{"case": False, "then": f"branch_{i}"} for i in range(50)],
                "default": "default_val",
            }
        },
        expected="default_val",
        msg="Default should be returned when 50 branches don't match",
    ),
]

# --- Degenerate cases ---
DEGENERATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "all_false_with_default",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "a"},
                    {"case": False, "then": "b"},
                ],
                "default": "default_val",
            }
        },
        expected="default_val",
        msg="All false branches should return default",
    ),
    ExpressionTestCase(
        "all_false_no_default_errors",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "a"},
                    {"case": False, "then": "b"},
                ]
            }
        },
        error_code=SWITCH_NO_MATCH_NO_DEFAULT_ERROR,
        msg="All false branches with no default should error",
    ),
]

# --- Key order independence ---
KEY_ORDER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "then_before_case",
        expression={"$switch": {"branches": [{"then": "matched", "case": True}]}},
        expected="matched",
        msg="Key order in branch should not matter",
    ),
    ExpressionTestCase(
        "default_before_branches",
        expression={
            "$switch": {"default": "default_val", "branches": [{"case": False, "then": "x"}]}
        },
        expected="default_val",
        msg="Key order at top level should not matter",
    ),
]

ALL_TESTS = (
    FIRST_MATCH_TESTS
    + SHORT_CIRCUIT_TESTS
    + LARGE_BRANCH_TESTS
    + DEGENERATE_TESTS
    + KEY_ORDER_TESTS
)


@pytest.mark.parametrize("test", ALL_TESTS, ids=lambda t: t.id)
def test_switch_evaluation(collection, test):
    """Test $switch evaluation order, short-circuit, and edge cases."""
    if test.doc:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    else:
        result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
