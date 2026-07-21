"""Tests for $log domain, type, and arity errors across the value and base arguments."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression_with_insert,
)
from documentdb_tests.framework.error_codes import (
    EXPRESSION_TYPE_MISMATCH_ERROR,
    LOG_INVALID_BASE_ERROR,
    LOG_NON_NUMERIC_BASE_ERROR,
    LOG_NON_NUMERIC_VALUE_ERROR,
    LOG_NON_POSITIVE_VALUE_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_MAX_NEGATIVE,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MIN,
    INT64_MIN,
)

# Property [Value Domain]: $log rejects a non-positive value, including zero, negative zero,
# negative values, and negative infinity, across numeric types.
LOG_VALUE_DOMAIN_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_value",
        doc={"value": 0, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject an int32 zero value",
    ),
    ExpressionTestCase(
        "zero_double_value",
        doc={"value": DOUBLE_ZERO, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a double zero value",
    ),
    ExpressionTestCase(
        "negative_zero_double_value",
        doc={"value": DOUBLE_NEGATIVE_ZERO, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a negative zero double value",
    ),
    ExpressionTestCase(
        "zero_decimal_value",
        doc={"value": DECIMAL128_ZERO, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a decimal128 zero value",
    ),
    ExpressionTestCase(
        "negative_zero_decimal_value",
        doc={"value": DECIMAL128_NEGATIVE_ZERO, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a negative zero decimal128 value",
    ),
    ExpressionTestCase(
        "negative_value",
        doc={"value": -10, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a negative int32 value",
    ),
    ExpressionTestCase(
        "negative_fractional_value",
        doc={"value": -0.5, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a negative fractional value",
    ),
    ExpressionTestCase(
        "negative_decimal_value",
        doc={"value": Decimal128("-5"), "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a negative decimal128 value",
    ),
    ExpressionTestCase(
        "int32_min_value",
        doc={"value": INT32_MIN, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject an INT32_MIN value",
    ),
    ExpressionTestCase(
        "int64_min_value",
        doc={"value": INT64_MIN, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject an INT64_MIN value",
    ),
    ExpressionTestCase(
        "decimal_min_value",
        doc={"value": DECIMAL128_MIN, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject the minimum decimal128 value",
    ),
    ExpressionTestCase(
        "decimal_max_negative_value",
        doc={"value": DECIMAL128_MAX_NEGATIVE, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject the smallest-magnitude negative decimal128 value",
    ),
    ExpressionTestCase(
        "negative_infinity_value",
        doc={"value": FLOAT_NEGATIVE_INFINITY, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a float negative infinity value",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity_value",
        doc={"value": DECIMAL128_NEGATIVE_INFINITY, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_POSITIVE_VALUE_ERROR,
        msg="$log should reject a decimal128 negative infinity value",
    ),
]

# Property [Base Domain]: $log rejects a base that is not a positive number other than one,
# including zero, negative bases, negative infinity, and one.
LOG_BASE_DOMAIN_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_base",
        doc={"value": 100, "base": 0},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject an int32 zero base",
    ),
    ExpressionTestCase(
        "zero_double_base",
        doc={"value": 100, "base": DOUBLE_ZERO},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a double zero base",
    ),
    ExpressionTestCase(
        "negative_zero_double_base",
        doc={"value": 100, "base": DOUBLE_NEGATIVE_ZERO},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a negative zero double base",
    ),
    ExpressionTestCase(
        "zero_decimal_base",
        doc={"value": 100, "base": DECIMAL128_ZERO},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a decimal128 zero base",
    ),
    ExpressionTestCase(
        "negative_zero_decimal_base",
        doc={"value": 100, "base": DECIMAL128_NEGATIVE_ZERO},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a negative zero decimal128 base",
    ),
    ExpressionTestCase(
        "negative_base",
        doc={"value": 100, "base": -10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a negative int32 base",
    ),
    ExpressionTestCase(
        "negative_base_two",
        doc={"value": 100, "base": -2},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a negative int32 base of minus two",
    ),
    ExpressionTestCase(
        "negative_decimal_base",
        doc={"value": 100, "base": Decimal128("-2")},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a negative decimal128 base",
    ),
    ExpressionTestCase(
        "int32_min_base",
        doc={"value": 100, "base": INT32_MIN},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject an INT32_MIN base",
    ),
    ExpressionTestCase(
        "int64_min_base",
        doc={"value": 100, "base": INT64_MIN},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject an INT64_MIN base",
    ),
    ExpressionTestCase(
        "decimal_min_base",
        doc={"value": 100, "base": DECIMAL128_MIN},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject the minimum decimal128 base",
    ),
    ExpressionTestCase(
        "negative_infinity_base",
        doc={"value": 100, "base": FLOAT_NEGATIVE_INFINITY},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a float negative infinity base",
    ),
    ExpressionTestCase(
        "decimal_negative_infinity_base",
        doc={"value": 100, "base": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a decimal128 negative infinity base",
    ),
    ExpressionTestCase(
        "base_one",
        doc={"value": 100, "base": 1},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject an int32 base of one",
    ),
    ExpressionTestCase(
        "base_one_double",
        doc={"value": 100, "base": 1.0},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a double base of one",
    ),
    ExpressionTestCase(
        "base_one_decimal",
        doc={"value": 100, "base": Decimal128("1")},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_INVALID_BASE_ERROR,
        msg="$log should reject a decimal128 base of one",
    ),
]

# Property [Value Type Strictness]: $log rejects a non-numeric value.
LOG_VALUE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"value_type_{tid}",
            doc={"value": val, "base": 10},
            expression={"$log": ["$value", "$base"]},
            error_code=LOG_NON_NUMERIC_VALUE_ERROR,
            msg=f"$log should reject a {tid} value",
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
    ],
    ExpressionTestCase(
        "value_empty_array",
        doc={"value": [], "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_NUMERIC_VALUE_ERROR,
        msg="$log should reject an empty array value",
    ),
    ExpressionTestCase(
        "value_empty_object",
        doc={"value": {}, "base": 10},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_NUMERIC_VALUE_ERROR,
        msg="$log should reject an empty object value",
    ),
]

# Property [Base Type Strictness]: $log rejects a non-numeric base.
LOG_BASE_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"base_type_{tid}",
            doc={"value": 100, "base": val},
            expression={"$log": ["$value", "$base"]},
            error_code=LOG_NON_NUMERIC_BASE_ERROR,
            msg=f"$log should reject a {tid} base",
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
    ],
    ExpressionTestCase(
        "base_empty_array",
        doc={"value": 100, "base": []},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_NUMERIC_BASE_ERROR,
        msg="$log should reject an empty array base",
    ),
    ExpressionTestCase(
        "base_empty_object",
        doc={"value": 100, "base": {}},
        expression={"$log": ["$value", "$base"]},
        error_code=LOG_NON_NUMERIC_BASE_ERROR,
        msg="$log should reject an empty object base",
    ),
]

# Property [Non-Numeric Expression and Path Inputs]: array and object expression inputs, and field
# paths that resolve to an array, are delivered to $log as values and rejected as non-numeric in
# the value and base arguments.
LOG_EXPRESSION_INPUT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_value_expression",
        doc={"value": 100},
        expression={"$log": [["$value"], 10]},
        error_code=LOG_NON_NUMERIC_VALUE_ERROR,
        msg="$log should reject an array expression value without flattening it into arguments",
    ),
    ExpressionTestCase(
        "object_value_expression",
        doc={"value": 100},
        expression={"$log": [{"z": "$value"}, 10]},
        error_code=LOG_NON_NUMERIC_VALUE_ERROR,
        msg="$log should reject an object expression value rather than evaluating it",
    ),
    ExpressionTestCase(
        "array_path_value",
        doc={"a": [{"b": 10}, {"b": 100}]},
        expression={"$log": ["$a.b", 10]},
        error_code=LOG_NON_NUMERIC_VALUE_ERROR,
        msg="$log should reject a field-path value that resolves to an array",
    ),
    ExpressionTestCase(
        "array_base_expression",
        doc={"base": 10},
        expression={"$log": [100, ["$base"]]},
        error_code=LOG_NON_NUMERIC_BASE_ERROR,
        msg="$log should reject an array expression base without flattening it into arguments",
    ),
    ExpressionTestCase(
        "object_base_expression",
        doc={"base": 10},
        expression={"$log": [100, {"z": "$base"}]},
        error_code=LOG_NON_NUMERIC_BASE_ERROR,
        msg="$log should reject an object expression base rather than evaluating it",
    ),
    ExpressionTestCase(
        "array_path_base",
        doc={"a": [{"b": 10}, {"b": 100}]},
        expression={"$log": [100, "$a.b"]},
        error_code=LOG_NON_NUMERIC_BASE_ERROR,
        msg="$log should reject a field-path base that resolves to an array",
    ),
]

# Property [Arity]: $log requires exactly two arguments.
LOG_ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero",
        doc={},
        expression={"$log": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$log should reject zero arguments",
    ),
    ExpressionTestCase(
        "arity_one",
        doc={},
        expression={"$log": [100]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$log should reject a single argument",
    ),
    ExpressionTestCase(
        "arity_three",
        doc={},
        expression={"$log": [100, 10, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$log should reject three arguments",
    ),
]

LOG_ERROR_ALL_TESTS = (
    LOG_VALUE_DOMAIN_ERROR_TESTS
    + LOG_BASE_DOMAIN_ERROR_TESTS
    + LOG_VALUE_TYPE_ERROR_TESTS
    + LOG_BASE_TYPE_ERROR_TESTS
    + LOG_EXPRESSION_INPUT_ERROR_TESTS
    + LOG_ARITY_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LOG_ERROR_ALL_TESTS))
def test_log_errors(collection, test_case: ExpressionTestCase):
    """Test $log domain, type, and arity error cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
