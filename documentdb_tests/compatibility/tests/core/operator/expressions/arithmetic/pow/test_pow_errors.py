"""
Error tests for $pow expression.

Covers non-numeric base/exponent rejection (empty array, empty object),
zero-base-with-negative-exponent rejection, and argument-count/
argument-shape errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
    POW_NON_NUMERIC_BASE_ERROR,
    POW_NON_NUMERIC_EXP_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

POW_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array_base",
        expression={"$pow": [[], 2]},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg="Should reject empty array base",
    ),
    ExpressionTestCase(
        "empty_object_base",
        expression={"$pow": [{}, 2]},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg="Should reject empty object base",
    ),
    ExpressionTestCase(
        "empty_array_exponent",
        expression={"$pow": [2, []]},
        error_code=POW_NON_NUMERIC_EXP_ERROR,
        msg="Should reject empty array exponent",
    ),
    ExpressionTestCase(
        "empty_object_exponent",
        expression={"$pow": [2, {}]},
        error_code=POW_NON_NUMERIC_EXP_ERROR,
        msg="Should reject empty object exponent",
    ),
    ExpressionTestCase(
        "zero_negative_exp",
        expression={"$pow": [0, -1]},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero negative exp",
    ),
    ExpressionTestCase(
        "zero_negative_exp_five",
        expression={"$pow": [0, -5]},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero negative exp five",
    ),
    ExpressionTestCase(
        "zero_fractional_negative_exp",
        expression={"$pow": [0, -0.5]},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero fractional negative exp",
    ),
    ExpressionTestCase(
        "zero_double_negative_exp",
        expression={"$pow": [0.0, -2.5]},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero double negative exp",
    ),
    ExpressionTestCase(
        "arity_zero_args",
        expression={"$pow": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $pow with zero arguments",
    ),
    ExpressionTestCase(
        "arity_one_arg",
        expression={"$pow": [5]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $pow with a single argument",
    ),
    ExpressionTestCase(
        "arity_three_args",
        expression={"$pow": [2, 3, 4]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $pow with three arguments",
    ),
    ExpressionTestCase(
        "arity_non_array",
        expression={"$pow": 5},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $pow with a non-array operand",
    ),
    ExpressionTestCase(
        "arity_array_wrapped_single_arg",
        expression={"$pow": [[2, 3]]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $pow with a single array-wrapped argument",
    ),
]


POW_INSERT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array_base",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": [], "power": 2},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg="Should reject empty array base",
    ),
    ExpressionTestCase(
        "empty_object_base",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": {}, "power": 2},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg="Should reject empty object base",
    ),
    ExpressionTestCase(
        "empty_array_exponent",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 2, "power": []},
        error_code=POW_NON_NUMERIC_EXP_ERROR,
        msg="Should reject empty array exponent",
    ),
    ExpressionTestCase(
        "empty_object_exponent",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 2, "power": {}},
        error_code=POW_NON_NUMERIC_EXP_ERROR,
        msg="Should reject empty object exponent",
    ),
    ExpressionTestCase(
        "zero_negative_exp",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 0, "power": -1},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero negative exp",
    ),
    ExpressionTestCase(
        "zero_negative_exp_five",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 0, "power": -5},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero negative exp five",
    ),
    ExpressionTestCase(
        "zero_fractional_negative_exp",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 0, "power": -0.5},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero fractional negative exp",
    ),
    ExpressionTestCase(
        "zero_double_negative_exp",
        expression={"$pow": ["$base", "$power"]},
        doc={"base": 0.0, "power": -2.5},
        error_code=POW_BASE_ZERO_EXP_NEGATIVE_ERROR,
        msg="Should reject zero double negative exp",
    ),
    ExpressionTestCase(
        "composite_array_path_base",
        expression={"$pow": ["$a.b", 2]},
        doc={"a": [{"b": 2}, {"b": 3}]},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg="Should reject base resolved from a composite array-path field lookup",
    ),
    ExpressionTestCase(
        "arity_array_wrapped_single_arg_field_refs",
        expression={"$pow": [["$x", "$y"]]},
        doc={"x": 2, "y": 3},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject $pow with a single array-wrapped argument of field refs",
    ),
    ExpressionTestCase(
        "object_base_with_field_ref_value",
        expression={"$pow": [{"a": "$x"}, 2]},
        doc={"x": 2},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg="Should reject object base containing a field-ref value",
    ),
    ExpressionTestCase(
        "array_index_path_base",
        expression={"$pow": ["$a.0.b", 2]},
        doc={"a": [{"b": 1}, {"b": 2}]},
        error_code=POW_NON_NUMERIC_BASE_ERROR,
        msg=(
            "Array-index-path field lookup ($a.0.b) resolves to an empty"
            " array (not element 0), which $pow rejects as non-numeric base"
        ),
    ),
]


@pytest.mark.parametrize("test", pytest_params(POW_LITERAL_TESTS))
def test_pow_literal(collection, test):
    """Test $pow from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(POW_INSERT_TESTS))
def test_pow_insert(collection, test):
    """Test $pow from documents"""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
