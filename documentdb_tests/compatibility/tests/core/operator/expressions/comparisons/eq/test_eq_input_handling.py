"""
Tests for $eq input handling.

Covers argument validation (error cases), field references, $literal keyword,
return type verification, and nested $eq expressions.
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
        expression={"$eq": []},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for empty arguments",
    ),
    ExpressionTestCase(
        "single_arg",
        expression={"$eq": ["$a"]},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for single argument",
    ),
    ExpressionTestCase(
        "non_array_int",
        expression={"$eq": 1},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array int argument",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$eq": "string"},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array string argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$eq": ["$a", "$b", "$c"]},
        doc={"a": 1, "b": 2, "c": 3},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for three arguments",
    ),
]


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref",
        expression={"$eq": ["$qty", 250]},
        doc={"qty": 250},
        expected=True,
        msg="Field reference equals literal",
    ),
    ExpressionTestCase(
        "field_ref_mismatch",
        expression={"$eq": ["$qty", 250]},
        doc={"qty": 200},
        expected=False,
        msg="Field reference not equal to different literal",
    ),
    ExpressionTestCase(
        "literal_keyword_vs_field_ref",
        expression={"$eq": [{"$literal": "$a"}, "$a"]},
        doc={"a": 42},
        expected=False,
        msg="$literal produces raw string '$a', field ref resolves to 42",
    ),
]


RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_true",
        expression={"$type": {"$eq": [1, 1]}},
        doc={"a": 1},
        expected="bool",
        msg="$eq true should return BSON bool type",
    ),
    ExpressionTestCase(
        "return_type_false",
        expression={"$type": {"$eq": [1, 2]}},
        doc={"a": 1},
        expected="bool",
        msg="$eq false should return BSON bool type",
    ),
]


NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_inner_true_vs_true",
        expression={"$eq": [{"$eq": [1, 1]}, True]},
        doc={"a": 1},
        expected=True,
        msg="Nested $eq true equals true",
    ),
    ExpressionTestCase(
        "nested_inner_false_vs_false",
        expression={"$eq": [{"$eq": [1, 2]}, False]},
        doc={"a": 1},
        expected=True,
        msg="Nested $eq false equals false",
    ),
    ExpressionTestCase(
        "nested_both_true",
        expression={"$eq": [{"$eq": [1, 1]}, {"$eq": [2, 2]}]},
        doc={"a": 1},
        expected=True,
        msg="Both nested $eq true",
    ),
    ExpressionTestCase(
        "nested_both_false",
        expression={"$eq": [{"$eq": [1, 2]}, {"$eq": [3, 4]}]},
        doc={"a": 1},
        expected=True,
        msg="Both nested $eq false",
    ),
    ExpressionTestCase(
        "nested_true_vs_false",
        expression={"$eq": [{"$eq": [1, 1]}, {"$eq": [1, 2]}]},
        doc={"a": 1},
        expected=False,
        msg="Nested true vs false",
    ),
]

ALL_TESTS = ARG_TESTS + FIELD_REF_TESTS + RETURN_TYPE_TESTS + NESTED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_eq_input_handling(collection, test):
    """Test $eq argument validation, field references, return type, and nesting."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
