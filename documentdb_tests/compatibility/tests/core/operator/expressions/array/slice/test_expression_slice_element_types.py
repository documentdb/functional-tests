"""
Numeric type and element type preservation tests for $slice expression.

Tests that n/position accept any integral numeric type (normalizing non-canonical
forms like -0.0) and that sliced elements, including special numeric values, retain
their original BSON type when passed as field references or literal arguments.
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
    DECIMAL128_TWO_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Numeric Argument Types]: n and position accept any integral numeric type,
# and non-canonical representations of an integer (negative zero, alternate Decimal128
# exponent forms) normalize to their integer value.
NUMERIC_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "n_int64",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": Int64(2)},
        expected=[1, 2],
        msg="$slice should accept Int64 n",
    ),
    ExpressionTestCase(
        "n_double_integral",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": 2.0},
        expected=[1, 2],
        msg="$slice should accept an integral double n",
    ),
    ExpressionTestCase(
        "n_decimal128_integral",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": Decimal128("2")},
        expected=[1, 2],
        msg="$slice should accept Decimal128 n",
    ),
    ExpressionTestCase(
        "n_neg_zero_double",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": DOUBLE_NEGATIVE_ZERO},
        expected=[],
        msg="$slice should treat -0.0 n as 0",
    ),
    ExpressionTestCase(
        "n_neg_zero_decimal128",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, 2, 3], "n": DECIMAL128_NEGATIVE_ZERO},
        expected=[],
        msg="$slice should treat decimal128 -0 n as 0",
    ),
    ExpressionTestCase(
        "pos_int64",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": Int64(1), "n": 2},
        expected=[2, 3],
        msg="$slice should accept Int64 position",
    ),
    ExpressionTestCase(
        "pos_double_integral",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": 1.0, "n": 2},
        expected=[2, 3],
        msg="$slice should accept an integral double position",
    ),
    ExpressionTestCase(
        "pos_decimal128_integral",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3, 4, 5], "pos": Decimal128("1"), "n": 2},
        expected=[2, 3],
        msg="$slice should accept Decimal128 position",
    ),
    ExpressionTestCase(
        "pos_neg_zero_double",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": DOUBLE_NEGATIVE_ZERO, "n": 2},
        expected=[1, 2],
        msg="$slice should treat -0.0 position as 0",
    ),
    ExpressionTestCase(
        "pos_neg_zero_decimal128",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": DECIMAL128_NEGATIVE_ZERO, "n": 2},
        expected=[1, 2],
        msg="$slice should treat Decimal128 -0 position as 0",
    ),
    ExpressionTestCase(
        "pos_decimal128_10E_neg1",
        expression={"$slice": ["$arr", "$pos", "$n"]},
        doc={"arr": [1, 2, 3], "pos": Decimal128("10E-1"), "n": 2},
        expected=[2, 3],
        msg="$slice should treat Decimal128 10E-1 position as 1",
    ),
]

# Property [Element Preservation]: sliced elements retain their original BSON type and value.
ELEMENT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "elem_int64",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [Int64(99), Int64(100)], "n": 1},
        expected=[Int64(99)],
        msg="$slice should preserve Int64 elements",
    ),
    ExpressionTestCase(
        "elem_decimal128",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [DECIMAL128_ONE_AND_HALF, DECIMAL128_TWO_AND_HALF], "n": 1},
        expected=[DECIMAL128_ONE_AND_HALF],
        msg="$slice should preserve Decimal128 elements",
    ),
    ExpressionTestCase(
        "elem_datetime",
        expression={"$slice": ["$arr", "$n"]},
        doc={
            "arr": [
                datetime(2024, 1, 1, tzinfo=timezone.utc),
                datetime(2024, 2, 1, tzinfo=timezone.utc),
            ],
            "n": 1,
        },
        expected=[datetime(2024, 1, 1, tzinfo=timezone.utc)],
        msg="$slice should preserve datetime elements",
    ),
    ExpressionTestCase(
        "elem_objectid",
        expression={"$slice": ["$arr", "$n"]},
        doc={
            "arr": [ObjectId("000000000000000000000001"), ObjectId("000000000000000000000002")],
            "n": 1,
        },
        expected=[ObjectId("000000000000000000000001")],
        msg="$slice should preserve ObjectId elements",
    ),
    ExpressionTestCase(
        "elem_binary",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [Binary(b"\x01", 0), Binary(b"\x02", 0)], "n": 1},
        expected=[b"\x01"],
        msg="$slice should preserve binary elements",
    ),
    ExpressionTestCase(
        "elem_regex",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [Regex("^a", "i"), Regex("^b", "i")], "n": 1},
        expected=[Regex("^a", "i")],
        msg="$slice should preserve regex elements",
    ),
    ExpressionTestCase(
        "elem_timestamp",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [Timestamp(1, 1), Timestamp(2, 2)], "n": 1},
        expected=[Timestamp(1, 1)],
        msg="$slice should preserve timestamp elements",
    ),
    ExpressionTestCase(
        "elem_minkey",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [MinKey(), 1], "n": 1},
        expected=[MinKey()],
        msg="$slice should preserve MinKey elements",
    ),
    ExpressionTestCase(
        "elem_maxkey",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [1, MaxKey()], "n": -1},
        expected=[MaxKey()],
        msg="$slice should preserve MaxKey elements",
    ),
    ExpressionTestCase(
        "elem_bool",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [True, False], "n": 1},
        expected=[True],
        msg="$slice should preserve bool elements",
    ),
    ExpressionTestCase(
        "elem_null",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [None, 1], "n": 1},
        expected=[None],
        msg="$slice should preserve null elements",
    ),
    ExpressionTestCase(
        "elem_nested_array",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [[1, 2], [3, 4]], "n": 1},
        expected=[[1, 2]],
        msg="$slice should preserve nested array elements",
    ),
    ExpressionTestCase(
        "elem_object",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [{"a": 1}, {"b": 2}], "n": 1},
        expected=[{"a": 1}],
        msg="$slice should preserve object elements",
    ),
    ExpressionTestCase(
        "elem_uuid",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")), 1], "n": 1},
        expected=[Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210"))],
        msg="$slice should preserve UUID binary elements",
    ),
    ExpressionTestCase(
        "elem_float_nan",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [FLOAT_NAN, 1, 2], "n": 1},
        expected=[pytest.approx(FLOAT_NAN, nan_ok=True)],
        msg="$slice should preserve NaN elements",
    ),
    ExpressionTestCase(
        "elem_float_infinity",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [FLOAT_INFINITY, 1], "n": 1},
        expected=[FLOAT_INFINITY],
        msg="$slice should preserve Infinity elements",
    ),
    ExpressionTestCase(
        "elem_float_neg_infinity",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [FLOAT_NEGATIVE_INFINITY, 1], "n": 1},
        expected=[FLOAT_NEGATIVE_INFINITY],
        msg="$slice should preserve -Infinity elements",
    ),
    ExpressionTestCase(
        "elem_decimal128_nan",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [DECIMAL128_NAN, 1], "n": 1},
        expected=[DECIMAL128_NAN],
        msg="$slice should preserve Decimal128 NaN elements",
    ),
    ExpressionTestCase(
        "elem_decimal128_infinity",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [DECIMAL128_INFINITY, 1], "n": 1},
        expected=[DECIMAL128_INFINITY],
        msg="$slice should preserve Decimal128 Infinity elements",
    ),
    ExpressionTestCase(
        "elem_decimal128_neg_infinity",
        expression={"$slice": ["$arr", "$n"]},
        doc={"arr": [DECIMAL128_NEGATIVE_INFINITY, 1], "n": 1},
        expected=[DECIMAL128_NEGATIVE_INFINITY],
        msg="$slice should preserve Decimal128 -Infinity elements",
    ),
]

ALL_TESTS = NUMERIC_TYPE_TESTS + ELEMENT_TYPE_TESTS

# Property [Literal Arguments]: $slice accepts literal arrays and numeric arguments.
LITERAL_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "literal_n_int64",
        expression={"$slice": [[1, 2, 3], Int64(2)]},
        expected=[1, 2],
        msg="$slice should accept a literal Int64 n",
    ),
    ExpressionTestCase(
        "literal_elem_int64",
        expression={"$slice": [[Int64(99), Int64(100)], 1]},
        expected=[Int64(99)],
        msg="$slice should preserve Int64 elements from a literal array",
    ),
    ExpressionTestCase(
        "literal_elem_decimal128_neg_infinity",
        expression={"$slice": [[DECIMAL128_NEGATIVE_INFINITY, 1], 1]},
        expected=[DECIMAL128_NEGATIVE_INFINITY],
        msg="$slice should preserve a Decimal128 -Infinity element from a literal array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(LITERAL_TESTS))
def test_slice_literal(collection, test):
    """Test $slice element/numeric types with literal values."""
    result = execute_expression(collection, test.expression)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_slice_insert(collection, test):
    """Test $slice element/numeric types with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
