"""
BSON type element preservation tests for $zip expression.

Tests that various BSON types are preserved when zipping arrays.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (  # noqa: E501
    assert_expression_result,
    execute_expression,
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
    INT64_ZERO,
)

# Property [Type Preservation]: $zip preserves each element's BSON type.
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int64_values",
        doc={"arr0": [Int64(1)], "arr1": [Int64(2)]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[Int64(1), Int64(2)]],
        msg="$zip should preserve Int64 values",
    ),
    ExpressionTestCase(
        "decimal128_values",
        doc={"arr0": [DECIMAL128_ONE_AND_HALF], "arr1": [DECIMAL128_TWO_AND_HALF]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF]],
        msg="$zip should preserve Decimal128 values",
    ),
    ExpressionTestCase(
        "datetime_values",
        doc={
            "arr0": [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            "arr1": [datetime(2024, 6, 1, tzinfo=timezone.utc)],
        },
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[
            [datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 6, 1, tzinfo=timezone.utc)]
        ],
        msg="$zip should preserve datetime values",
    ),
    ExpressionTestCase(
        "objectid_values",
        doc={
            "arr0": [ObjectId("000000000000000000000001")],
            "arr1": [ObjectId("000000000000000000000002")],
        },
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]],
        msg="$zip should preserve ObjectId values",
    ),
    ExpressionTestCase(
        "binary_values",
        doc={"arr0": [Binary(b"\x01", 0)], "arr1": [Binary(b"\x02", 0)]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[b"\x01", b"\x02"]],
        msg="$zip should preserve Binary values",
    ),
    ExpressionTestCase(
        "regex_values",
        doc={"arr0": [Regex("^a", "i")], "arr1": [Regex("^b", "i")]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[Regex("^a", "i"), Regex("^b", "i")]],
        msg="$zip should preserve Regex values",
    ),
    ExpressionTestCase(
        "timestamp_values",
        doc={"arr0": [Timestamp(1, 0)], "arr1": [Timestamp(2, 0)]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[Timestamp(1, 0), Timestamp(2, 0)]],
        msg="$zip should preserve Timestamp values",
    ),
    ExpressionTestCase(
        "minkey_maxkey",
        doc={"arr0": [MinKey()], "arr1": [MaxKey()]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[MinKey(), MaxKey()]],
        msg="$zip should preserve MinKey/MaxKey values",
    ),
    ExpressionTestCase(
        "uuid_values",
        doc={
            "arr0": [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))],
            "arr1": [Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef"))],
        },
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[
            [
                Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
                Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
            ]
        ],
        msg="$zip should preserve UUID binary values",
    ),
]

# Property [Mixed Types]: $zip processes arrays with mixed BSON types.
MIXED_BSON_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "mixed_bson_types",
        doc={"arr0": [1, "two", Int64(3)], "arr1": [Decimal128("4"), True, MinKey()]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[1, Decimal128("4")], ["two", True], [Int64(3), MinKey()]],
        msg="$zip should zip mixed BSON types preserving each",
    ),
]

# Property [Special Numerics]: $zip preserves NaN, Infinity, and boundary values.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "infinity_values",
        doc={"arr0": [FLOAT_INFINITY], "arr1": [FLOAT_NEGATIVE_INFINITY]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]],
        msg="$zip should preserve infinity values",
    ),
    ExpressionTestCase(
        "decimal128_infinity",
        doc={"arr0": [DECIMAL128_INFINITY], "arr1": [DECIMAL128_NEGATIVE_INFINITY]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]],
        msg="$zip should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        "boundary_values",
        doc={"arr0": [INT32_MIN, INT32_MAX], "arr1": [INT64_MIN, INT64_MAX]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[INT32_MIN, INT64_MIN], [INT32_MAX, INT64_MAX]],
        msg="$zip should preserve numeric boundary values",
    ),
    ExpressionTestCase(
        "negative_zero",
        doc={"arr0": [DOUBLE_NEGATIVE_ZERO], "arr1": [0]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[DOUBLE_NEGATIVE_ZERO, 0]],
        msg="$zip should preserve negative zero",
    ),
    ExpressionTestCase(
        "decimal128_nan",
        doc={"arr0": [DECIMAL128_NAN], "arr1": [Decimal128("1")]},
        expression={"$zip": {"inputs": ["$arr0", "$arr1"]}},
        expected=[[DECIMAL128_NAN, Decimal128("1")]],
        msg="$zip should preserve Decimal128 NaN",
    ),
]

# Property [BSON Defaults]: $zip uses BSON-typed default values correctly.
BSON_DEFAULTS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "default_int64",
        doc={"arr0": [1, 2, 3], "arr1": [Int64(10)]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, INT64_ZERO],
            }
        },
        expected=[[1, Int64(10)], [2, INT64_ZERO], [3, INT64_ZERO]],
        msg="$zip should use Int64 default value",
    ),
    ExpressionTestCase(
        "default_decimal128",
        doc={"arr0": [1, 2, 3], "arr1": [DECIMAL128_ONE_AND_HALF]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, DECIMAL128_ZERO],
            }
        },
        expected=[[1, DECIMAL128_ONE_AND_HALF], [2, DECIMAL128_ZERO], [3, DECIMAL128_ZERO]],
        msg="$zip should use Decimal128 default value",
    ),
    ExpressionTestCase(
        "default_datetime",
        doc={"arr0": [1, 2], "arr1": [datetime(2024, 1, 1, tzinfo=timezone.utc)]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, datetime(1970, 1, 1, tzinfo=timezone.utc)],
            }
        },
        expected=[
            [1, datetime(2024, 1, 1, tzinfo=timezone.utc)],
            [2, datetime(1970, 1, 1, tzinfo=timezone.utc)],
        ],
        msg="$zip should use datetime default value",
    ),
    ExpressionTestCase(
        "default_objectid",
        doc={"arr0": [1, 2], "arr1": [ObjectId("000000000000000000000001")]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, ObjectId("000000000000000000000000")],
            }
        },
        expected=[
            [1, ObjectId("000000000000000000000001")],
            [2, ObjectId("000000000000000000000000")],
        ],
        msg="$zip should use ObjectId default value",
    ),
    ExpressionTestCase(
        "default_timestamp",
        doc={"arr0": [1, 2], "arr1": [Timestamp(1, 0)]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, Timestamp(0, 0)],
            }
        },
        expected=[[1, Timestamp(1, 0)], [2, Timestamp(0, 0)]],
        msg="$zip should use Timestamp default value",
    ),
    ExpressionTestCase(
        "default_regex",
        doc={"arr0": [1, 2], "arr1": [Regex("^a", "i")]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, Regex(".*", "")],
            }
        },
        expected=[[1, Regex("^a", "i")], [2, Regex(".*", "")]],
        msg="$zip should use Regex default value",
    ),
    ExpressionTestCase(
        "default_minkey_maxkey",
        doc={"arr0": [1, 2], "arr1": [MinKey()]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, MaxKey()],
            }
        },
        expected=[[1, MinKey()], [2, MaxKey()]],
        msg="$zip should use MaxKey default value",
    ),
    ExpressionTestCase(
        "default_binary",
        doc={"arr0": [1, 2], "arr1": [Binary(b"\x01", 0)]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, Binary(b"\x00", 0)],
            }
        },
        expected=[[1, b"\x01"], [2, b"\x00"]],
        msg="$zip should use Binary default value",
    ),
]

# Property [Special Numeric Defaults]: $zip uses special numeric values as defaults.
SPECIAL_NUMERIC_DEFAULTS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "default_infinity",
        doc={"arr0": [1, 2], "arr1": [FLOAT_INFINITY]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, FLOAT_INFINITY],
            }
        },
        expected=[[1, FLOAT_INFINITY], [2, FLOAT_INFINITY]],
        msg="$zip should use infinity as default",
    ),
    ExpressionTestCase(
        "default_negative_infinity",
        doc={"arr0": [1, 2], "arr1": [FLOAT_NEGATIVE_INFINITY]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, FLOAT_NEGATIVE_INFINITY],
            }
        },
        expected=[[1, FLOAT_NEGATIVE_INFINITY], [2, FLOAT_NEGATIVE_INFINITY]],
        msg="$zip should use negative infinity as default",
    ),
    ExpressionTestCase(
        "default_negative_zero",
        doc={"arr0": [1, 2], "arr1": [DOUBLE_NEGATIVE_ZERO]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, DOUBLE_NEGATIVE_ZERO],
            }
        },
        expected=[[1, DOUBLE_NEGATIVE_ZERO], [2, DOUBLE_NEGATIVE_ZERO]],
        msg="$zip should use negative zero as default",
    ),
    ExpressionTestCase(
        "default_int32_boundaries",
        doc={"arr0": [1, 2], "arr1": [INT32_MIN]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, INT32_MAX],
            }
        },
        expected=[[1, INT32_MIN], [2, INT32_MAX]],
        msg="$zip should use INT32_MAX as default",
    ),
    ExpressionTestCase(
        "default_int64_boundaries",
        doc={"arr0": [1, 2], "arr1": [INT64_MIN]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, INT64_MAX],
            }
        },
        expected=[[1, INT64_MIN], [2, INT64_MAX]],
        msg="$zip should use INT64_MAX as default",
    ),
    ExpressionTestCase(
        "default_decimal128_infinity",
        doc={"arr0": [1, 2], "arr1": [DECIMAL128_INFINITY]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, DECIMAL128_NEGATIVE_INFINITY],
            }
        },
        expected=[[1, DECIMAL128_INFINITY], [2, DECIMAL128_NEGATIVE_INFINITY]],
        msg="$zip should use Decimal128 negative infinity as default",
    ),
    ExpressionTestCase(
        "default_decimal128_nan",
        doc={"arr0": [1, 2], "arr1": [DECIMAL128_NAN]},
        expression={
            "$zip": {
                "inputs": ["$arr0", "$arr1"],
                "useLongestLength": True,
                "defaults": [0, DECIMAL128_NAN],
            }
        },
        expected=[[1, DECIMAL128_NAN], [2, DECIMAL128_NAN]],
        msg="$zip should use Decimal128 NaN as default",
    ),
]

ALL_BSON_TESTS = (
    BSON_TYPE_TESTS
    + MIXED_BSON_TESTS
    + SPECIAL_NUMERIC_TESTS
    + BSON_DEFAULTS_TESTS
    + SPECIAL_NUMERIC_DEFAULTS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_zip_bson_type_preservation(collection, test):
    """Test $zip preserves BSON types in zipped output arrays."""
    if test.doc is None:
        result = execute_expression(collection, test.expression)
    else:
        result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
