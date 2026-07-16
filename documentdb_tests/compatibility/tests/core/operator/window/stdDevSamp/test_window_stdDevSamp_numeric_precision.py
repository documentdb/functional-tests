"""
Tests for $stdDevSamp numeric type mixing, overflow edge cases,
algorithmic precision validation, and Decimal128 type handling.
"""

from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess, assertSuccessNaN
from documentdb_tests.framework.property_checks import Gt, Lte, PerDoc
from documentdb_tests.framework.test_constants import DOUBLE_NEGATIVE_ZERO, FLOAT_NAN

# Property [Numeric Type Mixing]: Int32, Int64, Double coexist correctly


def test_stdDevSamp_all_int32_values(collection):
    """$stdDevSamp with all Int32 values produces correct Double result."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": 30},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": 20, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="all Int32 values produce correct Double result")


def test_stdDevSamp_all_int64_values(collection):
    """$stdDevSamp with all Int64 values produces correct result."""
    docs = [
        {"_id": 1, "partition": "A", "value": Int64(10)},
        {"_id": 2, "partition": "A", "value": Int64(20)},
        {"_id": 3, "partition": "A", "value": Int64(30)},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Int64(10), "result": 10.0},
        {"_id": 2, "partition": "A", "value": Int64(20), "result": 10.0},
        {"_id": 3, "partition": "A", "value": Int64(30), "result": 10.0},
    ]
    assertSuccess(result, expected, msg="all Int64 values compute correctly")


def test_stdDevSamp_mixed_int32_int64_double(collection):
    """$stdDevSamp with mixed Int32 + Int64 + Double in same frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": Int64(20)},
        {"_id": 3, "partition": "A", "value": 30.0},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": Int64(20), "result": 10.0},
        {"_id": 3, "partition": "A", "value": 30.0, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="mixed Int32 + Int64 + Double type promotion works")


# Property [Large Value Handling]: near-overflow and large-spread values compute without overflow


def test_stdDevSamp_large_int64_near_max(collection):
    """$stdDevSamp with Int64 values near MAX_LONG — squaring would overflow 64-bit."""
    docs = [
        {"_id": 1, "partition": "A", "value": Int64(9223372036854775806)},
        {"_id": 2, "partition": "A", "value": Int64(9223372036854775807)},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # Both values round to the same float64 (2^63-1 and 2^63-2 differ by 1 ULP at this scale),
    # so the server sees them as identical -> stdDevSamp = 0.0
    expected = [
        {"_id": 1, "partition": "A", "value": Int64(9223372036854775806), "result": 0.0},
        {"_id": 2, "partition": "A", "value": Int64(9223372036854775807), "result": 0.0},
    ]
    assertSuccess(result, expected, msg="Int64 near MAX_LONG does not overflow")


def test_stdDevSamp_large_int64_spread(collection):
    """$stdDevSamp with widely spread Int64 values — tests numeric stability."""
    docs = [
        {"_id": 1, "partition": "A", "value": Int64(0)},
        {"_id": 2, "partition": "A", "value": Int64(4611686018427387903)},
        {"_id": 3, "partition": "A", "value": Int64(9223372036854775807)},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # Verify 3 docs returned, each with a positive result (exact value depends on precision)
    checks = PerDoc(
        {"result": Gt(0)},
        {"result": Gt(0)},
        {"result": Gt(0)},
    )
    assertResult(result, expected=checks, msg="Large Int64 spread produces positive result")


def test_stdDevSamp_int32_sum_of_squares_overflow(collection):
    """$stdDevSamp with Int32 values where sum-of-squares would overflow Int32."""
    # Max Int32 = 2147483647. Values around 50000: 50000^2 = 2.5e9 > 2^31
    docs = [
        {"_id": 1, "partition": "A", "value": 50000},
        {"_id": 2, "partition": "A", "value": 50001},
        {"_id": 3, "partition": "A", "value": 50002},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # stdDevSamp of [N, N+1, N+2]: mean=N+1, sum_sq=2, var_samp=2/2=1, stdDevSamp=1.0
    expected = [
        {"_id": 1, "partition": "A", "value": 50000, "result": 1.0},
        {"_id": 2, "partition": "A", "value": 50001, "result": 1.0},
        {"_id": 3, "partition": "A", "value": 50002, "result": 1.0},
    ]
    assertSuccess(result, expected, msg="Int32 values that would overflow Int32 sum-of-squares")


def test_stdDevSamp_very_large_value(collection):
    """$stdDevSamp with very large numeric value (1e308) — all identical returns 0."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1e308},
        {"_id": 2, "partition": "A", "value": 1e308},
        {"_id": 3, "partition": "A", "value": 1e308},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1e308, "result": 0.0},
        {"_id": 2, "partition": "A", "value": 1e308, "result": 0.0},
        {"_id": 3, "partition": "A", "value": 1e308, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="very large identical values return 0")


def test_stdDevSamp_alternating_large_values(collection):
    """$stdDevSamp with alternating sign large values — stress variance accumulator."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1e15},
        {"_id": 2, "partition": "A", "value": -1e15},
        {"_id": 3, "partition": "A", "value": 1e15},
        {"_id": 4, "partition": "A", "value": -1e15},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # mean=0, sum_sq=4e30, var_samp=4e30/3, stdDevSamp=sqrt(4e30/3)=2e15/sqrt(3)
    expected = [
        {"_id": 1, "partition": "A", "value": 1e15, "result": 1.1547005383792515e15},
        {"_id": 2, "partition": "A", "value": -1e15, "result": 1.1547005383792515e15},
        {"_id": 3, "partition": "A", "value": 1e15, "result": 1.1547005383792515e15},
        {"_id": 4, "partition": "A", "value": -1e15, "result": 1.1547005383792515e15},
    ]
    assertSuccess(result, expected, msg="alternating large values produce correct stddev")


# Property [Algorithmic Precision]: known exact results and catastrophic cancellation handling


def test_stdDevSamp_known_exact_result(collection):
    """$stdDevSamp of [2,4,4,4,5,5,7,9] = sqrt(32/7) = 2.138089935299395."""
    docs = [
        {"_id": i, "partition": "A", "value": v} for i, v in enumerate([2, 4, 4, 4, 5, 5, 7, 9], 1)
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # mean=5, sum_sq=32, var_samp=32/7, stdDevSamp=sqrt(32/7)=2.138089935299395
    expected = [
        {"_id": i, "partition": "A", "value": v, "result": 2.138089935299395}
        for i, v in enumerate([2, 4, 4, 4, 5, 5, 7, 9], 1)
    ]
    assertSuccess(result, expected, msg="stdDevSamp of [2,4,4,4,5,5,7,9] must be sqrt(32/7)")


def test_stdDevSamp_identical_floats_exactly_zero(collection):
    """$stdDevSamp of identical float values must be exactly 0.0, not epsilon."""
    docs = [
        {"_id": 1, "partition": "A", "value": 3.0},
        {"_id": 2, "partition": "A", "value": 3.0},
        {"_id": 3, "partition": "A", "value": 3.0},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 3.0, "result": 0.0},
        {"_id": 2, "partition": "A", "value": 3.0, "result": 0.0},
        {"_id": 3, "partition": "A", "value": 3.0, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="identical floats produce exactly 0.0")


def test_stdDevSamp_catastrophic_cancellation(collection):
    """$stdDevSamp of [1000000001, 1000000002, 1000000003] — naive sum-of-squares fails."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1000000001},
        {"_id": 2, "partition": "A", "value": 1000000002},
        {"_id": 3, "partition": "A", "value": 1000000003},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # stdDevSamp of [N, N+1, N+2]: mean=N+1, sum_sq=2, var_samp=2/2=1, stdDevSamp=1.0
    expected = [
        {"_id": 1, "partition": "A", "value": 1000000001, "result": 1.0},
        {"_id": 2, "partition": "A", "value": 1000000002, "result": 1.0},
        {"_id": 3, "partition": "A", "value": 1000000003, "result": 1.0},
    ]
    assertSuccess(
        result,
        expected,
        msg="catastrophic cancellation handled — correct stddev for large offset values",
    )


def test_stdDevSamp_very_small_differences(collection):
    """$stdDevSamp with values that differ by very small amounts."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1.0000001},
        {"_id": 2, "partition": "A", "value": 1.0000002},
        {"_id": 3, "partition": "A", "value": 1.0000003},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # The stdDevSamp should be approximately 1e-7 — verify positive and tiny
    checks = PerDoc(
        {"result": [Gt(0), Lte(0.001)]},
        {"result": [Gt(0), Lte(0.001)]},
        {"result": [Gt(0), Lte(0.001)]},
    )
    assertResult(
        result, expected=checks, msg="Small differences produce very small positive stddev"
    )


def test_stdDevSamp_sequential_values_1_to_10(collection):
    """$stdDevSamp over sequential values 1..10 with known exact result."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 3},
        {"_id": 4, "partition": "A", "value": 4},
        {"_id": 5, "partition": "A", "value": 5},
        {"_id": 6, "partition": "A", "value": 6},
        {"_id": 7, "partition": "A", "value": 7},
        {"_id": 8, "partition": "A", "value": 8},
        {"_id": 9, "partition": "A", "value": 9},
        {"_id": 10, "partition": "A", "value": 10},
    ]
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[{"$match": {"_id": 1}}],
    )
    # stdDevSamp of 1..10: mean=5.5, sum_sq=82.5, var_samp=82.5/9, stdDevSamp=sqrt(82.5/9)
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 3.0276503540974917},
    ]
    assertSuccess(result, expected, msg="sequential 1..10 known stdDevSamp result")


# Property [Single Element Frame]: single value produces null for sample stddev (N-1=0)


def test_stdDevSamp_single_element_sliding_window(collection):
    """$stdDevSamp returns null when sliding window frame has exactly one value."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10.0},
        {"_id": 2, "partition": "A", "value": 20.0},
        {"_id": 3, "partition": "A", "value": 30.0},
        {"_id": 4, "partition": "A", "value": 40.0},
        {"_id": 5, "partition": "A", "value": 50.0},
    ]
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [0, 0]})
    # Window [0, 0] — each frame has exactly one value -> stdDevSamp = null (N-1 = 0)
    expected = [
        {"_id": 1, "partition": "A", "value": 10.0, "result": None},
        {"_id": 2, "partition": "A", "value": 20.0, "result": None},
        {"_id": 3, "partition": "A", "value": 30.0, "result": None},
        {"_id": 4, "partition": "A", "value": 40.0, "result": None},
        {"_id": 5, "partition": "A", "value": 50.0, "result": None},
    ]
    assertSuccess(result, expected, msg="single element in sliding frame returns null")


# Property [Decimal128 Support]: Decimal128 values and type mixing with other numerics


def test_stdDevSamp_pure_decimal128_values(collection):
    """$stdDevSamp with pure Decimal128 values computes correctly."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": Decimal128("20")},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": 10.0},
        {"_id": 2, "partition": "A", "value": Decimal128("20"), "result": 10.0},
        {"_id": 3, "partition": "A", "value": Decimal128("30"), "result": 10.0},
    ]
    assertSuccess(result, expected, msg="pure Decimal128 values compute stdDevSamp correctly")


def test_stdDevSamp_decimal128_with_double(collection):
    """$stdDevSamp with mixed Decimal128 and Double values."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": 20.0},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": 10.0},
        {"_id": 2, "partition": "A", "value": 20.0, "result": 10.0},
        {"_id": 3, "partition": "A", "value": Decimal128("30"), "result": 10.0},
    ]
    assertSuccess(result, expected, msg="mixed Decimal128 and Double compute correctly")


def test_stdDevSamp_decimal128_with_int32(collection):
    """$stdDevSamp with mixed Decimal128 and Int32 values."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": 10.0},
        {"_id": 2, "partition": "A", "value": 20, "result": 10.0},
        {"_id": 3, "partition": "A", "value": Decimal128("30"), "result": 10.0},
    ]
    assertSuccess(result, expected, msg="mixed Decimal128 and Int32 compute correctly")


def test_stdDevSamp_decimal128_with_int64(collection):
    """$stdDevSamp with mixed Decimal128 and Int64 values."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": Int64(20)},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": 10.0},
        {"_id": 2, "partition": "A", "value": Int64(20), "result": 10.0},
        {"_id": 3, "partition": "A", "value": Decimal128("30"), "result": 10.0},
    ]
    assertSuccess(result, expected, msg="mixed Decimal128 and Int64 compute correctly")


def test_stdDevSamp_decimal128_all_types_mixed(collection):
    """$stdDevSamp with Decimal128 + Double + Int32 + Int64 all in same frame."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": 20.0},
        {"_id": 3, "partition": "A", "value": 30},
        {"_id": 4, "partition": "A", "value": Int64(40)},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # stdDevSamp([10,20,30,40]): mean=25, sum_sq=500, var_samp=500/3, stdDevSamp=sqrt(500/3)
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": 12.909944487358056},
        {"_id": 2, "partition": "A", "value": 20.0, "result": 12.909944487358056},
        {"_id": 3, "partition": "A", "value": 30, "result": 12.909944487358056},
        {"_id": 4, "partition": "A", "value": Int64(40), "result": 12.909944487358056},
    ]
    assertSuccess(result, expected, msg="all four numeric types mixed in same frame")


def test_stdDevSamp_decimal128_high_precision(collection):
    """$stdDevSamp with high-precision Decimal128 values preserves precision."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("1.000000000000000000000000000000001")},
        {"_id": 2, "partition": "A", "value": Decimal128("2.000000000000000000000000000000001")},
        {"_id": 3, "partition": "A", "value": Decimal128("3.000000000000000000000000000000001")},
    ]
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[
            {"$addFields": {"result": {"$round": ["$result", 3]}}},
            {"$project": {"_id": 1, "result": 1}},
        ],
    )
    expected = [
        {"_id": 1, "result": 1.0},
        {"_id": 2, "result": 1.0},
        {"_id": 3, "result": 1.0},
    ]
    assertSuccess(result, expected, msg="high-precision Decimal128 values produce ~1.0")


def test_stdDevSamp_decimal128_near_zero(collection):
    """$stdDevSamp with very small Decimal128 values near zero."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("0.0000000000000000000000000000000001")},
        {"_id": 2, "partition": "A", "value": Decimal128("0.0000000000000000000000000000000002")},
        {"_id": 3, "partition": "A", "value": Decimal128("0.0000000000000000000000000000000003")},
    ]
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[
            {
                "$addFields": {
                    "valid": {
                        "$and": [
                            {"$ne": ["$result", None]},
                            {"$gte": ["$result", 0]},
                        ]
                    }
                }
            },
            {"$project": {"_id": 1, "valid": 1}},
        ],
    )
    expected = [
        {"_id": 1, "valid": True},
        {"_id": 2, "valid": True},
        {"_id": 3, "valid": True},
    ]
    assertSuccess(result, expected, msg="near-zero Decimal128 produces non-negative result")


def test_stdDevSamp_decimal128_identical_values(collection):
    """$stdDevSamp with identical Decimal128 values returns 0."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("42.5")},
        {"_id": 2, "partition": "A", "value": Decimal128("42.5")},
        {"_id": 3, "partition": "A", "value": Decimal128("42.5")},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("42.5"), "result": 0.0},
        {"_id": 2, "partition": "A", "value": Decimal128("42.5"), "result": 0.0},
        {"_id": 3, "partition": "A", "value": Decimal128("42.5"), "result": 0.0},
    ]
    assertSuccess(result, expected, msg="identical Decimal128 values return 0")


def test_stdDevSamp_decimal128_sliding_window(collection):
    """$stdDevSamp with Decimal128 values in a sliding window."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": Decimal128("20")},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
        {"_id": 4, "partition": "A", "value": Decimal128("40")},
        {"_id": 5, "partition": "A", "value": Decimal128("50")},
    ]
    # Window [-1, 0]: row 1 has single element -> null, rows 2-5 have pairs -> stdDevSamp
    # stdDevSamp of adjacent pairs with diff=10: sqrt((25+25)/1) = sqrt(50) = 7.0710678118654755
    result = run_window_operator(collection, "$stdDevSamp", docs, {"documents": [-1, 0]})
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": None},
        {"_id": 2, "partition": "A", "value": Decimal128("20"), "result": 7.0710678118654755},
        {"_id": 3, "partition": "A", "value": Decimal128("30"), "result": 7.0710678118654755},
        {"_id": 4, "partition": "A", "value": Decimal128("40"), "result": 7.0710678118654755},
        {"_id": 5, "partition": "A", "value": Decimal128("50"), "result": 7.0710678118654755},
    ]
    assertSuccess(result, expected, msg="Decimal128 values in sliding window with stdDevSamp")


# Property [Decimal128 Special Values]: Decimal128 NaN and Infinity handling


def test_stdDevSamp_decimal128_nan_special(collection):
    """$stdDevSamp with Decimal128 NaN — NaN is numeric and poisons the calculation."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": Decimal128("NaN")},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": Decimal128("10"), "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "value": Decimal128("NaN"), "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "value": Decimal128("30"), "result": FLOAT_NAN},
    ]
    assertSuccessNaN(
        result, expected, msg="Decimal128 NaN is numeric and poisons stdDevSamp to NaN"
    )


def test_stdDevSamp_decimal128_infinity_special(collection):
    """$stdDevSamp with Decimal128 Infinity special value."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": Decimal128("Infinity")},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[
            {
                "$addFields": {
                    "has_result": {"$ne": ["$result", None]},
                }
            },
            {"$project": {"_id": 1, "has_result": 1}},
        ],
    )
    expected = [
        {"_id": 1, "has_result": True},
        {"_id": 2, "has_result": True},
        {"_id": 3, "has_result": True},
    ]
    assertSuccess(result, expected, msg="Decimal128 Infinity produces a non-null result")


def test_stdDevSamp_decimal128_neg_infinity_special(collection):
    """$stdDevSamp with Decimal128 -Infinity special value."""
    docs = [
        {"_id": 1, "partition": "A", "value": Decimal128("10")},
        {"_id": 2, "partition": "A", "value": Decimal128("-Infinity")},
        {"_id": 3, "partition": "A", "value": Decimal128("30")},
    ]
    result = run_window_operator(
        collection,
        "$stdDevSamp",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        extra_stages=[
            {
                "$addFields": {
                    "has_result": {"$ne": ["$result", None]},
                }
            },
            {"$project": {"_id": 1, "has_result": 1}},
        ],
    )
    expected = [
        {"_id": 1, "has_result": True},
        {"_id": 2, "has_result": True},
        {"_id": 3, "has_result": True},
    ]
    assertSuccess(result, expected, msg="Decimal128 -Infinity produces a non-null result")


# Property [Basic Numeric]: standard numeric inputs handled correctly


def test_stdDevSamp_all_identical_values_returns_zero(collection):
    """$stdDevSamp returns 0 when all values in the frame are identical."""
    docs = [
        {"_id": 1, "partition": "A", "value": 7.0},
        {"_id": 2, "partition": "A", "value": 7.0},
        {"_id": 3, "partition": "A", "value": 7.0},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 7.0, "result": 0.0},
        {"_id": 2, "partition": "A", "value": 7.0, "result": 0.0},
        {"_id": 3, "partition": "A", "value": 7.0, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="identical values produce stdDevSamp = 0")


def test_stdDevSamp_negative_numbers(collection):
    """$stdDevSamp handles negative numbers correctly."""
    docs = [
        {"_id": 1, "partition": "A", "value": -10},
        {"_id": 2, "partition": "A", "value": 0},
        {"_id": 3, "partition": "A", "value": 10},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": -10, "result": 10.0},
        {"_id": 2, "partition": "A", "value": 0, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 10, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="negative numbers handled correctly")


def test_stdDevSamp_decimals(collection):
    """$stdDevSamp handles floating-point (double) values."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1.5},
        {"_id": 2, "partition": "A", "value": 2.5},
        {"_id": 3, "partition": "A", "value": 3.5},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1.5, "result": 1.0},
        {"_id": 2, "partition": "A", "value": 2.5, "result": 1.0},
        {"_id": 3, "partition": "A", "value": 3.5, "result": 1.0},
    ]
    assertSuccess(result, expected, msg="floating-point values handled correctly")


# Property [Negative Zero]: -0.0 treated as numeric zero


def test_stdDevSamp_negative_zero(collection):
    """$stdDevSamp treats -0.0 as numeric zero — participates in computation."""
    docs = [
        {"_id": 1, "partition": "A", "value": DOUBLE_NEGATIVE_ZERO},
        {"_id": 2, "partition": "A", "value": 10},
        {"_id": 3, "partition": "A", "value": 20},
    ]
    result = run_window_operator(
        collection, "$stdDevSamp", docs, {"documents": ["unbounded", "unbounded"]}
    )
    # Values: [-0.0, 10, 20] -> mean=10, sum_sq=200, var_samp=200/2=100, stdDevSamp=10.0
    expected = [
        {"_id": 1, "partition": "A", "value": DOUBLE_NEGATIVE_ZERO, "result": 10.0},
        {"_id": 2, "partition": "A", "value": 10, "result": 10.0},
        {"_id": 3, "partition": "A", "value": 20, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="-0.0 treated as numeric zero in stdDevSamp")
