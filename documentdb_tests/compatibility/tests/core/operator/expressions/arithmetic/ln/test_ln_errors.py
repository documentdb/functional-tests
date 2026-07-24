"""Tests for $ln domain, type, and arity errors."""

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
    LN_NON_POSITIVE_INPUT_ERROR,
    NON_NUMERIC_TYPE_MISMATCH_ERROR,
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

# Property [Domain]: $ln rejects non-positive inputs, including zero, negative zero, negative
# values, and negative infinity.
LN_DOMAIN_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "zero_int32",
        doc={"value": 0},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject int32 zero",
    ),
    ExpressionTestCase(
        "zero_double",
        doc={"value": DOUBLE_ZERO},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject double zero",
    ),
    ExpressionTestCase(
        "zero_decimal",
        doc={"value": DECIMAL128_ZERO},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject decimal128 zero",
    ),
    ExpressionTestCase(
        "negative_zero_double",
        doc={"value": DOUBLE_NEGATIVE_ZERO},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject negative zero double",
    ),
    ExpressionTestCase(
        "negative_zero_decimal",
        doc={"value": DECIMAL128_NEGATIVE_ZERO},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject negative zero decimal128",
    ),
    ExpressionTestCase(
        "negative_int32",
        doc={"value": -1},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject a negative integer",
    ),
    ExpressionTestCase(
        "negative_ten",
        doc={"value": -10},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject negative ten",
    ),
    ExpressionTestCase(
        "negative_double",
        doc={"value": -0.5},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject a negative double",
    ),
    ExpressionTestCase(
        "negative_decimal",
        doc={"value": Decimal128("-1")},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject a negative decimal128",
    ),
    ExpressionTestCase(
        "int32_min",
        doc={"value": INT32_MIN},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject INT32_MIN",
    ),
    ExpressionTestCase(
        "int64_min",
        doc={"value": INT64_MIN},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject INT64_MIN",
    ),
    ExpressionTestCase(
        "decimal_min",
        doc={"value": DECIMAL128_MIN},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject the minimum decimal128",
    ),
    ExpressionTestCase(
        "decimal_max_negative",
        doc={"value": DECIMAL128_MAX_NEGATIVE},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject the smallest-magnitude negative decimal128",
    ),
    ExpressionTestCase(
        "float_negative_infinity",
        doc={"value": FLOAT_NEGATIVE_INFINITY},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject float negative infinity",
    ),
    ExpressionTestCase(
        "decimal128_negative_infinity",
        doc={"value": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$ln": ["$value"]},
        error_code=LN_NON_POSITIVE_INPUT_ERROR,
        msg="$ln should reject decimal128 negative infinity",
    ),
]

# Property [Type Strictness]: $ln rejects non-numeric input types.
LN_TYPE_ERROR_TESTS: list[ExpressionTestCase] = [
    *[
        ExpressionTestCase(
            f"type_{tid}",
            doc={"value": val},
            expression={"$ln": ["$value"]},
            error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
            msg=f"$ln should reject a {tid} input",
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
        "empty_array",
        doc={"value": []},
        expression={"$ln": ["$value"]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ln should reject an empty array input",
    ),
    ExpressionTestCase(
        "empty_object",
        doc={"value": {}},
        expression={"$ln": ["$value"]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ln should reject an empty object input",
    ),
]

# Property [Non-Numeric Expression and Path Inputs]: array and object expression inputs, and field
# paths that resolve to an array, are delivered to $ln as values and rejected as non-numeric.
LN_EXPRESSION_INPUT_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "array_expression_input",
        doc={"value": 10},
        expression={"$ln": [["$value"]]},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ln should reject an array expression input without flattening it into arguments",
    ),
    ExpressionTestCase(
        "object_expression_input",
        doc={"value": 10},
        expression={"$ln": {"z": "$value"}},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ln should reject an object expression input as a value rather than evaluating it",
    ),
    ExpressionTestCase(
        "array_of_objects_path",
        doc={"a": [{"b": 10}, {"b": 100}]},
        expression={"$ln": "$a.b"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ln should reject a field path that resolves to an array from an array of objects",
    ),
    ExpressionTestCase(
        "array_index_path",
        doc={"a": [{"b": 10}, {"b": 100}]},
        expression={"$ln": "$a.0.b"},
        error_code=NON_NUMERIC_TYPE_MISMATCH_ERROR,
        msg="$ln should reject an array-index field path that resolves to an array in an "
        "aggregation expression",
    ),
]

# Property [Arity]: $ln requires exactly one argument.
LN_ARITY_ERROR_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "arity_zero",
        doc={},
        expression={"$ln": []},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$ln should reject zero arguments",
    ),
    ExpressionTestCase(
        "arity_two",
        doc={},
        expression={"$ln": [1, 2]},
        error_code=EXPRESSION_TYPE_MISMATCH_ERROR,
        msg="$ln should reject two arguments",
    ),
]

LN_ERROR_ALL_TESTS = (
    LN_DOMAIN_ERROR_TESTS
    + LN_TYPE_ERROR_TESTS
    + LN_EXPRESSION_INPUT_ERROR_TESTS
    + LN_ARITY_ERROR_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(LN_ERROR_ALL_TESTS))
def test_ln_errors(collection, test_case: ExpressionTestCase):
    """Test $ln domain, type, and arity error cases."""
    result = execute_expression_with_insert(collection, test_case.expression, test_case.doc)
    assert_expression_result(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
