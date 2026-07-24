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

# Property [Field Path Resolution]: $range resolves nested and composite field paths.
# Property [Field Lookup]: $range resolves field paths in expressions.
FIELD_LOOKUP_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_field_path",
        expression={"$range": ["$a.start", "$a.end"]},
        doc={"a": {"start": 0, "end": 3}},
        expected=[0, 1, 2],
        msg="$range should resolve nested field paths",
    ),
    ExpressionTestCase(
        "deeply_nested_field",
        expression={"$range": ["$a.b.start", "$a.b.end"]},
        doc={"a": {"b": {"start": 1, "end": 4}}},
        expected=[1, 2, 3],
        msg="$range should resolve deeply nested field paths",
    ),
    ExpressionTestCase(
        "nested_expr_start_end",
        expression={"$range": [{"$add": [1, 2]}, {"$multiply": [2, 5]}]},
        doc={"_placeholder": 1},
        expected=[3, 4, 5, 6, 7, 8, 9],
        msg="$range should support nested expressions as start and end",
    ),
]

# Property [Variables]: $range works with $let and system variables.
LET_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "let_variable",
        expression={
            "$let": {
                "vars": {"s": "$start", "e": "$end"},
                "in": {"$range": ["$$s", "$$e"]},
            }
        },
        doc={"start": 0, "end": 3},
        expected=[0, 1, 2],
        msg="$range should work with $let variables",
    ),
    ExpressionTestCase(
        "root_variable",
        expression={"$range": ["$$ROOT.start", "$$ROOT.end"]},
        doc={"_id": 1, "start": 0, "end": 3},
        expected=[0, 1, 2],
        msg="$range should work with $$ROOT",
    ),
    ExpressionTestCase(
        "current_variable",
        expression={"$range": ["$$CURRENT.start", "$$CURRENT.end"]},
        doc={"_id": 2, "start": 0, "end": 3},
        expected=[0, 1, 2],
        msg="$$CURRENT should be equivalent to field path",
    ),
    ExpressionTestCase(
        "remove_variable",
        expression={"$range": ["$$REMOVE", 5]},
        doc={"x": 1},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$$REMOVE should error like missing field",
    ),
]

# Property [Null/Missing Fields]: $range errors on null and missing field paths.
NULL_MISSING_EXPR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "missing_start_field",
        expression={"$range": ["$nonexistent", 5]},
        doc={"other": 1},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range missing start field should error",
    ),
    ExpressionTestCase(
        "missing_end_field",
        expression={"$range": [0, "$nonexistent"]},
        doc={"other": 1},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range missing end field should error",
    ),
    ExpressionTestCase(
        "null_start_field",
        expression={"$range": ["$a", 5]},
        doc={"a": None},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range null start field should error",
    ),
    ExpressionTestCase(
        "null_end_field",
        expression={"$range": [0, "$a"]},
        doc={"a": None},
        error_code=RANGE_END_NOT_NUMERIC_ERROR,
        msg="$range null end field should error",
    ),
    ExpressionTestCase(
        "null_step_field",
        expression={"$range": [0, 5, "$a"]},
        doc={"a": None},
        error_code=RANGE_STEP_NOT_NUMERIC_ERROR,
        msg="$range null step field should error",
    ),
    ExpressionTestCase(
        "all_missing_fields",
        expression={"$range": ["$a", "$b"]},
        doc={"_placeholder": 1},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range all missing should error on start first",
    ),
    ExpressionTestCase(
        "composite_array_path_error",
        expression={"$range": ["$a.b", 5]},
        doc={"a": [{"b": 0}, {"b": 5}]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range composite array path should error",
    ),
    ExpressionTestCase(
        "array_index_path_error",
        expression={"$range": ["$a.0", "$a.1", "$a.2"]},
        doc={"a": [0, 5, 2]},
        error_code=RANGE_START_NOT_INT32_ERROR,
        msg="$range array index path should error in expression context",
    ),
]

ALL_EXPR_TESTS = FIELD_LOOKUP_TESTS + LET_TESTS + NULL_MISSING_EXPR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_EXPR_TESTS))
def test_range_field_paths_and_variables(collection, test):
    """Test $range with field paths, $let, system variables, and null/missing errors."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
