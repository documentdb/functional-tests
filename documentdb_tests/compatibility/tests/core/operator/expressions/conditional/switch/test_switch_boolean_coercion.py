"""
Tests for $switch-specific boolean coercion behavior.

Covers multi-branch fall-through with falsy values, first-match-wins with
truthy values, and missing field coercion.
General truthy/falsy BSON type coverage is in shared/test_shared_boolean_coercion.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)

ALL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "false_vs_zero_both_falsy",
        expression={
            "$switch": {
                "branches": [
                    {"case": False, "then": "false_branch"},
                    {"case": 0, "then": "zero_branch"},
                ],
                "default": "neither",
            }
        },
        expected="neither",
        msg="Both false and 0 are falsy, should fall through to default",
    ),
    ExpressionTestCase(
        "true_vs_one_both_truthy",
        expression={
            "$switch": {
                "branches": [
                    {"case": True, "then": "true_branch"},
                    {"case": 1, "then": "one_branch"},
                ]
            }
        },
        expected="true_branch",
        msg="true is truthy, first match wins",
    ),
    ExpressionTestCase(
        "mixed_falsy_all_fall_through",
        expression={
            "$switch": {
                "branches": [
                    {"case": None, "then": "null_branch"},
                    {"case": 0, "then": "zero_branch"},
                    {"case": False, "then": "false_branch"},
                ],
                "default": "none_matched",
            }
        },
        expected="none_matched",
        msg="null, 0, and false are all falsy, should fall through to default",
    ),
    ExpressionTestCase(
        "first_truthy_after_falsy_branches",
        expression={
            "$switch": {
                "branches": [
                    {"case": 0, "then": "zero_branch"},
                    {"case": None, "then": "null_branch"},
                    {"case": 1, "then": "one_branch"},
                    {"case": "hello", "then": "string_branch"},
                ]
            }
        },
        expected="one_branch",
        msg="First truthy branch after falsy branches should win",
    ),
    ExpressionTestCase(
        "string_truthy_before_int_truthy",
        expression={
            "$switch": {
                "branches": [
                    {"case": "non-empty", "then": "string_branch"},
                    {"case": 1, "then": "int_branch"},
                ]
            }
        },
        expected="string_branch",
        msg="Non-empty string is truthy, first match wins over int 1",
    ),
    ExpressionTestCase(
        "zero_then_nonzero",
        expression={
            "$switch": {
                "branches": [
                    {"case": 0, "then": "zero_branch"},
                    {"case": 42, "then": "nonzero_branch"},
                ]
            }
        },
        expected="nonzero_branch",
        msg="0 is falsy, 42 is truthy, second branch should match",
    ),
]


@pytest.mark.parametrize("test", ALL_TESTS, ids=lambda t: t.id)
def test_switch_boolean_coercion(collection, test):
    """Test $switch-specific boolean coercion behavior."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
