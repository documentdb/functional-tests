"""
Tests for $switch expression types, field paths, nesting, and system variables.
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

# --- Literal tests (no doc insert needed) ---
LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "case_literal",
        expression={"$switch": {"branches": [{"case": True, "then": "yes"}], "default": "no"}},
        expected="yes",
        msg="Literal true case should match",
    ),
    ExpressionTestCase(
        "then_literal",
        expression={"$switch": {"branches": [{"case": True, "then": 42}]}},
        expected=42,
        msg="Literal then should return value",
    ),
    ExpressionTestCase(
        "default_literal",
        expression={"$switch": {"branches": [{"case": False, "then": "x"}], "default": "none"}},
        expected="none",
        msg="Literal default should return value",
    ),
    ExpressionTestCase(
        "nested_in_default",
        expression={
            "$switch": {
                "branches": [{"case": False, "then": "never"}],
                "default": {
                    "$switch": {"branches": [{"case": True, "then": "from nested default"}]}
                },
            }
        },
        expected="from nested default",
        msg="Nested $switch in default should evaluate",
    ),
]


@pytest.mark.parametrize("test", LITERAL_TESTS, ids=lambda t: t.id)
def test_switch_expression_literal(collection, test):
    """Test $switch with literal expression inputs."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# --- Insert tests (require doc) ---
INSERT_TESTS: list[ExpressionTestCase] = [
    # Case expression types
    ExpressionTestCase(
        "case_field_path",
        expression={"$switch": {"branches": [{"case": "$flag", "then": "yes"}], "default": "no"}},
        doc={"flag": True},
        expected="yes",
        msg="Field path case should resolve and match",
    ),
    ExpressionTestCase(
        "case_expression_operator",
        expression={
            "$switch": {
                "branches": [{"case": {"$gt": ["$x", 0]}, "then": "positive"}],
                "default": "non-positive",
            }
        },
        doc={"x": 5},
        expected="positive",
        msg="Expression operator case should evaluate",
    ),
    ExpressionTestCase(
        "case_nested_expression",
        expression={
            "$switch": {
                "branches": [
                    {
                        "case": {"$and": [{"$gt": ["$x", 0]}, {"$lt": ["$x", 100]}]},
                        "then": "in range",
                    }
                ],
                "default": "out of range",
            }
        },
        doc={"x": 50},
        expected="in range",
        msg="Nested expression case should evaluate",
    ),
    # Then expression types
    ExpressionTestCase(
        "then_field_path",
        expression={"$switch": {"branches": [{"case": True, "then": "$name"}]}},
        doc={"name": "Alice"},
        expected="Alice",
        msg="Field path then should resolve",
    ),
    ExpressionTestCase(
        "then_expression_operator",
        expression={"$switch": {"branches": [{"case": True, "then": {"$add": ["$x", 1]}}]}},
        doc={"x": 10},
        expected=11,
        msg="Expression operator then should evaluate",
    ),
    # Default expression types
    ExpressionTestCase(
        "default_field_path",
        expression={
            "$switch": {"branches": [{"case": False, "then": "x"}], "default": "$fallback"}
        },
        doc={"fallback": "backup"},
        expected="backup",
        msg="Field path default should resolve",
    ),
    ExpressionTestCase(
        "default_expression_operator",
        expression={
            "$switch": {
                "branches": [{"case": False, "then": "x"}],
                "default": {"$concat": ["no match for ", "$name"]},
            }
        },
        doc={"name": "Bob"},
        expected="no match for Bob",
        msg="Expression operator default should evaluate",
    ),
    # Field path resolution
    ExpressionTestCase(
        "simple_field_path",
        expression={
            "$switch": {
                "branches": [{"case": {"$eq": ["$a", 1]}, "then": "matched"}],
                "default": "no",
            }
        },
        doc={"a": 1},
        expected="matched",
        msg="Simple field path should resolve",
    ),
    ExpressionTestCase(
        "nested_field_path",
        expression={
            "$switch": {
                "branches": [{"case": {"$eq": ["$a.b", 1]}, "then": "matched"}],
                "default": "no",
            }
        },
        doc={"a": {"b": 1}},
        expected="matched",
        msg="Nested field path should resolve",
    ),
    ExpressionTestCase(
        "deep_nested_field_path",
        expression={
            "$switch": {
                "branches": [{"case": {"$eq": ["$a.b.c.d", 1]}, "then": "matched"}],
                "default": "no",
            }
        },
        doc={"a": {"b": {"c": {"d": 1}}}},
        expected="matched",
        msg="Deep nested field path should resolve",
    ),
    ExpressionTestCase(
        "then_field_path_array",
        expression={"$switch": {"branches": [{"case": True, "then": "$items.val"}]}},
        doc={"items": [{"val": 1}, {"val": 2}]},
        expected=[1, 2],
        msg="Field path should resolve to array from array-of-objects",
    ),
    # Nesting
    ExpressionTestCase(
        "nested_in_case",
        expression={
            "$switch": {
                "branches": [
                    {
                        "case": {
                            "$eq": [
                                {
                                    "$switch": {
                                        "branches": [{"case": {"$gt": ["$x", 0]}, "then": "pos"}],
                                        "default": "neg",
                                    }
                                },
                                "pos",
                            ]
                        },
                        "then": {
                            "$switch": {
                                "branches": [{"case": {"$gt": ["$x", 10]}, "then": "big positive"}],
                                "default": "small positive",
                            }
                        },
                    }
                ],
                "default": "not positive",
            }
        },
        doc={"x": 5},
        expected="small positive",
        msg="Nested $switch in case and then should evaluate",
    ),
    # System variables
    ExpressionTestCase(
        "current_in_case",
        expression={
            "$switch": {
                "branches": [{"case": {"$eq": ["$$CURRENT.x", 1]}, "then": "matched"}],
                "default": "no match",
            }
        },
        doc={"x": 1},
        expected="matched",
        msg="$$CURRENT should reference current document",
    ),
    ExpressionTestCase(
        "root_in_then",
        expression={"$switch": {"branches": [{"case": True, "then": "$$ROOT"}]}},
        doc={"_id": 1, "x": 1},
        expected={"_id": 1, "x": 1},
        msg="$$ROOT in then should return entire document",
    ),
]


@pytest.mark.parametrize("test", INSERT_TESTS, ids=lambda t: t.id)
def test_switch_expression_insert(collection, test):
    """Test $switch with field reference and document-dependent inputs."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
