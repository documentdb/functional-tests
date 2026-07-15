"""Tests for $floor rejection of non-numeric input types and wrong argument counts."""

from __future__ import annotations

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

# Property [Type Strictness]: a non-numeric input produces NON_NUMERIC_TYPE_MISMATCH_ERROR.
FLOOR_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"type_error_{tid}",
        doc={"value": val},
        expression={"$floor": ["$value"]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg=f"$floor should reject a {tid} input as non-numeric",
    )
    for tid, val in [
        ("string", "string"),
        ("bool", True),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("date", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("binary", Binary(b"data")),
        ("regex", Regex("abc")),
        ("timestamp", Timestamp(1, 1)),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("javascript", Code("function(){}")),
    ]
]

# Property [Arity]: floor requires exactly one argument.
FLOOR_ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_no_args",
        doc={},
        expression={"$floor": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$floor should reject a call with no arguments",
    ),
    ExpressionTestCase(
        "arity_two_args",
        doc={},
        expression={"$floor": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$floor should reject a call with two arguments",
    ),
]

FLOOR_ERROR_TESTS = FLOOR_TYPE_ERROR_TESTS + FLOOR_ARITY_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(FLOOR_ERROR_TESTS))
def test_floor_type_errors(collection, test):
    """Test $floor type and arity rejection."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
