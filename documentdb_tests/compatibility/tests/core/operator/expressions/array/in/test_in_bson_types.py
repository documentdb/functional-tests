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
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Success: search for various BSON types
BSON_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="bson_int64",
        doc={"val": Int64(99), "arr": [Int64(99), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Int64 in array",
    ),
    ExpressionTestCase(
        id="bson_decimal128",
        doc={"val": Decimal128("1.5"), "arr": [Decimal128("1.5"), 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Decimal128 in array",
    ),
    ExpressionTestCase(
        id="bson_datetime",
        doc={
            "val": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "arr": [datetime(2024, 1, 1, tzinfo=timezone.utc), 1],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find datetime in array",
    ),
    ExpressionTestCase(
        id="bson_objectid",
        doc={
            "val": ObjectId("000000000000000000000001"),
            "arr": [ObjectId("000000000000000000000001"), 1],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find ObjectId in array",
    ),
    ExpressionTestCase(
        id="bson_binary",
        doc={"val": Binary(b"\x01\x02", 0), "arr": [Binary(b"\x01\x02", 0), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Binary in array",
    ),
    ExpressionTestCase(
        id="bson_regex",
        doc={"val": Regex("^abc", "i"), "arr": [Regex("^abc", "i"), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Regex in array",
    ),
    ExpressionTestCase(
        id="bson_timestamp",
        doc={"val": Timestamp(1, 1), "arr": [Timestamp(1, 1), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Timestamp in array",
    ),
    ExpressionTestCase(
        id="bson_minkey",
        doc={"val": MinKey(), "arr": [MinKey(), 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find MinKey in array",
    ),
    ExpressionTestCase(
        id="bson_maxkey",
        doc={"val": MaxKey(), "arr": [1, MaxKey()]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find MaxKey in array",
    ),
    ExpressionTestCase(
        id="bson_uuid",
        doc={
            "val": Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")),
            "arr": [Binary.from_uuid(UUID("01234567-89ab-cdef-fedc-ba9876543210")), 1],
        },
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find UUID binary in array",
    ),
    # Special float values
    ExpressionTestCase(
        id="float_infinity_in_array",
        doc={"val": FLOAT_INFINITY, "arr": [FLOAT_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Infinity in array",
    ),
    ExpressionTestCase(
        id="float_neg_infinity_in_array",
        doc={"val": FLOAT_NEGATIVE_INFINITY, "arr": [FLOAT_NEGATIVE_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find -Infinity in array",
    ),
    ExpressionTestCase(
        id="float_infinity_not_in_array",
        doc={"val": FLOAT_INFINITY, "arr": [1, 2, 3]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Should not find Infinity in non-Infinity array",
    ),
    # Special Decimal128 values
    ExpressionTestCase(
        id="decimal128_infinity_in_array",
        doc={"val": DECIMAL128_INFINITY, "arr": [DECIMAL128_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Decimal128 Infinity in array",
    ),
    ExpressionTestCase(
        id="decimal128_neg_infinity_in_array",
        doc={"val": DECIMAL128_NEGATIVE_INFINITY, "arr": [DECIMAL128_NEGATIVE_INFINITY, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Decimal128 -Infinity in array",
    ),
    # NaN equality: NaN == NaN in BSON comparison (unlike IEEE 754)
    ExpressionTestCase(
        id="float_nan_found",
        doc={"val": FLOAT_NAN, "arr": [FLOAT_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find NaN in array (BSON equality)",
    ),
    ExpressionTestCase(
        id="decimal128_nan_found",
        doc={"val": DECIMAL128_NAN, "arr": [DECIMAL128_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find Decimal128 NaN in array (BSON equality)",
    ),
    ExpressionTestCase(
        id="float_nan_matches_decimal128_nan",
        doc={"val": FLOAT_NAN, "arr": [DECIMAL128_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="float NaN should match Decimal128 NaN cross-type",
    ),
    ExpressionTestCase(
        id="decimal128_nan_matches_float_nan",
        doc={"val": DECIMAL128_NAN, "arr": [FLOAT_NAN, 1]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Decimal128 NaN should match float NaN cross-type",
    ),
    # Aggregation $in does NOT pattern-match regex against strings (unlike query $in)
    ExpressionTestCase(
        id="regex_no_pattern_match",
        doc={"val": Regex("^a"), "arr": ["abc", "def"]},
        expression={"$in": ["$val", "$arr"]},
        expected=False,
        msg="Regex should not pattern-match strings in aggregation $in",
    ),
]

# Success: numeric type equivalence
NUMERIC_EQUIVALENCE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int_in_doubles",
        doc={"val": 1, "arr": [1.0, 2.0]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find int in doubles via numeric equivalence",
    ),
    ExpressionTestCase(
        id="int_in_longs",
        doc={"val": 1, "arr": [Int64(1), 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find int in longs via numeric equivalence",
    ),
    ExpressionTestCase(
        id="int_in_decimal128s",
        doc={"val": 1, "arr": [Decimal128("1"), 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find int in decimal128s via numeric equivalence",
    ),
    ExpressionTestCase(
        id="double_in_ints",
        doc={"val": 1.0, "arr": [1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find double in ints via numeric equivalence",
    ),
    ExpressionTestCase(
        id="long_in_ints",
        doc={"val": Int64(1), "arr": [1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find long in ints via numeric equivalence",
    ),
    ExpressionTestCase(
        id="decimal128_in_ints",
        doc={"val": Decimal128("1"), "arr": [1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find decimal128 in ints via numeric equivalence",
    ),
    ExpressionTestCase(
        id="decimal128_in_doubles",
        doc={"val": Decimal128("1.5"), "arr": [1.5, 2.5]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="Should find decimal128 in doubles via numeric equivalence",
    ),
]

# Negative zero equivalence with positive zero
NEGATIVE_ZERO_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="double_neg_zero_matches_zero",
        doc={"val": DOUBLE_NEGATIVE_ZERO, "arr": [0, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should treat -0.0 as equivalent to 0",
    ),
    ExpressionTestCase(
        id="zero_matches_double_neg_zero_in_array",
        doc={"val": 0, "arr": [DOUBLE_NEGATIVE_ZERO, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should find 0 in array containing -0.0",
    ),
    ExpressionTestCase(
        id="decimal128_neg_zero_matches_zero",
        doc={"val": DECIMAL128_NEGATIVE_ZERO, "arr": [0, 1, 2]},
        expression={"$in": ["$val", "$arr"]},
        expected=True,
        msg="$in should treat Decimal128 -0 as equivalent to 0",
    ),
    ExpressionTestCase(
        id="zero_matches_decimal128_neg_zero_in_array",
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
