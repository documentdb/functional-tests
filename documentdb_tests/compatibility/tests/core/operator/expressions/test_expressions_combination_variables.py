"""
Combination and nesting tests for $let with other expressions.

Covers nested $let scoping/shadowing, $let variable swap, triple nesting,
$$REMOVE through $let, multi-$let projections, cross-$let variable isolation,
and $let across multiple documents.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils import (
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.error_codes import LET_UNDEFINED_VARIABLE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Nested $let scoping
# ---------------------------------------------------------------------------
NESTED_LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "vars_block_refs_outer",
        expression={
            "$let": {
                "vars": {"x": 10},
                "in": {"$let": {"vars": {"x": 20, "y": "$$x"}, "in": "$$y"}},
            }
        },
        expected=10,
        msg="Inner vars block should reference outer value, not same-block value",
    ),
    ExpressionTestCase(
        "in_sees_outer_variable",
        expression={
            "$let": {
                "vars": {"x": 10},
                "in": {"$let": {"vars": {"y": 20}, "in": {"$add": ["$$x", "$$y"]}}},
            }
        },
        expected=30,
        msg="Inner in should see outer variable not redefined in inner vars",
    ),
    ExpressionTestCase(
        "nested_inner_vars",
        expression={
            "$let": {
                "vars": {"x": 1},
                "in": {"$let": {"vars": {"y": 2}, "in": {"$add": ["$$x", "$$y"]}}},
            }
        },
        expected=3,
        msg="Inner $let should define own vars alongside outer",
    ),
    ExpressionTestCase(
        "nested_shadow",
        expression={"$let": {"vars": {"x": 1}, "in": {"$let": {"vars": {"x": 99}, "in": "$$x"}}}},
        expected=99,
        msg="Inner $let should shadow outer variable",
    ),
    ExpressionTestCase(
        "nested_no_redefine",
        expression={"$let": {"vars": {"x": 42}, "in": {"$let": {"vars": {"y": 1}, "in": "$$x"}}}},
        expected=42,
        msg="Inner $let without redefining should see outer value",
    ),
    ExpressionTestCase(
        "shadow_does_not_leak",
        expression={
            "$let": {
                "vars": {"x": 10},
                "in": {"$add": [{"$let": {"vars": {"x": 99}, "in": "$$x"}}, "$$x"]},
            }
        },
        expected=109,
        msg="Inner shadow should not leak: 99 + 10 = 109",
    ),
    ExpressionTestCase(
        "nested_scope_override_same_name",
        expression={
            "$let": {
                "vars": {"x": 1},
                "in": {"$let": {"vars": {"x": 100}, "in": {"$add": ["$$x", "$$x"]}}},
            }
        },
        expected=200,
        msg="Inner should use inner x=100: 100+100=200",
    ),
    ExpressionTestCase(
        "vars_value_is_nested_let",
        expression={
            "$let": {"vars": {"x": {"$let": {"vars": {"y": 5}, "in": "$$y"}}}, "in": "$$x"}
        },
        expected=5,
        msg="Vars value from nested $let should be 5",
    ),
    ExpressionTestCase(
        "nested_variable_swap",
        expression={
            "$let": {
                "vars": {"x": 1, "y": 2},
                "in": {
                    "$let": {"vars": {"x": "$$y", "y": "$$x"}, "in": {"$subtract": ["$$x", "$$y"]}}
                },
            }
        },
        expected=1,
        msg="Swap: x=2, y=1, 2-1=1",
    ),
    ExpressionTestCase(
        "triple_nested_innermost_shadow_wins",
        expression={
            "$let": {
                "vars": {"x": 1},
                "in": {
                    "$let": {
                        "vars": {"x": 2},
                        "in": {"$let": {"vars": {"x": 4}, "in": {"$multiply": ["$$x", 2]}}},
                    }
                },
            }
        },
        expected=8,
        msg="Innermost shadow of x should be used when all three levels redefine it",
    ),
    ExpressionTestCase(
        "triple_nested_mixed_scope_resolution",
        expression={
            "$let": {
                "vars": {"x": 1, "y": 2},
                "in": {
                    "$let": {
                        "vars": {"x": 3},
                        "in": {"$let": {"vars": {"z": 5}, "in": {"$add": ["$$z", "$$x", "$$y"]}}},
                    }
                },
            }
        },
        expected=10,
        msg="Variables resolve from correct nesting levels: "
        "shadowed, inherited, and locally defined",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NESTED_LET_TESTS))
def test_let_nested_combinations(collection, test):
    """Test nested $let scoping and shadowing behavior."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(result, expected=test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Multiple $let in same projection
# ---------------------------------------------------------------------------
def test_let_two_lets_same_projection(collection):
    """Test two separate $let expressions in same projection with same variable name."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$project": {
                        "_id": 0,
                        "a": {"$let": {"vars": {"x": 1}, "in": "$$x"}},
                        "b": {"$let": {"vars": {"x": 2}, "in": "$$x"}},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"a": 1, "b": 2}], msg="Each $let should resolve independently")


# ---------------------------------------------------------------------------
# $$REMOVE through $let
# ---------------------------------------------------------------------------
def test_let_remove_in_project(collection):
    """Test $let where in expression evaluates to $$REMOVE in $project — field removed."""
    collection.insert_one({"_id": 1, "a": 10, "b": 20})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "a": 1,
                        "b": {"$let": {"vars": {"x": 1}, "in": "$$REMOVE"}},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"a": 10}], msg="$$REMOVE should remove field from projection")


def test_let_remove_assigned_to_variable(collection):
    """Test $let with vars assigning $$REMOVE to a variable, in returns that variable."""
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$project": {
                        "_id": 0,
                        "a": 1,
                        "b": {"$let": {"vars": {"x": "$$REMOVE"}, "in": "$$x"}},
                    }
                }
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"a": 10}], msg="Variable holding $$REMOVE should remove field")


def test_let_across_multiple_documents(collection):
    """Test $let across multiple documents where field exists in some but not others."""
    collection.insert_many([{"_id": 1, "a": 10}, {"_id": 2}, {"_id": 3, "a": 30}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {"$project": {"_id": 0, "result": {"$let": {"vars": {"x": "$a"}, "in": "$$x"}}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result, [{"result": 10}, {}, {"result": 30}], msg="Missing field docs should omit result"
    )


def test_let_error_cross_let_variable_ref(collection):
    """Test $let where variable defined in one $let is referenced in sibling $let."""
    result = execute_command(
        collection,
        {
            "aggregate": 1,
            "pipeline": [
                {"$documents": [{}]},
                {
                    "$project": {
                        "_id": 0,
                        "a": {"$let": {"vars": {"x": 1}, "in": "$$x"}},
                        "b": {"$let": {"vars": {"y": 2}, "in": "$$x"}},
                    }
                },
            ],
            "cursor": {},
        },
    )
    assert_expression_result(
        result, error_code=LET_UNDEFINED_VARIABLE_ERROR, msg="Cross-$let variable ref should fail"
    )
