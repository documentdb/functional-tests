"""
Expression and field path tests for $filter expression.

Tests field path lookups, composite paths, system variables,
null/missing propagation via expressions, nested $filter, and
access to outer document fields in cond.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Field path lookups
# ---------------------------------------------------------------------------
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$filter": {"input": "$a.b", "cond": {"$gt": ["$$this", 2]}}},
        doc={"a": {"b": [1, 2, 3, 4]}},
        expected=[3, 4],
        msg="Should resolve nested field path",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$filter": {"input": "$a.b.c", "cond": True}},
        doc={"a": {"b": {"c": [10, 20]}}},
        expected=[10, 20],
        msg="Should resolve deeply nested field path",
    ),
    ExpressionTestCase(
        id="composite_array_path",
        expression={"$filter": {"input": "$a.b", "cond": {"$gt": ["$$this", 1]}}},
        doc={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expected=[2, 3],
        msg="Composite array path should resolve to array",
    ),
    ExpressionTestCase(
        id="index_path_on_object_key",
        expression={"$filter": {"input": "$a.0.b", "cond": True}},
        doc={"a": {"0": {"b": [1, 2, 3]}}},
        expected=[1, 2, 3],
        msg="Object key '0' resolves correctly",
    ),
    ExpressionTestCase(
        id="object_key_zero",
        expression={"$filter": {"input": "$a.0", "cond": True}},
        doc={"a": {"0": [1, 2, 3]}},
        expected=[1, 2, 3],
        msg="$a.0 resolves as field named '0' on object",
    ),
    ExpressionTestCase(
        id="access_outer_field",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", "$threshold"]}}},
        doc={"arr": [1, 2, 3, 4, 5], "threshold": 3},
        expected=[4, 5],
        msg="Should access outer document field in cond",
    ),
]

# ---------------------------------------------------------------------------
# $let and system variables
# ---------------------------------------------------------------------------
LET_AND_VARIABLE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={
            "$let": {
                "vars": {"arr": "$values"},
                "in": {"$filter": {"input": "$$arr", "cond": {"$gt": ["$$this", 2]}}},
            }
        },
        doc={"values": [1, 2, 3, 4]},
        expected=[3, 4],
        msg="Should work with $let variables",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$filter": {"input": "$$ROOT.values", "cond": {"$gt": ["$$this", 2]}}},
        doc={"_id": 1, "values": [1, 2, 3, 4]},
        expected=[3, 4],
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$filter": {"input": "$$CURRENT.values", "cond": {"$gt": ["$$this", 2]}}},
        doc={"_id": 2, "values": [1, 2, 3, 4]},
        expected=[3, 4],
        msg="$$CURRENT should be equivalent to field path",
    ),
]

# ---------------------------------------------------------------------------
# Null/missing via expression
# ---------------------------------------------------------------------------
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$filter": {"input": "$nonexistent", "cond": True}},
        doc={"other": 1},
        expected=None,
        msg="Missing field should return null",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$filter": {"input": "$$REMOVE", "cond": True}},
        doc={"x": 1},
        expected=None,
        msg="$$REMOVE propagates null",
    ),
]

# ---------------------------------------------------------------------------
# Nested $filter
# ---------------------------------------------------------------------------
NESTED_FILTER_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="filter_then_filter",
        expression={
            "$filter": {
                "input": {"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 1]}}},
                "cond": {"$lt": ["$$this", 5]},
            }
        },
        doc={"arr": [1, 2, 3, 4, 5, 6]},
        expected=[2, 3, 4],
        msg="Nested $filter should chain conditions",
    ),
]


# ---------------------------------------------------------------------------
# Limit with field reference
# ---------------------------------------------------------------------------
LIMIT_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="limit_from_field",
        expression={"$filter": {"input": "$arr", "cond": {"$gt": ["$$this", 0]}, "limit": "$n"}},
        doc={"arr": [1, 2, 3, 4, 5], "n": 2},
        expected=[1, 2],
        msg="Limit from field reference",
    ),
]

# ---------------------------------------------------------------------------
# Literal array input (not field path)
# ---------------------------------------------------------------------------
LITERAL_INPUT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="literal_array_input",
        expression={"$filter": {"input": [1, 2, 3, 4, 5], "cond": {"$gt": ["$$this", 3]}}},
        doc={"x": 1},
        expected=[4, 5],
        msg="Should filter literal array input",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + LET_AND_VARIABLE_TESTS
    + NULL_MISSING_EXPR_TESTS
    + NESTED_FILTER_TESTS
    + LIMIT_EXPR_TESTS
    + LITERAL_INPUT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_filter_expression(collection, test):
    """Test $filter with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
