"""
Tests for $cmp argument handling.

Covers argument validation (error cases), field references, return type verification,
and nested $cmp expressions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import EXPRESSION_TYPE_MISMATCH_ERROR
from documentdb_tests.framework.parametrize import pytest_params

ARG_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "no_args",
        expression={"$cmp": []},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for empty arguments",
    ),
    ExpressionTestCase(
        "single_arg",
        expression={"$cmp": ["$a"]},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for single argument",
    ),
    ExpressionTestCase(
        "non_array_int",
        expression={"$cmp": 1},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array int argument",
    ),
    ExpressionTestCase(
        "non_array_string",
        expression={"$cmp": "string"},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array string argument",
    ),
    ExpressionTestCase(
        "non_array_object",
        expression={"$cmp": {"a": 1}},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array object argument",
    ),
    ExpressionTestCase(
        "non_array_boolean",
        expression={"$cmp": True},
        doc={"a": 1},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for non-array boolean argument",
    ),
    ExpressionTestCase(
        "three_args",
        expression={"$cmp": ["$a", "$b", "$c"]},
        doc={"a": 1, "b": 2, "c": 3},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should error for three arguments",
    ),
]


FIELD_REF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "field_ref_lt",
        expression={"$cmp": ["$qty", 250]},
        doc={"qty": 200},
        expected=-1,
        msg="Field reference less than literal",
    ),
    ExpressionTestCase(
        "field_ref_eq",
        expression={"$cmp": ["$qty", 250]},
        doc={"qty": 250},
        expected=0,
        msg="Field reference equals literal",
    ),
    ExpressionTestCase(
        "field_ref_gt",
        expression={"$cmp": ["$qty", 250]},
        doc={"qty": 300},
        expected=1,
        msg="Field reference greater than literal",
    ),
]


RETURN_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "return_type_neg1",
        expression={"$type": {"$cmp": [1, 2]}},
        doc={"a": 1},
        expected="int",
        msg="$cmp should return BSON int type",
    ),
]


NESTED_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "nested_cmp",
        expression={"$cmp": [{"$cmp": [1, 2]}, -1]},
        doc={"a": 1},
        expected=0,
        msg="Nested $cmp(-1) equals -1",
    ),
]

ALL_TESTS = ARG_TESTS + FIELD_REF_TESTS + RETURN_TYPE_TESTS + NESTED_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_cmp_argument_handling(collection, test):
    """Test $cmp argument validation, field references, return type, and nesting."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
