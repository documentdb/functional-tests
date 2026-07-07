"""
BSON type tests for $isArray expression.

Tests arrays containing specific BSON types return true,
non-array BSON types return false, special numeric values,
and boundary values.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Arrays containing specific BSON types → true
BSON_ARRAY_TRUE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="bindata_array",
        doc={"val": [Binary(b"\x00", 0)]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for BinData array",
    ),
    ExpressionTestCase(
        id="timestamp_array",
        doc={"val": [Timestamp(0, 0)]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Timestamp array",
    ),
    ExpressionTestCase(
        id="int64_array",
        doc={"val": [Int64(1)]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Int64 array",
    ),
    ExpressionTestCase(
        id="decimal128_array",
        doc={"val": [Decimal128("1")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Decimal128 array",
    ),
    ExpressionTestCase(
        id="objectid_array",
        doc={"val": [ObjectId()]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for ObjectId array",
    ),
    ExpressionTestCase(
        id="datetime_array",
        doc={"val": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for datetime array",
    ),
    ExpressionTestCase(
        id="minkey_array",
        doc={"val": [MinKey()]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for MinKey array",
    ),
    ExpressionTestCase(
        id="maxkey_array",
        doc={"val": [MaxKey()]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for MaxKey array",
    ),
    ExpressionTestCase(
        id="regex_array",
        doc={"val": [Regex(".*")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Regex array",
    ),
    ExpressionTestCase(
        id="nan_array",
        doc={"val": [float("nan")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for NaN array",
    ),
    ExpressionTestCase(
        id="inf_array",
        doc={"val": [float("inf")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Infinity array",
    ),
    ExpressionTestCase(
        id="decimal128_nan_array",
        doc={"val": [Decimal128("NaN")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Decimal128 NaN array",
    ),
    ExpressionTestCase(
        id="decimal128_inf_array",
        doc={"val": [Decimal128("Infinity")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Decimal128 Infinity array",
    ),
    ExpressionTestCase(
        id="decimal128_neg_nan_array",
        doc={"val": [Decimal128("-NaN")]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Decimal128 -NaN array",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf_array",
        doc={"val": [DECIMAL128_NEGATIVE_INFINITY]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Decimal128 -Infinity array",
    ),
    ExpressionTestCase(
        id="neg_inf_array",
        doc={"val": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for -Infinity array",
    ),
    ExpressionTestCase(
        id="neg_zero_array",
        doc={"val": [DOUBLE_NEGATIVE_ZERO]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for negative zero array",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_array",
        doc={"val": [DECIMAL128_NEGATIVE_ZERO]},
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for Decimal128 -0 array",
    ),
    ExpressionTestCase(
        id="nested_mixed_bson_array",
        doc={
            "val": [
                MinKey(),
                {"a": [Decimal128("1.5")]},
                Int64(1),
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                Binary(b"\x01", 0),
            ]
        },
        expression={"$isArray": "$val"},
        expected=True,
        msg="Should return true for nested mixed BSON array",
    ),
]

# Non-array BSON types → false
BSON_FALSE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64",
        doc={"val": Int64(1)},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Int64",
    ),
    ExpressionTestCase(
        id="decimal128",
        doc={"val": Decimal128("1")},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Decimal128",
    ),
    ExpressionTestCase(
        id="objectid",
        doc={"val": ObjectId("000000000000000000000001")},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for ObjectId",
    ),
    ExpressionTestCase(
        id="datetime",
        doc={"val": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for datetime",
    ),
    ExpressionTestCase(
        id="binary",
        doc={"val": Binary(b"\x01", 0)},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Binary",
    ),
    ExpressionTestCase(
        id="regex",
        doc={"val": Regex("^abc")},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Regex",
    ),
    ExpressionTestCase(
        id="timestamp",
        doc={"val": Timestamp(1, 1)},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Timestamp",
    ),
    ExpressionTestCase(
        id="minkey",
        doc={"val": MinKey()},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for MinKey",
    ),
    ExpressionTestCase(
        id="maxkey",
        doc={"val": MaxKey()},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for MaxKey",
    ),
]

# Special numeric values → false
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="nan",
        doc={"val": FLOAT_NAN},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for NaN",
    ),
    ExpressionTestCase(
        id="inf",
        doc={"val": FLOAT_INFINITY},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Infinity",
    ),
    ExpressionTestCase(
        id="neg_inf",
        doc={"val": FLOAT_NEGATIVE_INFINITY},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for -Infinity",
    ),
    ExpressionTestCase(
        id="neg_zero",
        doc={"val": DOUBLE_NEGATIVE_ZERO},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for negative zero",
    ),
    ExpressionTestCase(
        id="decimal128_nan",
        doc={"val": DECIMAL128_NAN},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Decimal128 NaN",
    ),
    ExpressionTestCase(
        id="decimal128_neg_nan",
        doc={"val": Decimal128("-NaN")},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Decimal128 -NaN",
    ),
    ExpressionTestCase(
        id="decimal128_inf",
        doc={"val": DECIMAL128_INFINITY},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Decimal128 Infinity",
    ),
    ExpressionTestCase(
        id="decimal128_neg_inf",
        doc={"val": DECIMAL128_NEGATIVE_INFINITY},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Decimal128 -Infinity",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero",
        doc={"val": DECIMAL128_NEGATIVE_ZERO},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for Decimal128 -0",
    ),
]

# Boundary values → false
BOUNDARY_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int32_max",
        doc={"val": INT32_MAX},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for INT32_MAX",
    ),
    ExpressionTestCase(
        id="int32_min",
        doc={"val": INT32_MIN},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for INT32_MIN",
    ),
    ExpressionTestCase(
        id="int64_max",
        doc={"val": INT64_MAX},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for INT64_MAX",
    ),
    ExpressionTestCase(
        id="int64_min",
        doc={"val": INT64_MIN},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for INT64_MIN",
    ),
    ExpressionTestCase(
        id="decimal128_max",
        doc={"val": DECIMAL128_MAX},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for DECIMAL128_MAX",
    ),
    ExpressionTestCase(
        id="decimal128_min",
        doc={"val": DECIMAL128_MIN},
        expression={"$isArray": "$val"},
        expected=False,
        msg="Should return false for DECIMAL128_MIN",
    ),
]

# Aggregate and test
# Property [Literal Evaluation]: $isArray BSON type detection works with inline literal values.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_bindata_array",
        doc=None,
        expression={"$isArray": [{"$literal": [Binary(b"\x00", 0)]}]},
        expected=True,
        msg="$isArray should return true for literal BinData array",
    ),
    ExpressionTestCase(
        "literal_nested_mixed_bson_array",
        doc=None,
        expression={"$isArray": [{"$literal": [MinKey(), {"a": [Decimal128("1.5")]}, Int64(1)]}]},
        expected=True,
        msg="$isArray should return true for literal nested mixed BSON array",
    ),
    ExpressionTestCase(
        "literal_int64",
        doc=None,
        expression={"$isArray": [Int64(1)]},
        expected=False,
        msg="$isArray should return false for literal Int64",
    ),
    ExpressionTestCase(
        "literal_nan",
        doc=None,
        expression={"$isArray": [FLOAT_NAN]},
        expected=False,
        msg="$isArray should return false for literal NaN",
    ),
]

ALL_BSON_TESTS = (
    BSON_ARRAY_TRUE_TESTS
    + BSON_FALSE_TESTS
    + SPECIAL_NUMERIC_TESTS
    + BOUNDARY_TESTS
    + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_isArray_bson_insert(collection, test):
    """Test $isArray BSON types with values from inserted documents."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(result, expected=test.expected, msg=test.msg)
