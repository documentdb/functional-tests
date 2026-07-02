"""Error tests for the $subtract operator."""

from __future__ import annotations

import pytest
from bson import Binary, MaxKey, MinKey, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness]: $subtract rejects non-numeric operands.
SUBTRACT_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "string_subtrahend",
        doc={},
        expression={"$subtract": [10, "string"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string subtrahend",
    ),
    ExpressionTestCase(
        "string_minuend",
        doc={},
        expression={"$subtract": ["string", 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject string minuend",
    ),
    ExpressionTestCase(
        "boolean_subtrahend",
        doc={},
        expression={"$subtract": [10, True]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject boolean subtrahend",
    ),
    ExpressionTestCase(
        "boolean_minuend",
        doc={},
        expression={"$subtract": [True, 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject boolean minuend",
    ),
    ExpressionTestCase(
        "array_subtrahend",
        doc={},
        expression={"$subtract": [10, [2, 3]]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array subtrahend",
    ),
    ExpressionTestCase(
        "array_minuend",
        doc={},
        expression={"$subtract": [[2, 3], 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject array minuend",
    ),
    ExpressionTestCase(
        "object_subtrahend",
        doc={},
        expression={"$subtract": [10, {"a": 2}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object subtrahend",
    ),
    ExpressionTestCase(
        "object_minuend",
        doc={},
        expression={"$subtract": [{"a": 2}, 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject object minuend",
    ),
    ExpressionTestCase(
        "binary_minuend",
        doc={"a": Binary(b"test", 0)},
        expression={"$subtract": ["$a", 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject binary minuend",
    ),
    ExpressionTestCase(
        "binary_subtrahend",
        doc={"a": Binary(b"test", 0)},
        expression={"$subtract": [10, "$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject binary subtrahend",
    ),
    ExpressionTestCase(
        "timestamp_minuend",
        doc={"a": Timestamp(1234567890, 1)},
        expression={"$subtract": ["$a", 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject timestamp minuend",
    ),
    ExpressionTestCase(
        "timestamp_subtrahend",
        doc={"a": Timestamp(1234567890, 1)},
        expression={"$subtract": [10, "$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject timestamp subtrahend",
    ),
    ExpressionTestCase(
        "maxkey_minuend",
        doc={"a": MaxKey()},
        expression={"$subtract": ["$a", 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject maxkey minuend",
    ),
    ExpressionTestCase(
        "maxkey_subtrahend",
        doc={"a": MaxKey()},
        expression={"$subtract": [10, "$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject maxkey subtrahend",
    ),
    ExpressionTestCase(
        "minkey_minuend",
        doc={"a": MinKey()},
        expression={"$subtract": ["$a", 5]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject minkey minuend",
    ),
    ExpressionTestCase(
        "minkey_subtrahend",
        doc={"a": MinKey()},
        expression={"$subtract": [10, "$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should reject minkey subtrahend",
    ),
]

# Property [Arity]: $subtract requires exactly two arguments.
SUBTRACT_ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        doc={},
        expression={"$subtract": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject zero arguments",
    ),
    ExpressionTestCase(
        "one_arg",
        doc={},
        expression={"$subtract": [1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject one argument",
    ),
    ExpressionTestCase(
        "three_args",
        doc={},
        expression={"$subtract": [1, 2, 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="Should reject three arguments",
    ),
]

SUBTRACT_ERROR_ALL_TESTS = SUBTRACT_TYPE_ERROR_TESTS + SUBTRACT_ARITY_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_ERROR_ALL_TESTS))
def test_subtract_errors(collection, test_case: ExpressionTestCase):
    """Test $subtract type and arity error cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result, expected=test_case.expected, error_code=test_case.error_code, msg=test_case.msg
    )
