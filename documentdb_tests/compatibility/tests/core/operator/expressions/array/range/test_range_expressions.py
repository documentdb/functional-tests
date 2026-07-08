"""
Expression and field path tests for $range expression.

Tests field path lookups, composite paths, system variables,
and null/missing behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    RANGE_END_NOT_NUMERIC_ERROR,
    RANGE_START_NOT_INT32_ERROR,
    RANGE_STEP_NOT_NUMERIC_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Field path lookups
# Property [Field Lookup]: $range resolves field paths in expressions.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nested_field_path",
        expression={"$range": ["$a.start", "$a.end"]},
        doc={"a": {"start": 0, "end": 3}},
        expected=[0, 1, 2],
        msg="Should resolve nested field paths",
    ),
    ExpressionTestCase(
        id="deeply_nested_field",
        expression={"$range": ["$a.b.start", "$a.b.end"]},
        doc={"a": {"b": {"start": 1, "end": 4}}},
        expected=[1, 2, 3],
        msg="Should resolve deeply nested field paths",
    ),
    ExpressionTestCase(
        id="nested_expr_start_end",
        expression={"$range": [{"$add": [1, 2]}, {"$multiply": [2, 5]}]},
        doc={"_placeholder": 1},
        expected=[3, 4, 5, 6, 7, 8, 9],
        msg="Should support nested expressions as start and end",
    ),
]

# $let and system variables
LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="let_variable",
        expression={
            "$let": {
                "vars": {"s": "$start", "e": "$end"},
                "in": {"$range": ["$$s", "$$e"]},
            }
        },
        doc={"start": 0, "end": 3},
        expected=[0, 1, 2],
        msg="Should work with $let variables",
    ),
    ExpressionTestCase(
        id="root_variable",
        expression={"$range": ["$$ROOT.start", "$$ROOT.end"]},
        doc={"_id": 1, "start": 0, "end": 3},
        expected=[0, 1, 2],
        msg="Should work with $$ROOT",
    ),
    ExpressionTestCase(
        id="current_variable",
        expression={"$range": ["$$CURRENT.start", "$$CURRENT.end"]},
        doc={"_id": 2, "start": 0, "end": 3},
        expected=[0, 1, 2],
        msg="$$CURRENT should be equivalent to field path",
    ),
    ExpressionTestCase(
        id="remove_variable",
        expression={"$range": ["$$REMOVE", 5]},
        doc={"x": 1},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$$REMOVE should error like missing field",
    ),
]

# Null/missing via expression — $range does NOT propagate null, it errors
# Property [Null/Missing Fields]: $range errors on null and missing field paths.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="missing_start_field",
        expression={"$range": ["$nonexistent", 5]},
        doc={"other": 1},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Missing start field should error",
    ),
    ExpressionTestCase(
        id="missing_end_field",
        expression={"$range": [0, "$nonexistent"]},
        doc={"other": 1},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Missing end field should error",
    ),
    ExpressionTestCase(
        id="null_start_field",
        expression={"$range": ["$a", 5]},
        doc={"a": None},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Null start field should error",
    ),
    ExpressionTestCase(
        id="null_end_field",
        expression={"$range": [0, "$a"]},
        doc={"a": None},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="Null end field should error",
    ),
    ExpressionTestCase(
        id="null_step_field",
        expression={"$range": [0, 5, "$a"]},
        doc={"a": None},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="Null step field should error",
    ),
    ExpressionTestCase(
        id="all_missing_fields",
        expression={"$range": ["$a", "$b"]},
        doc={"_placeholder": 1},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="All missing should error on start first",
    ),
    ExpressionTestCase(
        id="composite_array_path_error",
        expression={"$range": ["$a.b", 5]},
        doc={"a": [{"b": 0}, {"b": 5}]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Composite array path should error",
    ),
    ExpressionTestCase(
        id="array_index_path_error",
        expression={"$range": ["$a.0", "$a.1", "$a.2"]},
        doc={"a": [0, 5, 2]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="Array index path should error in expression context",
    ),
]

# Aggregate and test
ALL_EXPR_TESTS = FIELD_LOOKUP_TESTS + LET_TESTS + NULL_MISSING_EXPR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_range_field_paths_and_variables(collection, test):
    """Test $range with field paths, $let, system variables, and null/missing errors."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
