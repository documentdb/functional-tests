"""Tests for $exp type and arity errors."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    NON_NUMERIC_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params

# Property [Type Strictness]: $exp rejects non-numeric input types.
EXP_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"type_{tid}",
        doc={"value": val},
        expression={"$exp": ["$value"]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg=f"$exp should reject a {tid} input",
    )
    for tid, val in [
        ("string", "abc"),
        ("bool", True),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("regex", Regex("abc")),
        ("binary", Binary(b"data")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("timestamp", Timestamp(1, 1)),
        ("code", Code("function(){}")),
    ]
]

# Property [Arity]: $exp requires exactly one argument.
EXP_ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero",
        doc={},
        expression={"$exp": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$exp should reject zero arguments",
    ),
    ExpressionTestCase(
        "arity_two",
        doc={},
        expression={"$exp": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$exp should reject two arguments",
    ),
]

EXP_ERROR_ALL_TESTS = EXP_TYPE_ERROR_TESTS + EXP_ARITY_ERROR_TESTS


@pytest.mark.parametrize("test_case", pytest_params(EXP_ERROR_ALL_TESTS))
def test_exp_errors(collection, test_case: ExpressionTestCase):
    """Test $exp type and arity error cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
