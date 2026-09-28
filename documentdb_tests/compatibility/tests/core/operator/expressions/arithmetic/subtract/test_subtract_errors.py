from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    OVERFLOW_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
)

# Property [Date constraint]: $subtract enforces date arithmetic type rules.
DATE_CONSTRAINT_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "number_minus_date",
        doc={"a": 1, "b": datetime(2026, 1, 1, tzinfo=timezone.utc)},
        expression={"$subtract": ["$a", "$b"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$subtract should reject a date subtrahend when the minuend is a number",
    ),
    ExpressionTestCase(
        "date_minus_string",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": "string"},
        expression={"$subtract": ["$a", "$b"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$subtract should reject a string subtrahend when the minuend is a date",
    ),
    ExpressionTestCase(
        "date_minus_bool",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": True},
        expression={"$subtract": ["$a", "$b"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$subtract should reject a boolean subtrahend when the minuend is a date",
    ),
    ExpressionTestCase(
        "date_minus_array",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": [1, 2]},
        expression={"$subtract": ["$a", "$b"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$subtract should reject an array subtrahend when the minuend is a date",
    ),
]

# Property [Date NaN/Inf]: $subtract rejects NaN/Infinity as a date offset with
# TYPE_MISMATCH_DATE_ERROR.
DATE_NAN_INF_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_minus_nan",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": FLOAT_NAN},
        expression={"$subtract": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$subtract should reject NaN as a date millisecond offset",
    ),
    ExpressionTestCase(
        "date_minus_infinity",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": FLOAT_INFINITY},
        expression={"$subtract": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$subtract should reject Infinity as a date millisecond offset",
    ),
    ExpressionTestCase(
        "date_minus_decimal_nan",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": DECIMAL128_NAN},
        expression={"$subtract": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$subtract should reject Decimal128 NaN as a date millisecond offset",
    ),
]

# Property [Arity]: $subtract requires exactly two arguments.
ARITY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_args",
        doc={},
        expression={"$subtract": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$subtract should reject an empty argument list",
    ),
    ExpressionTestCase(
        "one_arg",
        doc={},
        expression={"$subtract": [1]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$subtract should reject a single argument",
    ),
    ExpressionTestCase(
        "three_args",
        doc={},
        expression={"$subtract": [1, 2, 3]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$subtract should reject three arguments",
    ),
]

SUBTRACT_ERROR_TESTS: list[ExpressionTestCase] = (
    DATE_CONSTRAINT_TESTS + DATE_NAN_INF_TESTS + ARITY_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SUBTRACT_ERROR_TESTS))
def test_subtract_errors(collection, test_case: ExpressionTestCase):
    """Test $subtract error handling for invalid types, date constraints, and arity violations."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
