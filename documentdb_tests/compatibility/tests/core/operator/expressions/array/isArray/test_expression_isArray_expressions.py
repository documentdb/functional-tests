"""
Expression, field path, and variable tests for $isArray expression.

Tests nested expressions, field path lookups, composite paths,
null/missing handling, self-nesting, system variables,
and large input.
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

SELF_NESTING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="self_nested",
        expression={"$isArray": [{"$isArray": "$arr"}]},
        doc={"arr": [1, 2]},
        expected=False,
        msg="Inner returns bool, outer returns false",
    ),
]

# Field path lookups
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_array",
        expression={"$isArray": "$a.b"},
        doc={"a": {"b": [1, 2]}},
        expected=True,
        msg="Nested array field",
    ),
    ExpressionTestCase(
        id="deeply_nested_array",
        expression={"$isArray": "$a.b.c"},
        doc={"a": {"b": {"c": [1]}}},
        expected=True,
        msg="Deeply nested array field",
    ),
    ExpressionTestCase(
        id="numeric_index_on_object_key",
        expression={"$isArray": "$a.0.b"},
        doc={"a": {"0": {"b": [1]}}},
        expected=True,
        msg="Numeric key on object resolves to array",
    ),
]

# Composite array paths
COMPOSITE_PATH_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="composite_array_path",
        expression={"$isArray": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}]},
        expected=True,
        msg="Composite array path should resolve to array",
    ),
    ExpressionTestCase(
        id="composite_empty_array",
        expression={"$isArray": "$a.b"},
        doc={"a": []},
        expected=True,
        msg="Composite on empty array resolves to empty array",
    ),
    ExpressionTestCase(
        id="composite_three_elements",
        expression={"$isArray": "$a.b"},
        doc={"a": [{"b": 1}, {"b": 2}, {"b": 3}]},
        expected=True,
        msg="Three-element composite resolves to array",
    ),
]

# Deep composite array traversal
DEEP_COMPOSITE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="array_at_leaf",
        expression={"$isArray": "$a.b.c.d"},
        doc={"a": {"b": {"c": {"d": [1, 2, 3]}}}},
        expected=True,
        msg="Array at leaf level",
    ),
    ExpressionTestCase(
        id="array_at_c",
        expression={"$isArray": "$a.b.c.d"},
        doc={"a": {"b": {"c": [{"d": 1}]}}},
        expected=True,
        msg="Array at c level",
    ),
]

# Null and missing handling
NULL_MISSING_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_field",
        expression={"$isArray": "$nonexistent"},
        doc={"other": 1},
        expected=False,
        msg="Missing field should return false",
    ),
    ExpressionTestCase(
        id="missing_nested_partial_path",
        expression={"$isArray": "$a.b"},
        doc={"a": 1},
        expected=False,
        msg="Nested field on scalar parent returns false",
    ),
    ExpressionTestCase(
        id="missing_nested_empty_doc",
        expression={"$isArray": "$a.b"},
        doc={"x": 1},
        expected=False,
        msg="Missing nested field returns false",
    ),
]

# System variables
SYSTEM_VAR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="root_variable",
        expression={"$isArray": "$$ROOT"},
        doc={"a": 1},
        expected=False,
        msg="$$ROOT is object, returns false",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$isArray": "$$CURRENT"},
        doc={"a": 1},
        expected=False,
        msg="$$CURRENT is object, returns false",
    ),
    ExpressionTestCase(
        id="let_array_variable",
        expression={"$let": {"vars": {"x": "$arr"}, "in": {"$isArray": "$$x"}}},
        doc={"arr": [1, 2]},
        expected=True,
        msg="$let var bound to array returns true",
    ),
]

# Aggregate and test
ALL_EXPR_TESTS = (
    FIELD_LOOKUP_TESTS
    + COMPOSITE_PATH_TESTS
    + DEEP_COMPOSITE_TESTS
    + NULL_MISSING_TESTS
    + SYSTEM_VAR_TESTS
    + SELF_NESTING_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_isArray_expression(collection, test):
    """Test $isArray with field paths and expressions."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
