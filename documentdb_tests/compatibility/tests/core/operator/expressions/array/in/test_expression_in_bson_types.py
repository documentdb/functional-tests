"""
BSON type and numeric equivalence tests for $in expression.

Tests searching for various BSON types and cross-type numeric matching.
"""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.array.utils.array_test_case import (  # noqa: E501
    ArrayTestClass,
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
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Success: search for various BSON types
BSON_TYPE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="bson_int64",
        value=Int64(99),
        array=[Int64(99), 1],
        expected=True,
        msg="Should find Int64 in array",
    ),
    ArrayTestClass(
        id="bson_decimal128",
        value=Decimal128("1.5"),
        array=[Decimal128("1.5"), 2],
        expected=True,
        msg="Should find Decimal128 in array",
    ),
    ArrayTestClass(
        id="bson_datetime",
        value=datetime(2024, 1, 1, tzinfo=timezone.utc),
        array=[datetime(2024, 1, 1, tzinfo=timezone.utc), 1],
        expected=True,
        msg="Should find datetime in array",
    ),
    ArrayTestClass(
        id="bson_objectid",
        value=ObjectId("000000000000000000000001"),
        array=[ObjectId("000000000000000000000001"), 1],
        expected=True,
        msg="Should find ObjectId in array",
    ),
    ArrayTestClass(
        id="bson_binary",
        value=Binary(b"\x01\x02", 0),
        array=[Binary(b"\x01\x02", 0), 1],
        expected=True,
        msg="Should find Binary in array",
    ),
    ArrayTestClass(
        id="bson_regex",
        value=Regex("^abc", "i"),
        array=[Regex("^abc", "i"), 1],
        expected=True,
        msg="Should find Regex in array",
    ),
    ArrayTestClass(
        id="bson_timestamp",
        value=Timestamp(1, 1),
        array=[Timestamp(1, 1), 1],
        expected=True,
        msg="Should find Timestamp in array",
    ),
    ArrayTestClass(
        id="bson_minkey",
        value=MinKey(),
        array=[MinKey(), 1],
        expected=True,
        msg="Should find MinKey in array",
    ),
    ArrayTestClass(
        id="bson_maxkey",
        value=MaxKey(),
        array=[1, MaxKey()],
        expected=True,
        msg="Should find MaxKey in array",
    ),
    ArrayTestClass(
        id="bson_uuid",
        value=Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
        array=[Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")), 1],
        expected=True,
        msg="Should find UUID binary in array",
    ),
    # Special float values
    ArrayTestClass(
        id="float_infinity_in_array",
        value=FLOAT_INFINITY,
        array=[FLOAT_INFINITY, 1],
        expected=True,
        msg="Should find Infinity in array",
    ),
    ArrayTestClass(
        id="float_neg_infinity_in_array",
        value=FLOAT_NEGATIVE_INFINITY,
        array=[FLOAT_NEGATIVE_INFINITY, 1],
        expected=True,
        msg="Should find -Infinity in array",
    ),
    ArrayTestClass(
        id="float_infinity_not_in_array",
        value=FLOAT_INFINITY,
        array=[1, 2, 3],
        expected=False,
        msg="Should not find Infinity in non-Infinity array",
    ),
    # Special Decimal128 values
    ArrayTestClass(
        id="decimal128_infinity_in_array",
        value=DECIMAL128_INFINITY,
        array=[DECIMAL128_INFINITY, 1],
        expected=True,
        msg="Should find Decimal128 Infinity in array",
    ),
    ArrayTestClass(
        id="decimal128_neg_infinity_in_array",
        value=DECIMAL128_NEGATIVE_INFINITY,
        array=[DECIMAL128_NEGATIVE_INFINITY, 1],
        expected=True,
        msg="Should find Decimal128 -Infinity in array",
    ),
    # NaN equality: NaN == NaN in BSON comparison (unlike IEEE 754)
    ArrayTestClass(
        id="float_nan_found",
        value=FLOAT_NAN,
        array=[FLOAT_NAN, 1],
        expected=True,
        msg="Should find NaN in array (BSON equality)",
    ),
    ArrayTestClass(
        id="decimal128_nan_found",
        value=DECIMAL128_NAN,
        array=[DECIMAL128_NAN, 1],
        expected=True,
        msg="Should find Decimal128 NaN in array (BSON equality)",
    ),
    ArrayTestClass(
        id="float_nan_matches_decimal128_nan",
        value=FLOAT_NAN,
        array=[DECIMAL128_NAN, 1],
        expected=True,
        msg="float NaN should match Decimal128 NaN cross-type",
    ),
    ArrayTestClass(
        id="decimal128_nan_matches_float_nan",
        value=DECIMAL128_NAN,
        array=[FLOAT_NAN, 1],
        expected=True,
        msg="Decimal128 NaN should match float NaN cross-type",
    ),
    # Aggregation $in does NOT pattern-match regex against strings (unlike query $in)
    ArrayTestClass(
        id="regex_no_pattern_match",
        value=Regex("^a"),
        array=["abc", "def"],
        expected=False,
        msg="Regex should not pattern-match strings in aggregation $in",
    ),
]

# Success: numeric type equivalence
NUMERIC_EQUIVALENCE_TESTS: list[ArrayTestClass] = [
    ArrayTestClass(
        id="int_in_doubles",
        value=1,
        array=[1.0, 2.0],
        expected=True,
        msg="Should find int in doubles via numeric equivalence",
    ),
    ArrayTestClass(
        id="int_in_longs",
        value=1,
        array=[Int64(1), 2],
        expected=True,
        msg="Should find int in longs via numeric equivalence",
    ),
    ArrayTestClass(
        id="int_in_decimal128s",
        value=1,
        array=[Decimal128("1"), 2],
        expected=True,
        msg="Should find int in decimal128s via numeric equivalence",
    ),
    ArrayTestClass(
        id="double_in_ints",
        value=1.0,
        array=[1, 2],
        expected=True,
        msg="Should find double in ints via numeric equivalence",
    ),
    ArrayTestClass(
        id="long_in_ints",
        value=Int64(1),
        array=[1, 2],
        expected=True,
        msg="Should find long in ints via numeric equivalence",
    ),
    ArrayTestClass(
        id="decimal128_in_ints",
        value=Decimal128("1"),
        array=[1, 2],
        expected=True,
        msg="Should find decimal128 in ints via numeric equivalence",
    ),
    ArrayTestClass(
        id="decimal128_in_doubles",
        value=Decimal128("1.5"),
        array=[1.5, 2.5],
        expected=True,
        msg="Should find decimal128 in doubles via numeric equivalence",
    ),
]

# Aggregate and test
ALL_TESTS = BSON_TYPE_TESTS + NUMERIC_EQUIVALENCE_TESTS

TEST_SUBSET_FOR_LITERAL = [
    BSON_TYPE_TESTS[0],  # bson_int64
    BSON_TYPE_TESTS[-1],  # decimal128_nan_found
    NUMERIC_EQUIVALENCE_TESTS[0],  # int_in_doubles
]


@pytest.mark.parametrize("test", pytest_params(TEST_SUBSET_FOR_LITERAL))
def test_in_literal(collection, test):
    """Test $in BSON types with literal values."""
    result = execute_expression(collection, {"$in": [test.value, test.array]})
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_in_insert(collection, test):
    """Test $in BSON types with values from inserted documents."""
    result = execute_expression_with_insert(
        collection, {"$in": ["$val", "$arr"]}, {"val": test.value, "arr": test.array}
    )
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
