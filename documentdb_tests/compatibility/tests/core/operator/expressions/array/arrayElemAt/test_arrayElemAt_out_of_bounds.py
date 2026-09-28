"""
Out-of-bounds index tests for $arrayElemAt expression.

Tests that $arrayElemAt returns no result (missing) when the index
exceeds array bounds in either direction.
"""

from bson import Decimal128

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.expression_test_case import (  # noqa: E501
    ExpressionTestCase,
)
from documentdb_tests.framework.test_constants import INT32_MAX, INT32_MIN

# Property [Out Of Bounds]: $arrayElemAt returns no value when the index is out of bounds.
OUT_OF_BOUNDS_TESTS: list[ExpressionTestCase] = [
    ExpressionTestCase(
        id="positive_oob",
        doc={"arr": [1, 2, 3], "idx": 15},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for positive OOB",
    ),
    ExpressionTestCase(
        id="positive_oob_by_one",
        doc={"arr": [1, 2, 3], "idx": 3},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for OOB by one",
    ),
    ExpressionTestCase(
        id="negative_oob",
        doc={"arr": [1, 2, 3], "idx": -4},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for negative OOB",
    ),
    ExpressionTestCase(
        id="negative_oob_large",
        doc={"arr": [1, 2, 3], "idx": -100},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for large negative OOB",
    ),
    ExpressionTestCase(
        id="empty_array_idx_0",
        doc={"arr": [], "idx": 0},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for empty array idx 0",
    ),
    ExpressionTestCase(
        id="empty_array_neg1",
        doc={"arr": [], "idx": -1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for empty array idx -1",
    ),
    ExpressionTestCase(
        id="int32_max_oob",
        doc={"arr": [1, 2, 3], "idx": INT32_MAX},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for INT32_MAX index",
    ),
    ExpressionTestCase(
        id="int32_min_oob",
        doc={"arr": [1, 2, 3], "idx": INT32_MIN},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for INT32_MIN index",
    ),
    ExpressionTestCase(
        id="single_element_oob_pos",
        doc={"arr": [42], "idx": 1},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for single element OOB positive",
    ),
    ExpressionTestCase(
        id="single_element_oob_neg",
        doc={"arr": [42], "idx": -2},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for single element OOB negative",
    ),
    ExpressionTestCase(
        id="decimal128_oob_pos",
        doc={"arr": [1, 2, 3], "idx": Decimal128("15")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for Decimal128 positive OOB",
    ),
    ExpressionTestCase(
        id="decimal128_oob_neg",
        doc={"arr": [1, 2, 3], "idx": Decimal128("-100")},
        expression={"$arrayElemAt": ["$arr", "$idx"]},
        expected=[{}],
        msg="$arrayElemAt should return no result for Decimal128 negative OOB",
    ),
]
