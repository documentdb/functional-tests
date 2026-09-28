"""
BSON type and numeric equivalence tests for $in expression.

Tests searching for various BSON types and cross-type numeric matching.
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
    execute_expression_with_insert,
)
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Success: search for various BSON types
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "bson_int64",
        doc={"val": Int64(99), "arr": [Int64(99), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Int64 in array",
    ),
    ExpressionTestCase(
        "bson_decimal128",
        doc={"val": DECIMAL128_ONE_AND_HALF, "arr": [DECIMAL128_ONE_AND_HALF, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Decimal128 in array",
    ),
    ExpressionTestCase(
        "bson_datetime",
        doc={
            "val": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "arr": [datetime(2024, 1, 1, tzinfo=timezone.utc), 1],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find datetime in array",
    ),
    ExpressionTestCase(
        "bson_objectid",
        doc={
            "val": ObjectId("000000000000000000000001"),
            "arr": [ObjectId("000000000000000000000001"), 1],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find ObjectId in array",
    ),
    ExpressionTestCase(
        "bson_binary",
        doc={"val": Binary(b"\x01\x02", 0), "arr": [Binary(b"\x01\x02", 0), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Binary in array",
    ),
    ExpressionTestCase(
        "bson_regex",
        doc={"val": Regex("^abc", "i"), "arr": [Regex("^abc", "i"), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Regex in array",
    ),
    ExpressionTestCase(
        "bson_timestamp",
        doc={"val": Timestamp(1, 1), "arr": [Timestamp(1, 1), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Timestamp in array",
    ),
    ExpressionTestCase(
        "bson_minkey",
        doc={"val": MinKey(), "arr": [MinKey(), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find MinKey in array",
    ),
    ExpressionTestCase(
        "bson_maxkey",
        doc={"val": MaxKey(), "arr": [1, MaxKey()]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find MaxKey in array",
    ),
    ExpressionTestCase(
        "bson_uuid",
        doc={
            "val": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
            "arr": [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")), 1],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find UUID binary in array",
    ),
    # Special float values
    ExpressionTestCase(
        "float_infinity_in_array",
        doc={"val": FLOAT_INFINITY, "arr": [FLOAT_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Infinity in array",
    ),
    ExpressionTestCase(
        "float_neg_infinity_in_array",
        doc={"val": FLOAT_NEGATIVE_INFINITY, "arr": [FLOAT_NEGATIVE_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find -Infinity in array",
    ),
    ExpressionTestCase(
        "float_infinity_not_in_array",
        doc={"val": FLOAT_INFINITY, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="$in should not find Infinity in non-Infinity array",
    ),
    # Special Decimal128 values
    ExpressionTestCase(
        "decimal128_infinity_in_array",
        doc={"val": DECIMAL128_INFINITY, "arr": [DECIMAL128_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Decimal128 Infinity in array",
    ),
    ExpressionTestCase(
        "decimal128_neg_infinity_in_array",
        doc={"val": DECIMAL128_NEGATIVE_INFINITY, "arr": [DECIMAL128_NEGATIVE_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Decimal128 -Infinity in array",
    ),
    # NaN equality: NaN == NaN in BSON comparison (unlike IEEE 754)
    ExpressionTestCase(
        "float_nan_found",
        doc={"val": FLOAT_NAN, "arr": [FLOAT_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find NaN in array (BSON equality)",
    ),
    ExpressionTestCase(
        "decimal128_nan_found",
        doc={"val": DECIMAL128_NAN, "arr": [DECIMAL128_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find Decimal128 NaN in array (BSON equality)",
    ),
    ExpressionTestCase(
        "float_nan_matches_decimal128_nan",
        doc={"val": FLOAT_NAN, "arr": [DECIMAL128_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in float NaN should match Decimal128 NaN cross-type",
    ),
    ExpressionTestCase(
        "decimal128_nan_matches_float_nan",
        doc={"val": DECIMAL128_NAN, "arr": [FLOAT_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in decimal128 NaN should match float NaN cross-type",
    ),
    # Aggregation $in does NOT pattern-match regex against strings (unlike query $in)
    ExpressionTestCase(
        "regex_no_pattern_match",
        doc={"val": Regex("^a"), "arr": ["abc", "def"]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="$in regex should not pattern-match strings in aggregation $in",
    ),
]

# Success: numeric type equivalence
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "int_in_doubles",
        doc={"val": 1, "arr": [1.0, 2.0]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find int in doubles via numeric equivalence",
    ),
    ExpressionTestCase(
        "int_in_longs",
        doc={"val": 1, "arr": [Int64(1), 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find int in longs via numeric equivalence",
    ),
    ExpressionTestCase(
        "int_in_decimal128s",
        doc={"val": 1, "arr": [Decimal128("1"), 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find int in decimal128s via numeric equivalence",
    ),
    ExpressionTestCase(
        "double_in_ints",
        doc={"val": 1.0, "arr": [1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find double in ints via numeric equivalence",
    ),
    ExpressionTestCase(
        "long_in_ints",
        doc={"val": Int64(1), "arr": [1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find long in ints via numeric equivalence",
    ),
    ExpressionTestCase(
        "decimal128_in_ints",
        doc={"val": Decimal128("1"), "arr": [1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find decimal128 in ints via numeric equivalence",
    ),
    ExpressionTestCase(
        "decimal128_in_doubles",
        doc={"val": DECIMAL128_ONE_AND_HALF, "arr": [1.5, 2.5]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find decimal128 in doubles via numeric equivalence",
    ),
]

# Negative zero equivalence with positive zero
NEGATIVE_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        "double_neg_zero_matches_zero",
        doc={"val": DOUBLE_NEGATIVE_ZERO, "arr": [0, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should treat -0.0 as equivalent to 0",
    ),
    ExpressionTestCase(
        "zero_matches_double_neg_zero_in_array",
        doc={"val": 0, "arr": [DOUBLE_NEGATIVE_ZERO, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find 0 in array containing -0.0",
    ),
    ExpressionTestCase(
        "decimal128_neg_zero_matches_zero",
        doc={"val": DECIMAL128_NEGATIVE_ZERO, "arr": [0, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should treat Decimal128 -0 as equivalent to 0",
    ),
    ExpressionTestCase(
        "zero_matches_decimal128_neg_zero_in_array",
        doc={"val": 0, "arr": [DECIMAL128_NEGATIVE_ZERO, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find 0 in array containing Decimal128 -0",
    ),
]

# Aggregate and test
ALL_TESTS = BSON_TYPE_TESTS + NUMERIC_EQUIVALENCE_TESTS + NEGATIVE_ZERO_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_in_bson_insert(collection, test):
    """Test $in BSON type matching with values from inserted documents."""
    result = execute_expression_with_insert(collection, test.expression, test.doc)
    assert_expression_result(
        result, expected=test.expected, error_code=test.error_code, msg=test.msg
    )
