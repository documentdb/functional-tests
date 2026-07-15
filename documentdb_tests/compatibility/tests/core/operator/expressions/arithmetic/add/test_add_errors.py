"""Tests for $add error cases including invalid operand types, multiple dates, and date overflow."""

from datetime import datetime, timezone

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.bson_type_validator import (
    BsonType,
    BsonTypeTestCase,
    generate_bson_rejection_test_cases,
)
from documentdb_tests.framework.error_codes import (
    MORE_THAN_ONE_DATE_ERROR,
    OVERFLOW_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    INT64_MAX,
)

_NUMERIC_DATE_AND_NULL_TYPES = [
    BsonType.DOUBLE,
    BsonType.INT,
    BsonType.LONG,
    BsonType.DECIMAL,
    BsonType.DATE,
    BsonType.NULL,
]

# Property [Type Strictness]: $add rejects non-numeric, non-date operand types.
ADD_TYPE_SPEC = BsonTypeTestCase(
    id="add_operand",
    msg="$add should reject non-numeric, non-date operand",
    keyword="$add",
    valid_types=_NUMERIC_DATE_AND_NULL_TYPES,
    default_error_code=TYPE_MISMATCH_ERROR,
)

ADD_TYPE_REJECTION_CASES = generate_bson_rejection_test_cases([ADD_TYPE_SPEC])
_ADD_TYPE_REJECTION_EXPR = {"$add": [1, "$b"]}


@pytest.mark.parametrize("bson_type,sample_value,spec", ADD_TYPE_REJECTION_CASES)
def test_add_rejects_invalid_operand_type(collection, bson_type, sample_value, spec):
    """Test $add rejects non-numeric, non-date BSON types as operands."""
    result = execute_expression_with_insert(
        collection, _ADD_TYPE_REJECTION_EXPR, {"b": sample_value}
    )
    assertFailureCode(result, spec.expected_code(bson_type), msg=spec.msg)


# Property [Mixed Valid and Invalid]: $add rejects an invalid operand when it appears among
# valid numeric operands.
ADD_MIXED_VALID_INVALID_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_valid_invalid",
        doc={"a": 1, "b": 2, "c": "string"},
        expression={"$add": ["$a", "$b", "$c"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$add should error when a string appears among numeric operands",
    ),
]

# Property [Single Invalid Operand]: $add rejects a single operand of an invalid type.
ADD_SINGLE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "single_string",
        doc={"a": "string"},
        expression={"$add": ["$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$add should reject a single string operand",
    ),
    ExpressionTestCase(
        "single_boolean",
        doc={"a": True},
        expression={"$add": ["$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$add should reject a single boolean operand",
    ),
    ExpressionTestCase(
        "single_array",
        doc={"a": [1, 2]},
        expression={"$add": ["$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$add should reject a single array operand",
    ),
    ExpressionTestCase(
        "single_object",
        doc={"a": {"x": 1}},
        expression={"$add": ["$a"]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="$add should reject a single object operand",
    ),
]

# Property [Multiple Dates]: $add rejects expressions with more than one date operand.
ADD_MULTIPLE_DATE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "add_two_identical_dates",
        doc={
            "a": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 1, tzinfo=timezone.utc),
        },
        expression={"$add": ["$a", "$b"]},
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="$add should error when adding two identical date operands",
    ),
    ExpressionTestCase(
        "two_different_dates",
        doc={
            "a": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 2, tzinfo=timezone.utc),
        },
        expression={"$add": ["$a", "$b"]},
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="$add should error when adding two different date operands",
    ),
    ExpressionTestCase(
        "two_dates_with_numbers",
        doc={
            "a": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 2, tzinfo=timezone.utc),
        },
        expression={"$add": [1, 2, 3, "$a", "$b"]},
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="$add should error when two dates appear among numeric operands",
    ),
    ExpressionTestCase(
        "dates_separated_by_number",
        doc={
            "a": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "b": datetime(2026, 1, 2, tzinfo=timezone.utc),
        },
        expression={"$add": ["$a", 1, "$b"]},
        error_code=MORE_THAN_ONE_DATE_ERROR,
        msg="$add should error when two dates are separated by a numeric operand",
    ),
]

# Property [Date with Non-Finite]: $add rejects NaN and Infinity as numeric operands when a
# date is also present, since the resulting date would be non-representable.
ADD_DATE_NON_FINITE_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_nan",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": FLOAT_NAN},
        expression={"$add": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$add should error when adding a date and float NaN",
    ),
    ExpressionTestCase(
        "date_infinity",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": FLOAT_INFINITY},
        expression={"$add": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$add should error when adding a date and float infinity",
    ),
    ExpressionTestCase(
        "date_decimal_nan",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": DECIMAL128_NAN},
        expression={"$add": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$add should error when adding a date and decimal128 NaN",
    ),
    ExpressionTestCase(
        "date_decimal_infinity",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": DECIMAL128_INFINITY},
        expression={"$add": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$add should error when adding a date and decimal128 infinity",
    ),
]

# Property [Date Overflow]: $add errors when the millisecond offset would push the date result
# beyond the representable date range.
ADD_DATE_OVERFLOW_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "date_int64_max",
        doc={"a": datetime(2026, 1, 1, tzinfo=timezone.utc), "b": INT64_MAX},
        expression={"$add": ["$a", "$b"]},
        error_code=OVERFLOW_ERROR,
        msg="$add should error when adding INT64_MAX milliseconds to a date overflows the date range",  # noqa: E501
    ),
]

ADD_REMAINING_ERROR_TESTS = (
    ADD_MIXED_VALID_INVALID_TESTS
    + ADD_SINGLE_TYPE_ERROR_TESTS
    + ADD_MULTIPLE_DATE_TESTS
    + ADD_DATE_NON_FINITE_ERROR_TESTS
    + ADD_DATE_OVERFLOW_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(ADD_REMAINING_ERROR_TESTS))
def test_add_errors(collection, test_case: ExpressionTestCase):
    """Test $add multiple-date, single-invalid, and date non-finite error cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
