"""
Position-argument error tests for $slice expression.

Tests non-numeric and non-integral position rejection in the 3-arg form.
Array and n-argument errors are in test_expression_slice_errors.py.
"""

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
    EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
    EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT64_MAX,
)

# Property [Numeric Position]: a non-numeric position is rejected for every BSON type.
POS_NOT_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pos_string",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": "1", "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject string position",
    ),
    ExpressionTestCase(
        "pos_bool",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": True, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject bool position",
    ),
    ExpressionTestCase(
        "pos_array",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": [1], "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject array position",
    ),
    ExpressionTestCase(
        "pos_object",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": {"a": 1}, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject object position",
    ),
    ExpressionTestCase(
        "pos_datetime",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": datetime(2024, 1, 1, tzinfo=timezone.utc), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject datetime position",
    ),
    ExpressionTestCase(
        "pos_objectid",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": ObjectId(), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject objectid position",
    ),
    ExpressionTestCase(
        "pos_binary",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": Binary(b"x", 0), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject binary position",
    ),
    ExpressionTestCase(
        "pos_regex",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": Regex("x"), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject regex position",
    ),
    ExpressionTestCase(
        "pos_javascript",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": Code("x"), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject JavaScript code position",
    ),
    ExpressionTestCase(
        "pos_timestamp",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": Timestamp(0, 0), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject timestamp position",
    ),
    ExpressionTestCase(
        "pos_minkey",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": MinKey(), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject minkey position",
    ),
    ExpressionTestCase(
        "pos_maxkey",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": MaxKey(), "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_NUMERIC_ERROR,
        msg="$slice should reject maxkey position",
    ),
]

# Property [32-bit Representability]: position must be a whole number representable as
# a signed 32-bit integer; fractional values, NaN/Infinity, and integral values outside
# the int32 range are all rejected with the same error.
POS_NOT_INTEGRAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "pos_fractional",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": 1.5, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject a fractional position",
    ),
    ExpressionTestCase(
        "pos_nan",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": FLOAT_NAN, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject NaN position",
    ),
    ExpressionTestCase(
        "pos_inf",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": FLOAT_INFINITY, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject infinity position",
    ),
    ExpressionTestCase(
        "pos_neg_inf",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": FLOAT_NEGATIVE_INFINITY, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject -infinity position",
    ),
    ExpressionTestCase(
        "pos_decimal128_nan",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": DECIMAL128_NAN, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject decimal128 NaN position",
    ),
    ExpressionTestCase(
        "pos_decimal128_inf",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": DECIMAL128_INFINITY, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg="$slice should reject decimal128 infinity position",
    ),
    ExpressionTestCase(
        "pos_int64_max",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": INT64_MAX, "n": 2},
        error_code=EXPRESSION_SLICE_ARG_NOT_INTEGRAL_ERROR,
        msg=(
            "$slice should reject a position that is a whole number outside the "
            "32-bit integer range"
        ),
    ),
]

ALL_TESTS = POS_NOT_NUMERIC_TESTS + POS_NOT_INTEGRAL_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_slice_position_insert(collection, test):
    """Test $slice position-argument error cases with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
