"""
Element type preservation tests for $arrayElemAt expression.

Tests that $arrayElemAt correctly returns elements of all BSON types
including special float/Decimal128 values and boundary integers.
"""

import math
from datetime import datetime, timezone

import pytest
from bson import Binary, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    INT32_MAX,
    INT64_MAX,
)

# Property [Element Types]: $arrayElemAt returns the element with its original BSON type.
ELEMENT_TYPE_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="int64_element",
        doc={"arr": [Int64(99)], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=Int64(99),
        msg="$arrayElemAt should return Int64 element",
    ),
    ExpressionTestCase(
        id="decimal128_element",
        doc={"arr": [DECIMAL128_ONE_AND_HALF], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=DECIMAL128_ONE_AND_HALF,
        msg="$arrayElemAt should return Decimal128 element",
    ),
    ExpressionTestCase(
        id="datetime_element",
        doc={"arr": [datetime(2024, 1, 1, tzinfo=timezone.utc)], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=datetime(2024, 1, 1, tzinfo=timezone.utc),
        msg="$arrayElemAt should return datetime element",
    ),
    ExpressionTestCase(
        id="binary_element",
        doc={"arr": [Binary(b"\x01\x02", 0)], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=b"\x01\x02",
        msg="$arrayElemAt should return binary element",
    ),
    ExpressionTestCase(
        id="regex_element",
        doc={"arr": [Regex("^abc", "i")], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=Regex("^abc", "i"),
        msg="$arrayElemAt should return regex element",
    ),
    ExpressionTestCase(
        id="objectid_element",
        doc={"arr": [ObjectId("000000000000000000000001")], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=ObjectId("000000000000000000000001"),
        msg="$arrayElemAt should return ObjectId element",
    ),
    ExpressionTestCase(
        id="minkey_element",
        doc={"arr": [MinKey(), 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=MinKey(),
        msg="$arrayElemAt should return MinKey element",
    ),
    ExpressionTestCase(
        id="maxkey_element",
        doc={"arr": [1, MaxKey()], "idx": 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=MaxKey(),
        msg="$arrayElemAt should return MaxKey element",
    ),
    ExpressionTestCase(
        id="timestamp_element",
        doc={"arr": [Timestamp(0, 0)], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=Timestamp(0, 0),
        msg="$arrayElemAt should return Timestamp element",
    ),
    ExpressionTestCase(
        id="float_nan_element",
        doc={"arr": [FLOAT_NAN, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=pytest.approx(math.nan, nan_ok=True),
        msg="$arrayElemAt should return NaN element",
    ),
    ExpressionTestCase(
        id="float_infinity_element",
        doc={"arr": [FLOAT_INFINITY, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=FLOAT_INFINITY,
        msg="$arrayElemAt should return Infinity element",
    ),
    ExpressionTestCase(
        id="float_neg_infinity_element",
        doc={"arr": [FLOAT_NEGATIVE_INFINITY, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=FLOAT_NEGATIVE_INFINITY,
        msg="$arrayElemAt should return -Infinity element",
    ),
    ExpressionTestCase(
        id="decimal128_nan_element",
        doc={"arr": [DECIMAL128_NAN, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=DECIMAL128_NAN,
        msg="$arrayElemAt should return Decimal128 NaN element",
    ),
    ExpressionTestCase(
        id="decimal128_infinity_element",
        doc={"arr": [DECIMAL128_INFINITY, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=DECIMAL128_INFINITY,
        msg="$arrayElemAt should return Decimal128 Infinity element",
    ),
    ExpressionTestCase(
        id="decimal128_neg_infinity_element",
        doc={"arr": [DECIMAL128_NEGATIVE_INFINITY, 1], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=DECIMAL128_NEGATIVE_INFINITY,
        msg="$arrayElemAt should return Decimal128 -Infinity element",
    ),
    ExpressionTestCase(
        id="int32_max_element",
        doc={"arr": [INT32_MAX, 0], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=INT32_MAX,
        msg="$arrayElemAt should return INT32_MAX element",
    ),
    ExpressionTestCase(
        id="int64_max_element",
        doc={"arr": [INT64_MAX, 0], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=INT64_MAX,
        msg="$arrayElemAt should return INT64_MAX element",
    ),
    ExpressionTestCase(
        id="mixed_special_last",
        doc={"arr": [INT32_MAX, FLOAT_INFINITY, DECIMAL128_NAN], "idx": 2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=DECIMAL128_NAN,
        msg="$arrayElemAt should return element from mixed special values array",
    ),
]
