"""
BSON type element preservation tests for $reverseArray expression.

Tests that various BSON types are preserved when reversing arrays,
including special numeric values and boundary values.
"""

from datetime import datetime, timezone
from uuid import UUID

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
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TRAILING_ZERO,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

# Property [Literal-path parity]: representative BSON-type cases also run
# through the literal-value path (not just via inserted documents). Defined
# here directly (not by positional index into the groups below) so the
# mapping is name-stable, and appended to ALL_TESTS below so they also get
# insert coverage.
TEST_SUBSET_FOR_LITERAL: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_values",
        expression={"$reverseArray": {"$literal": [Int64(1), Int64(2), Int64(3)]}},
        doc={"arr": [Int64(1), Int64(2), Int64(3)]},
        expected=[Int64(3), Int64(2), Int64(1)],
        msg="Should preserve Int64 values",
    ),
    ExpressionTestCase(
        id="binary_values",
        expression={"$reverseArray": {"$literal": [Binary(b"\x01", 0), Binary(b"\x02", 0)]}},
        doc={"arr": [Binary(b"\x01", 0), Binary(b"\x02", 0)]},
        expected=[b"\x02", b"\x01"],
        msg="Should preserve Binary values",
    ),
    ExpressionTestCase(
        id="mixed_bson_types",
        expression={
            "$reverseArray": {
                "$literal": [1, "two", Int64(3), Decimal128("4"), True, None, MinKey()]
            }
        },
        doc={"arr": [1, "two", Int64(3), Decimal128("4"), True, None, MinKey()]},
        expected=[MinKey(), None, True, Decimal128("4"), Int64(3), "two", 1],
        msg="Should reverse mixed BSON types preserving each",
    ),
    ExpressionTestCase(
        id="infinity_values",
        expression={"$reverseArray": {"$literal": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY]}},
        doc={"arr": [FLOAT_NEGATIVE_INFINITY, 0, FLOAT_INFINITY]},
        expected=[FLOAT_INFINITY, 0, FLOAT_NEGATIVE_INFINITY],
        msg="Should preserve infinity values",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_reverseArray_bson_literal(collection, test):
    """Test $reverseArray BSON types with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


# Property [BSON type preservation]: each BSON value type survives reversal
# unchanged — no coercion, widening, or precision loss (e.g. Binary subtype
# and UUID binary round-trip exactly, Regex flags are preserved).
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="decimal128_values",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF, Decimal128("3.5")]},
        expected=[Decimal128("3.5"), DECIMAL128_TWO_AND_HALF, DECIMAL128_ONE_AND_HALF],
        msg="Should preserve Decimal128 values",
    ),
    ExpressionTestCase(
        id="datetime_values",
        expression={"$reverseArray": "$arr"},
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 6, 1, tzinfo=timezone.utc),
                datetime(2024, 12, 1, tzinfo=timezone.utc),
            ]
        },
        expected=[
            datetime(2024, 12, 1, tzinfo=timezone.utc),
            datetime(2024, 6, 1, tzinfo=timezone.utc),
            datetime(2024, 1, 1, tzinfo=timezone.utc),
        ],
        msg="Should preserve datetime values",
    ),
    ExpressionTestCase(
        id="objectid_values",
        expression={"$reverseArray": "$arr"},
        doc={
            "arr": [
                ObjectId("000000000000000000000001"),
                ObjectId("000000000000000000000002"),
                ObjectId("000000000000000000000003"),
            ]
        },
        expected=[
            ObjectId("000000000000000000000003"),
            ObjectId("000000000000000000000002"),
            ObjectId("000000000000000000000001"),
        ],
        msg="Should preserve ObjectId values",
    ),
    ExpressionTestCase(
        id="binary_subtype_preservation",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [Binary(b"\x01", 128), Binary(b"\x02", 128)]},
        expected=[Binary(b"\x02", 128), Binary(b"\x01", 128)],
        msg="Should preserve Binary subtype",
    ),
    ExpressionTestCase(
        id="regex_values",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")]},
        expected=[Regex("^b", "i"), Regex("^a", "i")],
        msg="Should preserve Regex values",
    ),
    ExpressionTestCase(
        id="timestamp_values",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [Timestamp(1, 0), Timestamp(2, 0), Timestamp(3, 0)]},
        expected=[Timestamp(3, 0), Timestamp(2, 0), Timestamp(1, 0)],
        msg="Should preserve Timestamp values",
    ),
    ExpressionTestCase(
        id="minkey_maxkey",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [MinKey(), MaxKey()]},
        expected=[MaxKey(), MinKey()],
        msg="Should preserve MinKey/MaxKey values",
    ),
    ExpressionTestCase(
        id="uuid_values",
        expression={"$reverseArray": "$arr"},
        doc={
            "arr": [
                Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
                Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
            ]
        },
        expected=[
            Binary.from_uuid(UUID("fedcba98-7654-3210-0123-456789abcdef")),
            Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
        ],
        msg="Should preserve UUID binary values",
    ),
]

# Property [Special numeric value preservation]: IEEE-754/Decimal128 special
# values (±Infinity) and numeric boundary values (Int32/Int64 min/max) pass
# through reversal without normalization, precision loss, or overflow.
SPECIAL_NUMERIC_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="decimal128_infinity",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [DECIMAL128_NEGATIVE_INFINITY, DECIMAL128_ZERO, DECIMAL128_INFINITY]},
        expected=[DECIMAL128_INFINITY, DECIMAL128_ZERO, DECIMAL128_NEGATIVE_INFINITY],
        msg="Should preserve Decimal128 infinity values",
    ),
    ExpressionTestCase(
        id="boundary_values",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [INT32_MIN, INT32_MAX, INT64_MIN, INT64_MAX]},
        expected=[INT64_MAX, INT64_MIN, INT32_MAX, INT32_MIN],
        msg="Should preserve numeric boundary values",
    ),
]

# Property [Element-level numeric edge preservation]: subtle numeric
# representations (Decimal128 trailing zeros, double/Decimal128 negative
# zero, Decimal128 NaN) as individual array elements survive reversal without
# normalization or collapsing distinct representations.
ELEMENT_PRESERVATION_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="decimal128_trailing_zeros",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [DECIMAL128_TRAILING_ZERO, Decimal128("1.00"), Decimal128("1.000")]},
        expected=[Decimal128("1.000"), Decimal128("1.00"), DECIMAL128_TRAILING_ZERO],
        msg="Decimal128 trailing zeros preserved",
    ),
    ExpressionTestCase(
        id="double_negative_zero",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [1, DOUBLE_NEGATIVE_ZERO, -1]},
        expected=[-1, DOUBLE_NEGATIVE_ZERO, 1],
        msg="Double negative zero preserved",
    ),
    ExpressionTestCase(
        id="decimal128_negative_zero",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [Decimal128("1"), DECIMAL128_NEGATIVE_ZERO]},
        expected=[DECIMAL128_NEGATIVE_ZERO, Decimal128("1")],
        msg="Decimal128 negative zero preserved",
    ),
    ExpressionTestCase(
        id="decimal128_nan_element",
        expression={"$reverseArray": "$arr"},
        doc={"arr": [DECIMAL128_NAN, Decimal128("1")]},
        expected=[Decimal128("1"), DECIMAL128_NAN],
        msg="Decimal128 NaN element preserved",
    ),
]

ALL_TESTS = (
    BSON_TYPE_TESTS + SPECIAL_NUMERIC_TESTS + ELEMENT_PRESERVATION_TESTS + TEST_SUBSET_FOR_LITERAL
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_reverseArray_bson_insert(collection, test):
    """Test $reverseArray BSON types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
