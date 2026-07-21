"""
Null, missing, sign, and zero tests for $multiply expression.

Covers null/missing short-circuiting in any operand position, sign
combinations (positive/negative), zero, and negative-zero handling for
both double and Decimal128.
"""

import pytest
from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NEGATIVE_ZERO,
    MISSING,
)

MULTIPLY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_null",
        expression={"$multiply": [None]},
        expected=None,
        msg="Should return null for single null",
    ),
    ExpressionTestCase(
        "null_operand",
        expression={"$multiply": [2, None]},
        expected=None,
        msg="Should return null for null operand",
    ),
    ExpressionTestCase(
        "missing_field",
        expression={"$multiply": [2, MISSING]},
        expected=None,
        msg="Should return null for missing field",
    ),
    ExpressionTestCase(
        "null_with_multiple",
        expression={"$multiply": [2, 3, None]},
        expected=None,
        msg="Should return null for null with multiple",
    ),
    ExpressionTestCase(
        "null_in_middle",
        expression={"$multiply": [2, 3, 4, None, 5]},
        expected=None,
        msg="Should return null for null in middle",
    ),
    ExpressionTestCase(
        "all_missing",
        expression={"$multiply": [MISSING, MISSING]},
        expected=None,
        msg="Should return null for all missing",
    ),
    ExpressionTestCase(
        "null_and_string",
        expression={"$multiply": [None, "string"]},
        expected=None,
        msg="Should return null for null and string",
    ),
    ExpressionTestCase(
        "missing_and_boolean",
        expression={"$multiply": [MISSING, True]},
        expected=None,
        msg="Should return null for missing and boolean",
    ),
    ExpressionTestCase(
        "two_nulls",
        expression={"$multiply": [None, None]},
        expected=None,
        msg="Should return null for two nulls",
    ),
    ExpressionTestCase(
        "null_with_invalid",
        expression={"$multiply": [2, None, "string"]},
        expected=None,
        msg="Should return null for null with invalid",
    ),
    ExpressionTestCase(
        "negative_positive",
        expression={"$multiply": [-5, 3]},
        expected=-15,
        msg="Should handle negative positive",
    ),
    ExpressionTestCase(
        "both_negative",
        expression={"$multiply": [-10, -20]},
        expected=200,
        msg="Should handle both negative",
    ),
    ExpressionTestCase(
        "zero_multiply",
        expression={"$multiply": [0, 5]},
        expected=0,
        msg="Should handle zero multiply",
    ),
    ExpressionTestCase(
        "zero_negative_zero",
        expression={"$multiply": [0, -0.0]},
        expected=-0.0,
        msg="Should handle zero negative zero",
    ),
    ExpressionTestCase(
        "single_negative_zero",
        expression={"$multiply": [-0.0]},
        expected=-0.0,
        msg="Should handle single negative zero",
    ),
    ExpressionTestCase(
        "zero_in_middle",
        expression={"$multiply": [5, 0, 10]},
        expected=0,
        msg="Should handle zero in middle",
    ),
    ExpressionTestCase(
        "decimal_negative_zero_times_positive",
        expression={"$multiply": [DECIMAL128_NEGATIVE_ZERO, 5]},
        expected=DECIMAL128_NEGATIVE_ZERO,
        msg="Should handle decimal negative zero times positive",
    ),
    ExpressionTestCase(
        "decimal_negative_zero_times_negative",
        expression={"$multiply": [DECIMAL128_NEGATIVE_ZERO, -5]},
        expected=Decimal128("0"),
        msg="Should handle decimal negative zero times negative",
    ),
]


MULTIPLY_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_null",
        expression={"$multiply": ["$val0"]},
        doc={"val0": None},
        expected=None,
        msg="Should return null for single null",
    ),
    ExpressionTestCase(
        "null_operand",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": None},
        expected=None,
        msg="Should return null for null operand",
    ),
    ExpressionTestCase(
        "null_with_multiple",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": 2, "val1": 3, "val2": None},
        expected=None,
        msg="Should return null for null with multiple",
    ),
    ExpressionTestCase(
        "null_in_middle",
        expression={"$multiply": ["$val0", "$val1", "$val2", "$val3", "$val4"]},
        doc={"val0": 2, "val1": 3, "val2": 4, "val3": None, "val4": 5},
        expected=None,
        msg="Should return null for null in middle",
    ),
    ExpressionTestCase(
        "null_and_string",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": None, "val1": "string"},
        expected=None,
        msg="Should return null for null and string",
    ),
    ExpressionTestCase(
        "two_nulls",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": None, "val1": None},
        expected=None,
        msg="Should return null for two nulls",
    ),
    ExpressionTestCase(
        "null_with_invalid",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": 2, "val1": None, "val2": "string"},
        expected=None,
        msg="Should return null for null with invalid",
    ),
    ExpressionTestCase(
        "negative_positive",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": -5, "val1": 3},
        expected=-15,
        msg="Should handle negative positive",
    ),
    ExpressionTestCase(
        "both_negative",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": -10, "val1": -20},
        expected=200,
        msg="Should handle both negative",
    ),
    ExpressionTestCase(
        "zero_multiply",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 0, "val1": 5},
        expected=0,
        msg="Should handle zero multiply",
    ),
    ExpressionTestCase(
        "zero_negative_zero",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 0, "val1": -0.0},
        expected=-0.0,
        msg="Should handle zero negative zero",
    ),
    ExpressionTestCase(
        "single_negative_zero",
        expression={"$multiply": ["$val0"]},
        doc={"val0": -0.0},
        expected=-0.0,
        msg="Should handle single negative zero",
    ),
    ExpressionTestCase(
        "zero_in_middle",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": 5, "val1": 0, "val2": 10},
        expected=0,
        msg="Should handle zero in middle",
    ),
    ExpressionTestCase(
        "null_operand_mixed",
        expression={"$multiply": ["$val0", None]},
        doc={"val0": 2},
        expected=None,
        msg="Should return null for null operand",
    ),
    ExpressionTestCase(
        "missing_field",
        expression={"$multiply": ["$val0", MISSING]},
        doc={"val0": 2},
        expected=None,
        msg="Should return null for missing field",
    ),
    ExpressionTestCase(
        "null_with_multiple_mixed",
        expression={"$multiply": ["$val0", 3, None]},
        doc={"val0": 2},
        expected=None,
        msg="Should return null for null with multiple",
    ),
    ExpressionTestCase(
        "null_in_middle_mixed",
        expression={"$multiply": ["$val0", 3, 4, None, 5]},
        doc={"val0": 2},
        expected=None,
        msg="Should return null for null in middle",
    ),
    ExpressionTestCase(
        "null_and_string_mixed",
        expression={"$multiply": ["$val0", "string"]},
        doc={"val0": None},
        expected=None,
        msg="Should return null for null and string",
    ),
    ExpressionTestCase(
        "two_nulls_mixed",
        expression={"$multiply": ["$val0", None]},
        doc={"val0": None},
        expected=None,
        msg="Should return null for two nulls",
    ),
    ExpressionTestCase(
        "null_with_invalid_mixed",
        expression={"$multiply": ["$val0", None, "string"]},
        doc={"val0": 2},
        expected=None,
        msg="Should return null for null with invalid",
    ),
    ExpressionTestCase(
        "negative_positive_mixed",
        expression={"$multiply": ["$val0", 3]},
        doc={"val0": -5},
        expected=-15,
        msg="Should handle negative positive",
    ),
    ExpressionTestCase(
        "both_negative_mixed",
        expression={"$multiply": ["$val0", -20]},
        doc={"val0": -10},
        expected=200,
        msg="Should handle both negative",
    ),
    ExpressionTestCase(
        "zero_multiply_mixed",
        expression={"$multiply": ["$val0", 5]},
        doc={"val0": 0},
        expected=0,
        msg="Should handle zero multiply",
    ),
    ExpressionTestCase(
        "zero_negative_zero_mixed",
        expression={"$multiply": ["$val0", -0.0]},
        doc={"val0": 0},
        expected=-0.0,
        msg="Should handle zero negative zero",
    ),
    ExpressionTestCase(
        "zero_in_middle_mixed",
        expression={"$multiply": ["$val0", 0, 10]},
        doc={"val0": 5},
        expected=0,
        msg="Should handle zero in middle",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_LITERAL_TESTS))
def test_multiply_literal(collection, test):
    """Test $multiply from literals"""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(MULTIPLY_FIELD_REF_TESTS))
def test_multiply_field_ref(collection, test):
    """Test $multiply from documents, using all-field-reference and mixed
    literal/field-reference operand forms."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
