"""
Tests for $ne input handling.

Covers argument validation (error cases), field references, $literal keyword,
return type verification, and nested $ne expressions.
Combination tests with other operators are in
/comparisons/test_expressions_combination_comparison_operators.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_args",
        expression={"$ne": []},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for empty arguments",
    ),
    ExpressionTestCase(
        "single_arg",
        expression={"$ne": ["$a"]},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for single argument",
    ),
    ExpressionTestCase(
        "non_array_int",
        expression={"$ne": 1},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array int argument",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$ne": "string"},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array string argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$ne": ["$a", "$b", "$c"]},
        doc={"a": 1, "b": 2, "c": 3},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for three arguments",
    ),
]


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref",
        expression={"$ne": ["$qty", 250]},
        doc={"qty": 250},
        expected=False,
        msg="Field reference equals literal",
    ),
    ExpressionTestCase(
        "field_ref_mismatch",
        expression={"$ne": ["$qty", 250]},
        doc={"qty": 200},
        expected=True,
        msg="Field reference not equal to different literal",
    ),
    ExpressionTestCase(
        "literal_keyword_vs_field_ref",
        expression={"$ne": [{"$literal": "$a"}, "$a"]},
        doc={"a": 42},
        expected=True,
        msg="$literal produces raw string '$a', field ref resolves to 42",
    ),
]


RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_true",
        expression={"$type": {"$ne": [1, 2]}},
        doc={"a": 1},
        expected="bool",
        msg="$ne true should return BSON bool type",
    ),
    ExpressionTestCase(
        "return_type_false",
        expression={"$type": {"$ne": [1, 1]}},
        doc={"a": 1},
        expected="bool",
        msg="$ne false should return BSON bool type",
    ),
]


NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_inner_true_vs_true",
        expression={"$ne": [{"$ne": [1, 2]}, True]},
        doc={"a": 1},
        expected=False,
        msg="Nested $ne true equals true",
    ),
    ExpressionTestCase(
        "nested_inner_false_vs_false",
        expression={"$ne": [{"$ne": [1, 1]}, False]},
        doc={"a": 1},
        expected=False,
        msg="Nested $ne false equals false",
    ),
    ExpressionTestCase(
        "nested_both_true",
        expression={"$ne": [{"$ne": [1, 2]}, {"$ne": [3, 4]}]},
        doc={"a": 1},
        expected=False,
        msg="Both nested $ne true",
    ),
    ExpressionTestCase(
        "nested_both_false",
        expression={"$ne": [{"$ne": [1, 1]}, {"$ne": [2, 2]}]},
        doc={"a": 1},
        expected=False,
        msg="Both nested $ne false",
    ),
    ExpressionTestCase(
        "nested_true_vs_false",
        expression={"$ne": [{"$ne": [1, 2]}, {"$ne": [1, 1]}]},
        doc={"a": 1},
        expected=True,
        msg="Nested true vs false",
    ),
]

ALL_TESTS = ARG_TESTS + FIELD_REF_TESTS + RETURN_TYPE_TESTS + NESTED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_ne_input_handling(collection, test):
    """Test $ne argument validation, field references, return type, and nesting."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
