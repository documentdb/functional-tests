"""
Error tests for $multiply expression.

Covers non-numeric operand rejection (empty array, empty object) and a
mixed valid/invalid operand list.
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
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

MULTIPLY_LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array",
        expression={"$multiply": [2, []]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$multiply": [2, {}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object",
    ),
    ExpressionTestCase(
        "mixed_valid_invalid",
        expression={"$multiply": [2, 3, "string"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject mixed valid invalid",
    ),
]


MULTIPLY_FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "empty_array",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array",
    ),
    ExpressionTestCase(
        "empty_object",
        expression={"$multiply": ["$val0", "$val1"]},
        doc={"val0": 2, "val1": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object",
    ),
    ExpressionTestCase(
        "mixed_valid_invalid",
        expression={"$multiply": ["$val0", "$val1", "$val2"]},
        doc={"val0": 2, "val1": 3, "val2": "string"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject mixed valid invalid",
    ),
    ExpressionTestCase(
        "empty_array_mixed",
        expression={"$multiply": ["$val0", []]},
        doc={"val0": 2},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty array",
    ),
    ExpressionTestCase(
        "empty_object_mixed",
        expression={"$multiply": ["$val0", {}]},
        doc={"val0": 2},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject empty object",
    ),
    ExpressionTestCase(
        "mixed_valid_invalid_mixed",
        expression={"$multiply": ["$val0", 3, "string"]},
        doc={"val0": 2},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject mixed valid invalid",
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
