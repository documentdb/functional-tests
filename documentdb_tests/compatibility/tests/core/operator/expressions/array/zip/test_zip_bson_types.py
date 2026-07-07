"""
BSON type element preservation tests for $zip expression.

Tests that various BSON types are preserved when zipping arrays.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.zip.utils.zip_common import (  # noqa: E501
    ZipTest,
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
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# ---------------------------------------------------------------------------
# BSON types preserved after zipping
# ---------------------------------------------------------------------------
BSON_TYPE_TESTS: list[ZipTest] = [
    ZipTest(
        id="int64_values",
        inputs=[[Int64(1)], [Int64(2)]],
        expected=[[Int64(1), Int64(2)]],
        msg="Should preserve Int64 values",
    ),
    ZipTest(
        id="decimal128_values",
        inputs=[[Decimal128("1.5")], [Decimal128("2.5")]],
        expected=[[Decimal128("1.5"), Decimal128("2.5")]],
        msg="Should preserve Decimal128 values",
    ),
    ZipTest(
        id="datetime_values",
        inputs=[
            [datetime(2024, 1, 1, tzinfo=timezone.utc)],
            [datetime(2024, 6, 1, tzinfo=timezone.utc)],
        ],
        expected=[
            [datetime(2024, 1, 1, tzinfo=timezone.utc), datetime(2024, 6, 1, tzinfo=timezone.utc)]
        ],
        msg="Should preserve datetime values",
    ),
    ZipTest(
        id="objectid_values",
        inputs=[
            [ObjectId("000000000000000000000001")],
            [ObjectId("000000000000000000000002")],
        ],
        expected=[[ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")]],
        msg="Should preserve ObjectId values",
    ),
    ZipTest(
        id="binary_values",
        inputs=[[Binary(b"\x01", 0)], [Binary(b"\x02", 0)]],
        expected=[[b"\x01", b"\x02"]],
        msg="Should preserve Binary values",
    ),
    ZipTest(
        id="regex_values",
        inputs=[[Regex("^a", "i")], [Regex("^b", "i")]],
        expected=[[Regex("^a", "i"), Regex("^b", "i")]],
        msg="Should preserve Regex values",
    ),
    ZipTest(
        id="timestamp_values",
        inputs=[[Timestamp(1, 0)], [Timestamp(2, 0)]],
        expected=[[Timestamp(1, 0), Timestamp(2, 0)]],
        msg="Should preserve Timestamp values",
    ),
    ZipTest(
        id="minkey_maxkey",
        inputs=[[MinKey()], [MaxKey()]],
        expected=[[MinKey(), MaxKey()]],
        msg="Should preserve MinKey/MaxKey values",
    ),
    ZipTest(
        id="uuid_values",
        inputs=[
            [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))],
            [Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef"))],
        ],
        expected=[
            [
                Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
                Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
            ]
        ],
        msg="Should preserve UUID binary values",
    ),
]

# ---------------------------------------------------------------------------
# Mixed BSON types across arrays
# ---------------------------------------------------------------------------
MIXED_BSON_TESTS: list[ZipTest] = [
    ZipTest(
        id="mixed_bson_types",
        inputs=[[1, "two", Int64(3)], [Decimal128("4"), True, MinKey()]],
        expected=[[1, Decimal128("4")], ["two", True], [Int64(3), MinKey()]],
        msg="Should zip mixed BSON types preserving each",
    ),
]

# ---------------------------------------------------------------------------
# Special numeric values as elements
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_TESTS: list[ZipTest] = [
    ZipTest(
        id="infinity_values",
        inputs=[[FLOAT_INFINITY], [FLOAT_NEGATIVE_INFINITY]],
        expected=[[FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY]],
        msg="Should preserve infinity values",
    ),
    ZipTest(
        id="decimal128_infinity",
        inputs=[[DECIMAL128_INFINITY], [DECIMAL128_NEGATIVE_INFINITY]],
        expected=[[DECIMAL128_INFINITY, DECIMAL128_NEGATIVE_INFINITY]],
        msg="Should preserve Decimal128 infinity values",
    ),
    ZipTest(
        id="boundary_values",
        inputs=[[INT32_MIN, INT32_MAX], [INT64_MIN, INT64_MAX]],
        expected=[[INT32_MIN, INT64_MIN], [INT32_MAX, INT64_MAX]],
        msg="Should preserve numeric boundary values",
    ),
    ZipTest(
        id="negative_zero",
        inputs=[[DOUBLE_NEGATIVE_ZERO], [0]],
        expected=[[DOUBLE_NEGATIVE_ZERO, 0]],
        msg="Should preserve negative zero",
    ),
    ZipTest(
        id="decimal128_nan",
        inputs=[[DECIMAL128_NAN], [Decimal128("1")]],
        expected=[[DECIMAL128_NAN, Decimal128("1")]],
        msg="Should preserve Decimal128 NaN",
    ),
]

# ---------------------------------------------------------------------------
# Defaults with BSON types
# ---------------------------------------------------------------------------
BSON_DEFAULTS_TESTS: list[ZipTest] = [
    ZipTest(
        id="default_int64",
        inputs=[[1, 2, 3], [Int64(10)]],
        use_longest_length=True,
        defaults=[0, Int64(0)],
        expected=[[1, Int64(10)], [2, Int64(0)], [3, Int64(0)]],
        msg="Should use Int64 default value",
    ),
    ZipTest(
        id="default_decimal128",
        inputs=[[1, 2, 3], [Decimal128("1.5")]],
        use_longest_length=True,
        defaults=[0, Decimal128("0")],
        expected=[[1, Decimal128("1.5")], [2, Decimal128("0")], [3, Decimal128("0")]],
        msg="Should use Decimal128 default value",
    ),
    ZipTest(
        id="default_datetime",
        inputs=[[1, 2], [datetime(2024, 1, 1, tzinfo=timezone.utc)]],
        use_longest_length=True,
        defaults=[0, datetime(1970, 1, 1, tzinfo=timezone.utc)],
        expected=[
            [1, datetime(2024, 1, 1, tzinfo=timezone.utc)],
            [2, datetime(1970, 1, 1, tzinfo=timezone.utc)],
        ],
        msg="Should use datetime default value",
    ),
    ZipTest(
        id="default_objectid",
        inputs=[[1, 2], [ObjectId("000000000000000000000001")]],
        use_longest_length=True,
        defaults=[0, ObjectId("000000000000000000000000")],
        expected=[
            [1, ObjectId("000000000000000000000001")],
            [2, ObjectId("000000000000000000000000")],
        ],
        msg="Should use ObjectId default value",
    ),
    ZipTest(
        id="default_timestamp",
        inputs=[[1, 2], [Timestamp(1, 0)]],
        use_longest_length=True,
        defaults=[0, Timestamp(0, 0)],
        expected=[[1, Timestamp(1, 0)], [2, Timestamp(0, 0)]],
        msg="Should use Timestamp default value",
    ),
    ZipTest(
        id="default_regex",
        inputs=[[1, 2], [Regex("^a", "i")]],
        use_longest_length=True,
        defaults=[0, Regex(".*", "")],
        expected=[[1, Regex("^a", "i")], [2, Regex(".*", "")]],
        msg="Should use Regex default value",
    ),
    ZipTest(
        id="default_minkey_maxkey",
        inputs=[[1, 2], [MinKey()]],
        use_longest_length=True,
        defaults=[0, MaxKey()],
        expected=[[1, MinKey()], [2, MaxKey()]],
        msg="Should use MaxKey default value",
    ),
    ZipTest(
        id="default_binary",
        inputs=[[1, 2], [Binary(b"\x01", 0)]],
        use_longest_length=True,
        defaults=[0, Binary(b"\x00", 0)],
        expected=[[1, b"\x01"], [2, b"\x00"]],
        msg="Should use Binary default value",
    ),
]

# ---------------------------------------------------------------------------
# Defaults with special numeric values
# ---------------------------------------------------------------------------
SPECIAL_NUMERIC_DEFAULTS_TESTS: list[ZipTest] = [
    ZipTest(
        id="default_infinity",
        inputs=[[1, 2], [FLOAT_INFINITY]],
        use_longest_length=True,
        defaults=[0, FLOAT_INFINITY],
        expected=[[1, FLOAT_INFINITY], [2, FLOAT_INFINITY]],
        msg="Should use infinity as default",
    ),
    ZipTest(
        id="default_negative_infinity",
        inputs=[[1, 2], [FLOAT_NEGATIVE_INFINITY]],
        use_longest_length=True,
        defaults=[0, FLOAT_NEGATIVE_INFINITY],
        expected=[[1, FLOAT_NEGATIVE_INFINITY], [2, FLOAT_NEGATIVE_INFINITY]],
        msg="Should use negative infinity as default",
    ),
    ZipTest(
        id="default_negative_zero",
        inputs=[[1, 2], [DOUBLE_NEGATIVE_ZERO]],
        use_longest_length=True,
        defaults=[0, DOUBLE_NEGATIVE_ZERO],
        expected=[[1, DOUBLE_NEGATIVE_ZERO], [2, DOUBLE_NEGATIVE_ZERO]],
        msg="Should use negative zero as default",
    ),
    ZipTest(
        id="default_int32_boundaries",
        inputs=[[1, 2], [INT32_MIN]],
        use_longest_length=True,
        defaults=[0, INT32_MAX],
        expected=[[1, INT32_MIN], [2, INT32_MAX]],
        msg="Should use INT32_MAX as default",
    ),
    ZipTest(
        id="default_int64_boundaries",
        inputs=[[1, 2], [INT64_MIN]],
        use_longest_length=True,
        defaults=[0, INT64_MAX],
        expected=[[1, INT64_MIN], [2, INT64_MAX]],
        msg="Should use INT64_MAX as default",
    ),
    ZipTest(
        id="default_decimal128_infinity",
        inputs=[[1, 2], [DECIMAL128_INFINITY]],
        use_longest_length=True,
        defaults=[0, DECIMAL128_NEGATIVE_INFINITY],
        expected=[[1, DECIMAL128_INFINITY], [2, DECIMAL128_NEGATIVE_INFINITY]],
        msg="Should use Decimal128 negative infinity as default",
    ),
    ZipTest(
        id="default_decimal128_nan",
        inputs=[[1, 2], [DECIMAL128_NAN]],
        use_longest_length=True,
        defaults=[0, DECIMAL128_NAN],
        expected=[[1, DECIMAL128_NAN], [2, DECIMAL128_NAN]],
        msg="Should use Decimal128 NaN as default",
    ),
]

# ---------------------------------------------------------------------------
# Aggregate and test
# ---------------------------------------------------------------------------
ALL_BSON_TESTS = (
    BSON_TYPE_TESTS
    + MIXED_BSON_TESTS
    + SPECIAL_NUMERIC_TESTS
    + BSON_DEFAULTS_TESTS
    + SPECIAL_NUMERIC_DEFAULTS_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_BSON_TESTS))
def test_zip_bson_insert(collection, test):
    """Test $zip BSON types with values from inserted documents."""
    expr = {"inputs": [f"$arr{i}" for i in range(len(test.inputs))]}
    if test.use_longest_length is not None:
        expr["useLongestLength"] = test.use_longest_length
    if test.defaults is not None:
        expr["defaults"] = test.defaults
    doc = {f"arr{i}": arr for i, arr in enumerate(test.inputs)}
    result = execute_expression_with_insert(collection, {"$zip": expr}, doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


TEST_SUBSET_FOR_LITERAL = [
    BSON_TYPE_TESTS[0],  # int64_values
    BSON_TYPE_TESTS[4],  # binary_values
    MIXED_BSON_TESTS[0],  # mixed_bson_types
    SPECIAL_NUMERIC_TESTS[0],  # infinity_values
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_zip_bson_literal(collection, test):
    """Test $zip BSON types with literal values."""
    expr = {"inputs": [{"$literal": a} for a in test.inputs]}
    if test.use_longest_length is not None:
        expr["useLongestLength"] = test.use_longest_length
    if test.defaults is not None:
        expr["defaults"] = test.defaults
    result = execute_expression(collection, {"$zip": expr})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
