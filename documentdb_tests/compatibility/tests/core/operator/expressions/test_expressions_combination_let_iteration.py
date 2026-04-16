"""
Integration tests for $let with sibling expression operators.

Covers $let inside iteration operators ($map, $reduce, $filter), variable
shadowing by iteration operators, and $let with conditional/comparison/string
operators.
"""

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)


# ---------------------------------------------------------------------------
# $let inside $map
# ---------------------------------------------------------------------------
def test_let_inside_map(collection):
    """Test $let used inside $map 'in' expression."""
    result = execute_expression(
        collection,
        {
            "$map": {
                "input": [1, 2, 3],
                "as": "num",
                "in": {
                    "$let": {
                        "vars": {"doubled": {"$multiply": ["$$num", 2]}},
                        "in": {"$add": ["$$doubled", 1]},
                    }
                },
            }
        },
    )
    assert_expression_result(result, expected=[3, 5, 7], msg="$let inside $map should compute 2n+1")


def test_map_inside_let(collection):
    """Test $map used inside $let 'in' expression."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"offset": 10},
                "in": {
                    "$map": {
                        "input": [1, 2, 3],
                        "as": "num",
                        "in": {"$add": ["$$num", "$$offset"]},
                    }
                },
            }
        },
    )
    assert_expression_result(
        result, expected=[11, 12, 13], msg="$map inside $let should access outer variable"
    )


# ---------------------------------------------------------------------------
# $let inside $reduce
# ---------------------------------------------------------------------------
def test_let_inside_reduce(collection):
    """Test $let used inside $reduce 'in' expression."""
    result = execute_expression(
        collection,
        {
            "$reduce": {
                "input": [1, 2, 3],
                "initialValue": 0,
                "in": {
                    "$let": {
                        "vars": {"doubled": {"$multiply": ["$$this", 2]}},
                        "in": {"$add": ["$$value", "$$doubled"]},
                    }
                },
            }
        },
    )
    assert_expression_result(
        result, expected=12, msg="$let inside $reduce should sum doubled values: 2+4+6=12"
    )


# ---------------------------------------------------------------------------
# $let inside $filter
# ---------------------------------------------------------------------------
def test_let_inside_filter(collection):
    """Test $let used inside $filter 'cond' expression."""
    result = execute_expression(
        collection,
        {
            "$filter": {
                "input": [1, 2, 3, 4, 5],
                "as": "num",
                "cond": {
                    "$let": {
                        "vars": {"threshold": 3},
                        "in": {"$gt": ["$$num", "$$threshold"]},
                    }
                },
            }
        },
    )
    assert_expression_result(
        result, expected=[4, 5], msg="$let inside $filter should filter values > 3"
    )


# ---------------------------------------------------------------------------
# Variable shadowing: $let var shadowed by $reduce $$this/$$value
# ---------------------------------------------------------------------------
def test_let_var_this_shadowed_by_reduce(collection):
    """Test $let variable named 'this' is shadowed by $reduce's $$this."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"this": 999},
                "in": {
                    "$reduce": {
                        "input": [1, 2, 3],
                        "initialValue": 0,
                        "in": {"$add": ["$$value", "$$this"]},
                    }
                },
            }
        },
    )
    assert_expression_result(
        result,
        expected=6,
        msg="$reduce's $$this should shadow $let's 'this' variable: 1+2+3=6",
    )


def test_let_var_value_shadowed_by_reduce(collection):
    """Test $let variable named 'value' is shadowed by $reduce's $$value."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"value": 999},
                "in": {
                    "$reduce": {
                        "input": [10, 20],
                        "initialValue": 0,
                        "in": {"$add": ["$$value", "$$this"]},
                    }
                },
            }
        },
    )
    assert_expression_result(
        result,
        expected=30,
        msg="$reduce's $$value should shadow $let's 'value' variable: 0+10+20=30",
    )


# ---------------------------------------------------------------------------
# Variable shadowing: $let var shadowed by $map/$filter 'as'
# ---------------------------------------------------------------------------
def test_let_var_shadowed_by_map_as(collection):
    """Test $let variable shadowed by $map 'as' with same name."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"x": 999},
                "in": {
                    "$map": {
                        "input": [1, 2, 3],
                        "as": "x",
                        "in": "$$x",
                    }
                },
            }
        },
    )
    assert_expression_result(
        result, expected=[1, 2, 3], msg="$map 'as' should shadow $let variable of same name"
    )


def test_let_var_shadowed_by_filter_as(collection):
    """Test $let variable shadowed by $filter 'as' with same name."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"x": 999},
                "in": {
                    "$filter": {
                        "input": [1, 2, 3, 4],
                        "as": "x",
                        "cond": {"$gt": ["$$x", 2]},
                    }
                },
            }
        },
    )
    assert_expression_result(
        result, expected=[3, 4], msg="$filter 'as' should shadow $let variable of same name"
    )


# ---------------------------------------------------------------------------
# $let with conditional/comparison/string operators
# ---------------------------------------------------------------------------
def test_let_cond_branching_on_variable(collection):
    """Test $cond branching on a $let variable."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"flag": True},
                "in": {"$cond": ["$$flag", "yes", "no"]},
            }
        },
    )
    assert_expression_result(result, expected="yes", msg="$cond should branch on $let variable")


def test_let_eq_comparing_variables(collection):
    """Test $eq comparing two $let variables."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"a": 5, "b": 5},
                "in": {"$eq": ["$$a", "$$b"]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="$eq should compare $let variables")


def test_let_gt_comparing_variables(collection):
    """Test $gt comparing two $let variables."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"a": 10, "b": 5},
                "in": {"$gt": ["$$a", "$$b"]},
            }
        },
    )
    assert_expression_result(result, expected=True, msg="$gt should compare $let variables")


def test_let_concat_with_string_variables(collection):
    """Test $concat with $let string variables."""
    result = execute_expression(
        collection,
        {
            "$let": {
                "vars": {"first": "hello", "second": " world"},
                "in": {"$concat": ["$$first", "$$second"]},
            }
        },
    )
    assert_expression_result(
        result, expected="hello world", msg="$concat should join $let string variables"
    )
