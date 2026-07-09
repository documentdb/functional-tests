"""
Expression and field path tests for $map expression.

Tests field path lookups, composite paths, system variables,
null/missing propagation via expressions, nested $map, and self-composition.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import MISSING

# Property [Field Path Resolution]: $map resolves nested and composite field paths.
# Property [Field Lookup]: $map resolves field paths in expressions.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={"$map": {"input": "$a.b", "in": {"$multiply": ["$$this", 2]}}},
        doc={"a": {"b": [1, 2, 3]}},
        expected=[2, 4, 6],
        msg="$map should resolve nested field path",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$map": {"input": "$a.b.c", "in": "$$this"}},
        doc={"a": {"b": {"c": [10, 20]}}},
        expected=[10, 20],
        msg="$map should resolve deeply nested field path",
    ),
    ExpressionTestCase(
        "composite_array_path",
        expression={"$map": {"input": "$a.b", "in": {"$multiply": ["$$this", 10]}}},
        doc={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expected=[10, 20, 30],
        msg="$map composite array path should resolve to array",
    ),
    ExpressionTestCase(
        "index_path_on_object_key",
        expression={"$map": {"input": "$a.0.b", "in": "$$this"}},
        doc={"a": {"0": {"b": [1, 2, 3]}}},
        expected=[1, 2, 3],
        msg="$map object key '0' resolves correctly",
    ),
    ExpressionTestCase(
        "object_key_zero",
        expression={"$map": {"input": "$a.0", "in": "$$this"}},
        doc={"a": {"0": [1, 2, 3]}},
        expected=[1, 2, 3],
        msg="$a.0 resolves as field named '0' on object",
    ),
    ExpressionTestCase(
        "access_outer_field",
        expression={"$map": {"input": "$arr", "in": {"$add": ["$$this", "$val"]}}},
        doc={"arr": [1, 2, 3], "val": 100},
        expected=[101, 102, 103],
        msg="$map should access outer document field in 'in' expression",
    ),
    ExpressionTestCase(
        "array_expression_input",
        expression={"$map": {"input": ["$x", "$y"], "in": {"$multiply": ["$$this", 2]}}},
        doc={"x": 1, "y": 2},
        expected=[2, 4],
        msg="$map array expression with field refs resolved",
    ),
]

# Property [Variables]: $map works with $let and system variables.
LET_AND_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "let_variable",
        expression={
            "$let": {
                "vars": {"arr": "$values"},
                "in": {"$map": {"input": "$$arr", "in": {"$add": ["$$this", 1]}}},
            }
        },
        doc={"values": [1, 2, 3]},
        expected=[2, 3, 4],
        msg="$map should work with $let variables",
    ),
    ExpressionTestCase(
        "root_variable",
        expression={"$map": {"input": "$$ROOT.values", "in": "$$this"}},
        doc={"_id": 1, "values": [10, 20]},
        expected=[10, 20],
        msg="$map should work with $$ROOT",
    ),
    ExpressionTestCase(
        "current_variable",
        expression={"$map": {"input": "$$CURRENT.values", "in": "$$this"}},
        doc={"_id": 2, "values": [10, 20]},
        expected=[10, 20],
        msg="$$CURRENT should be equivalent to field path",
    ),
]

# Property [Null/Missing Fields]: null and missing field paths produce null results.
# Property [Null/Missing Fields]: $map handles null and missing field paths.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_field",
        expression={"$map": {"input": "$nonexistent", "in": "$$this"}},
        doc={"other": 1},
        expected=None,
        msg="$map missing field should return null",
    ),
    ExpressionTestCase(
        "missing_input_type_is_null",
        expression={"$type": {"$map": {"input": "$nonexistent", "in": "$$this"}}},
        doc={"x": 1},
        expected="null",
        msg="$map missing field should produce null type",
    ),
    ExpressionTestCase(
        "remove_variable",
        expression={"$map": {"input": "$$REMOVE", "in": "$$this"}},
        doc={"x": 1},
        expected=None,
        msg="$$REMOVE propagates null",
    ),
    ExpressionTestCase(
        "missing_field_in_expression",
        expression={"$map": {"input": "$arr", "in": MISSING}},
        doc={"arr": [1, 2, 3]},
        expected=[None, None, None],
        msg="$map missing field in 'in' should produce null for each element",
    ),
]

# Property [Nested Map]: $map can be nested inside another $map.
NESTED_MAP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_map",
        expression={
            "$map": {
                "input": "$arr",
                "as": "inarr",
                "in": {
                    "$map": {
                        "input": "$$inarr",
                        "as": "num",
                        "in": {"$multiply": ["$$num", 2]},
                    }
                },
            }
        },
        doc={"arr": [[1, 2], [3, 4]]},
        expected=[[2, 4], [6, 8]],
        msg="$map nested $map should process 2D array",
    ),
]


# Property [Reduce Interaction]: $map composes correctly with $reduce scoping.
# Property [Reduce Interaction]: $map output works with $reduce.
REDUCE_INTERACTION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "map_within_reduce",
        expression={
            "$reduce": {
                "input": [4, 5, 6],
                "initialValue": [0],
                "in": {
                    "$concatArrays": ["$$value", {"$map": {"input": [1, 2, 3], "in": "$$this"}}]
                },
            }
        },
        doc={"_placeholder": 1},
        expected=[0, 1, 2, 3, 1, 2, 3, 1, 2, 3],
        msg="$map's $$this should reference $map elements, not $reduce's",
    ),
    ExpressionTestCase(
        "reduce_within_map",
        expression={
            "$map": {
                "input": [100, 50],
                "in": {
                    "$reduce": {
                        "input": [25, 25],
                        "initialValue": 1,
                        "in": {"$add": ["$$value", "$$this"]},
                    }
                },
            }
        },
        doc={"_placeholder": 1},
        expected=[51, 51],
        msg="$reduce's $$value and $$this should be scoped to $reduce",
    ),
]

# Property [System Variables]: $map works with $$ROOT and $$REMOVE.
# Property [System Variables]: $map works with $$ROOT and $$CURRENT.
SYSTEM_VAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "root_returns_full_doc",
        expression={"$map": {"input": "$arr", "in": "$$ROOT"}},
        doc={"_id": 1, "arr": [1, 2]},
        expected=[{"_id": 1, "arr": [1, 2]}, {"_id": 1, "arr": [1, 2]}],
        msg="$$ROOT should return root document for each element",
    ),
    ExpressionTestCase(
        "root_field_access",
        expression={"$map": {"input": "$arr", "in": "$$ROOT.name"}},
        doc={"_id": 1, "arr": [1, 2], "name": "test"},
        expected=["test", "test"],
        msg="$$ROOT.field should access root field for each element",
    ),
    ExpressionTestCase(
        "remove_in_cond_becomes_null",
        expression={
            "$map": {
                "input": [1, 10, 2, 20],
                "in": {"$cond": [{"$gt": ["$$this", 5]}, "$$this", "$$REMOVE"]},
            }
        },
        doc={"_placeholder": 1},
        expected=[None, 10, None, 20],
        msg="$$REMOVE as array element becomes null, does not remove element",
    ),
]


ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + LET_AND_VARIABLE_TESTS
    + NULL_MISSING_EXPR_TESTS
    + NESTED_MAP_TESTS
    + REDUCE_INTERACTION_TESTS
    + SYSTEM_VAR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_map_field_paths_and_variables(collection, test):
    """Test $map with field paths, $let, system variables, and nested composition."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
