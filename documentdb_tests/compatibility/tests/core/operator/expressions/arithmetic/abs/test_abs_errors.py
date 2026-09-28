"""Tests for $abs type, arity, and overflow errors."""

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
    ABS_OVERFLOW_ERROR,
    EXPRESSION_TYPE_MISMATCH_ERROR,
    NON_NUMERIC_TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    INT64_MIN,
)

# Property [Type Strictness]: $abs rejects non-numeric input types.
ABS_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        f"type_{tid}",
        doc={"value": val},
        expression={"$abs": ["$value"]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg=f"$abs should reject a {tid} input",
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

# Property [Arity]: $abs requires exactly one argument.
ABS_ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero",
        doc={},
        expression={"$abs": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$abs should reject zero arguments",
    ),
    ExpressionTestCase(
        "arity_two",
        doc={},
        expression={"$abs": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$abs should reject two arguments",
    ),
]

# Property [Overflow]: $abs of the minimum int64 errors because the positive result is not
# representable as a long.
ABS_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_min_overflow",
        doc={"value": INT64_MIN},
        expression={"$abs": ["$value"]},
        error_code=ABS_OVERFLOW_ERROR,
        msg="$abs should error on overflow for INT64_MIN",
    ),
]

ABS_ERROR_ALL_TESTS = ABS_TYPE_ERROR_TESTS + ABS_ARITY_ERROR_TESTS + ABS_OVERFLOW_TESTS


@pytest.mark.parametrize("test_case", pytest_params(ABS_ERROR_ALL_TESTS))
def test_abs_errors(collection, test_case: ExpressionTestCase):
    """Test $abs type, arity, and overflow error cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
