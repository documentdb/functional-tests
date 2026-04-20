"""
Tests for $rand expression contexts and operator interactions.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_project,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.test_constants import DOUBLE_ZERO


def test_rand_nested_in_multiply(collection):
    """Test rand nested in multiply expression produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$multiply": [{"$rand": {}}, 100]}},
                "in": {"$and": [{"$gte": ["$$r", DOUBLE_ZERO]}, {"$lt": ["$$r", 100.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in [0, 100)")


def test_rand_in_object_expression(collection):
    """Test rand in object expression context."""
    result = execute_project(collection, {"result": {"a": {"$rand": {}}}})
    batch = result["cursor"]["firstBatch"]
    assertSuccess(result, batch, msg="Should produce object with rand field")


def test_rand_deep_nesting(collection):
    """Test rand deeply nested in floor and multiply produces integer in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$floor": {"$multiply": [{"$rand": {}}, 100]}}},
                "in": {"$and": [{"$gte": ["$$r", 0]}, {"$lte": ["$$r", 99]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce integer in [0, 99]")


def test_rand_multiply_zero(collection):
    """Test rand multiplied by zero should always return zero."""
    result = execute_expression(collection, {"$multiply": [{"$rand": {}}, 0]})
    assert_expression_result(result, expected=DOUBLE_ZERO, msg="Should return zero")


def test_rand_add_10(collection):
    """Test rand plus 10 produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$add": [{"$rand": {}}, 10]}},
                "in": {"$and": [{"$gte": ["$$r", 10.0]}, {"$lt": ["$$r", 11.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in [10, 11)")


def test_rand_subtract_from_one(collection):
    """Test one minus rand produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$subtract": [1, {"$rand": {}}]}},
                "in": {"$and": [{"$gt": ["$$r", DOUBLE_ZERO]}, {"$lte": ["$$r", 1.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in (0, 1]")


def test_rand_multiply_neg1(collection):
    """Test rand multiplied by negative one produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$multiply": [{"$rand": {}}, -1]}},
                "in": {"$and": [{"$gt": ["$$r", -1.0]}, {"$lte": ["$$r", DOUBLE_ZERO]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in (-1, 0]")


def test_rand_pow_zero(collection):
    """Test rand raised to power zero should return one."""
    result = execute_expression(collection, {"$pow": [{"$rand": {}}, 0]})
    assert_expression_result(result, expected=1.0, msg="Should return 1")


def test_rand_pow_one(collection):
    """Test rand raised to power one returns value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$pow": [{"$rand": {}}, 1]}},
                "in": {"$and": [{"$gte": ["$$r", DOUBLE_ZERO]}, {"$lt": ["$$r", 1.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in [0, 1)")


def test_rand_mod_one(collection):
    """Test rand mod one returns value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$mod": [{"$rand": {}}, 1]}},
                "in": {"$and": [{"$gte": ["$$r", DOUBLE_ZERO]}, {"$lt": ["$$r", 1.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in [0, 1)")


def test_rand_divide_by_two(collection):
    """Test rand divided by two produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$divide": [{"$rand": {}}, 2]}},
                "in": {"$and": [{"$gte": ["$$r", DOUBLE_ZERO]}, {"$lt": ["$$r", 0.5]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in [0, 0.5)")


# ---------------------------------------------------------------------------
# Multiple invocations with arithmetic
# ---------------------------------------------------------------------------
def test_rand_add_two_calls(collection):
    """Test adding two rand calls produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$add": [{"$rand": {}}, {"$rand": {}}]}},
                "in": {"$and": [{"$gte": ["$$r", DOUBLE_ZERO]}, {"$lt": ["$$r", 2.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in [0, 2)")


def test_rand_subtract_two_calls(collection):
    """Test subtracting two rand calls produces value in expected range."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$subtract": [{"$rand": {}}, {"$rand": {}}]}},
                "in": {"$and": [{"$gt": ["$$r", -1.0]}, {"$lt": ["$$r", 1.0]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce value in (-1, 1)")


# ---------------------------------------------------------------------------
# Conditional operators
# ---------------------------------------------------------------------------
def test_rand_cond_true_branch(collection):
    """Test rand in cond true branch returns a double."""
    result = execute_expression(
        collection,
        {"$type": {"$cond": [True, {"$rand": {}}, 0]}},
    )
    assert_expression_result(result, expected="double", msg="Should return double from true branch")


def test_rand_cond_false_branch(collection):
    """Test cond false branch skips rand and returns fallback value."""
    result = execute_expression(
        collection,
        {"$cond": [False, {"$rand": {}}, 0]},
    )
    assert_expression_result(result, expected=0, msg="Should return fallback value")


# ---------------------------------------------------------------------------
# Type operators
# ---------------------------------------------------------------------------
def test_rand_tostring(collection):
    """Test rand converted to string produces string type."""
    result = execute_expression(
        collection,
        {"$eq": [{"$type": {"$toString": {"$rand": {}}}}, "string"]},
    )
    assert_expression_result(result, expected=True, msg="Should produce string type")


def test_rand_concat(collection):
    """Test rand converted to string and concatenated produces string type."""
    result = execute_expression(
        collection,
        {"$eq": [{"$type": {"$concat": ["value: ", {"$toString": {"$rand": {}}}]}}, "string"]},
    )
    assert_expression_result(result, expected=True, msg="Should produce string type")


# ---------------------------------------------------------------------------
# $let variable binding
# ---------------------------------------------------------------------------
def test_rand_let_variable_reuse(collection):
    """Test let variable bound to rand is consistent when reused in same expression."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"r": {"$rand": {}}},
                "in": {"$eq": [{"$add": ["$$r", "$$r"]}, {"$multiply": ["$$r", 2]}]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should be consistent when reused")


def test_rand_let_multiple_vars_independent(collection):
    """Test multiple let variables bound to rand produce independent values."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"a": {"$rand": {}}, "b": {"$rand": {}}},
                "in": {"$ne": ["$$a", "$$b"]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce independent values")


# ---------------------------------------------------------------------------
# $switch
# ---------------------------------------------------------------------------
def test_rand_switch_produces_valid_result(collection):
    """Test rand in switch branches produces one of the expected string values."""
    result = execute_expression(
        collection,
        {
            "$in": [
                {
                    "$switch": {
                        "branches": [
                            {"case": {"$lt": [{"$rand": {}}, 0.33]}, "then": "low"},
                            {"case": {"$lt": [{"$rand": {}}, 0.66]}, "then": "mid"},
                        ],
                        "default": "high",
                    }
                },
                ["low", "mid", "high"],
            ]
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce one of low/mid/high")


def test_rand_filter_produces_subset(collection):
    """Test rand in filter condition produces subset of expected size."""
    result = execute_expression(
        collection,
        {
            "$lte": [
                {
                    "$size": {
                        "$filter": {
                            "input": [1, 2, 3, 4, 5],
                            "as": "x",
                            "cond": {"$lt": [{"$rand": {}}, 0.5]},
                        }
                    }
                },
                5,
            ]
        },
    )
    assert_expression_result(result, expected=True, msg="Should produce subset of size <= 5")
