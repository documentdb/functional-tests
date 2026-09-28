"""
Tests for $covariancePop numeric type mixing, overflow edge cases,
algorithmic precision validation, and Decimal128 type handling.

Covers: Int32/Int64/Double mixing, Int64 near MAX_LONG (overflow risk when
squaring), catastrophic cancellation in variance calculation, known exact
results, very small differences, consistency between window modes,
Decimal128 (NumberDecimal) values, high-precision Decimal128, mixed Decimal128
with other numeric types, and Decimal128 special values (NaN, Infinity).

Server behavior (verified):
- When ANY input value is Decimal128, the server returns Decimal128 type results
- Pure Decimal128 returns Decimal128("1.333333333333333333333333333333333")
- Decimal128 identical values returns Decimal128("0E+12"), not float 0.0
- Decimal128 sliding window: Row 1 returns float 0.0, subsequent rows Decimal128("0.5")
- 1e308 identical values: returns NaN (overflow in intermediate computation)
"""

from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Gt, Lte, PerDoc
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DOUBLE_NEAR_MAX,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
)

# Property [Numeric Type Mixing]: Int32, Int64, Double coexist correctly


def test_covariancePop_all_int32_values(collection):
    """$covariancePop with all Int32 values produces Double result."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[1,2,3], y=[2,4,6]: covPop = 4/3 = 1.3333...
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2, "result": 1.3333333333333333},
        {"_id": 2, "partition": "A", "x": 2, "y": 4, "result": 1.3333333333333333},
        {"_id": 3, "partition": "A", "x": 3, "y": 6, "result": 1.3333333333333333},
    ]
    assertSuccess(result, expected, msg="all Int32 values produce correct Double result")


def test_covariancePop_all_int64_values(collection):
    """$covariancePop with all Int64 values produces correct result."""
    docs = [
        {"_id": 1, "partition": "A", "x": Int64(1), "y": Int64(2)},
        {"_id": 2, "partition": "A", "x": Int64(2), "y": Int64(4)},
        {"_id": 3, "partition": "A", "x": Int64(3), "y": Int64(6)},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": Int64(1), "y": Int64(2), "result": 1.3333333333333333},
        {"_id": 2, "partition": "A", "x": Int64(2), "y": Int64(4), "result": 1.3333333333333333},
        {"_id": 3, "partition": "A", "x": Int64(3), "y": Int64(6), "result": 1.3333333333333333},
    ]
    assertSuccess(result, expected, msg="all Int64 values compute correctly")


def test_covariancePop_mixed_int32_int64_double(collection):
    """$covariancePop with mixed Int32 + Int64 + Double in same frame."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2.0},
        {"_id": 2, "partition": "A", "x": Int64(2), "y": 4},
        {"_id": 3, "partition": "A", "x": 3.0, "y": Int64(6)},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 2.0, "result": 1.3333333333333333},
        {"_id": 2, "partition": "A", "x": Int64(2), "y": 4, "result": 1.3333333333333333},
        {"_id": 3, "partition": "A", "x": 3.0, "y": Int64(6), "result": 1.3333333333333333},
    ]
    assertSuccess(result, expected, msg="mixed Int32 + Int64 + Double type promotion works")


# Property [Large Value Handling]: near-overflow and large-spread values compute without overflow


def test_covariancePop_large_int64_near_max(collection):
    """$covariancePop with Int64 values near MAX_LONG — squaring would overflow 64-bit."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "x": Int64(9223372036854775806),
            "y": Int64(9223372036854775806),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Int64(9223372036854775807),
            "y": Int64(9223372036854775807),
        },
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Both values round to the same float64 at this scale -> covPop = 0.0
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Int64(9223372036854775806),
            "y": Int64(9223372036854775806),
            "result": 0.0,
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Int64(9223372036854775807),
            "y": Int64(9223372036854775807),
            "result": 0.0,
        },
    ]
    assertSuccess(result, expected, msg="Int64 near MAX_LONG does not overflow")


def test_covariancePop_large_int64_spread(collection):
    """$covariancePop with widely spread Int64 values — tests numeric stability."""
    docs = [
        {"_id": 1, "partition": "A", "x": Int64(0), "y": Int64(0)},
        {
            "_id": 2,
            "partition": "A",
            "x": Int64(4611686018427387903),
            "y": Int64(4611686018427387903),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Int64(9223372036854775807),
            "y": Int64(9223372036854775807),
        },
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # When x==y, covPop(x,y) = varPop(x) > 0
    checks = PerDoc(
        {"result": Gt(0)},
        {"result": Gt(0)},
        {"result": Gt(0)},
    )
    assertResult(result, expected=checks, msg="Large Int64 spread produces positive result")


def test_covariancePop_very_large_value(collection):
    """$covariancePop with very large numeric value (1e308) — all identical returns NaN."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1e308, "y": 1e308},
        {"_id": 2, "partition": "A", "x": 1e308, "y": 1e308},
        {"_id": 3, "partition": "A", "x": 1e308, "y": 1e308},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Server returns NaN due to overflow in intermediate computation
    expected = [
        {"_id": 1, "partition": "A", "x": 1e308, "y": 1e308, "result": FLOAT_NAN},
        {"_id": 2, "partition": "A", "x": 1e308, "y": 1e308, "result": FLOAT_NAN},
        {"_id": 3, "partition": "A", "x": 1e308, "y": 1e308, "result": FLOAT_NAN},
    ]
    assertSuccessNaN(result, expected, msg="very large identical values overflow to NaN")


def test_covariancePop_alternating_large_values(collection):
    """$covariancePop with alternating sign large values — stress accumulator."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1e15, "y": 1e15},
        {"_id": 2, "partition": "A", "x": -1e15, "y": -1e15},
        {"_id": 3, "partition": "A", "x": 1e15, "y": 1e15},
        {"_id": 4, "partition": "A", "x": -1e15, "y": -1e15},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # When x==y: covPop = varPop. Mean=0, var = (4*1e30)/4 = 1e30
    expected = [
        {"_id": 1, "partition": "A", "x": 1e15, "y": 1e15, "result": 1e30},
        {"_id": 2, "partition": "A", "x": -1e15, "y": -1e15, "result": 1e30},
        {"_id": 3, "partition": "A", "x": 1e15, "y": 1e15, "result": 1e30},
        {"_id": 4, "partition": "A", "x": -1e15, "y": -1e15, "result": 1e30},
    ]
    assertSuccess(result, expected, msg="alternating large values produce correct covariancePop")


# Property [Algorithmic Precision]: known exact results and catastrophic cancellation handling


def test_covariancePop_known_exact_result(collection):
    """$covariancePop with known exact result: covPop([1,2,3,4],[2,4,6,8]) = 2.5."""
    docs = [
        {"_id": i, "partition": "A", "x": x, "y": y}
        for i, (x, y) in enumerate([(1, 2), (2, 4), (3, 6), (4, 8)], 1)
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[1,2,3,4], y=[2,4,6,8]: mean_x=2.5, mean_y=5
    # covPop = ((-1.5)(-3)+(-0.5)(-1)+(0.5)(1)+(1.5)(3))/4 = (4.5+0.5+0.5+4.5)/4 = 2.5
    expected = [
        {"_id": i, "partition": "A", "x": x, "y": y, "result": 2.5}
        for i, (x, y) in enumerate([(1, 2), (2, 4), (3, 6), (4, 8)], 1)
    ]
    assertSuccess(result, expected, msg="covariancePop of [1,2,3,4],[2,4,6,8] must be exactly 2.5")


def test_covariancePop_identical_values_exactly_zero(collection):
    """$covariancePop of identical (x,y) pairs where y is constant must be exactly 0.0."""
    docs = [
        {"_id": 1, "partition": "A", "x": 3.0, "y": 7.0},
        {"_id": 2, "partition": "A", "x": 3.0, "y": 7.0},
        {"_id": 3, "partition": "A", "x": 3.0, "y": 7.0},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {"_id": 1, "partition": "A", "x": 3.0, "y": 7.0, "result": 0.0},
        {"_id": 2, "partition": "A", "x": 3.0, "y": 7.0, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3.0, "y": 7.0, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="identical pairs produce exactly 0.0")


def test_covariancePop_catastrophic_cancellation(collection):
    """$covariancePop with large offset values — naive algorithm fails."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1000000001, "y": 1000000002},
        {"_id": 2, "partition": "A", "x": 1000000002, "y": 1000000004},
        {"_id": 3, "partition": "A", "x": 1000000003, "y": 1000000006},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x = [N, N+1, N+2], y = [M, M+2, M+4] where N,M are large
    # After centering: x-offsets = [-1, 0, 1], y-offsets = [-2, 0, 2]
    # covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = 4/3 = 1.3333...
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": 1000000001,
            "y": 1000000002,
            "result": 1.3333333333333333,
        },
        {
            "_id": 2,
            "partition": "A",
            "x": 1000000002,
            "y": 1000000004,
            "result": 1.3333333333333333,
        },
        {
            "_id": 3,
            "partition": "A",
            "x": 1000000003,
            "y": 1000000006,
            "result": 1.3333333333333333,
        },
    ]
    assertSuccess(
        result,
        expected,
        msg="catastrophic cancellation handled — correct covPop for large offset values",
    )


def test_covariancePop_very_small_differences(collection):
    """$covariancePop with values that differ by very small amounts."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1.0000001, "y": 2.0000002},
        {"_id": 2, "partition": "A", "x": 1.0000002, "y": 2.0000004},
        {"_id": 3, "partition": "A", "x": 1.0000003, "y": 2.0000006},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # The covariancePop should be positive and tiny
    checks = PerDoc(
        {"result": [Gt(0), Lte(0.001)]},
        {"result": [Gt(0), Lte(0.001)]},
        {"result": [Gt(0), Lte(0.001)]},
    )
    assertResult(
        result, expected=checks, msg="Small differences produce very small positive covPop"
    )


# Property [Single Element Frame]: single value produces 0 for population covariance


def test_covariancePop_single_element_sliding_window(collection):
    """$covariancePop returns 0 when sliding window frame has exactly one value."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10},
        {"_id": 2, "partition": "A", "x": 2, "y": 20},
        {"_id": 3, "partition": "A", "x": 3, "y": 30},
        {"_id": 4, "partition": "A", "x": 4, "y": 40},
        {"_id": 5, "partition": "A", "x": 5, "y": 50},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [0, 0]},
        expression=["$x", "$y"],
    )
    # Window [0, 0] — each frame has exactly one value -> covPop = 0
    expected = [
        {"_id": 1, "partition": "A", "x": 1, "y": 10, "result": 0.0},
        {"_id": 2, "partition": "A", "x": 2, "y": 20, "result": 0.0},
        {"_id": 3, "partition": "A", "x": 3, "y": 30, "result": 0.0},
        {"_id": 4, "partition": "A", "x": 4, "y": 40, "result": 0.0},
        {"_id": 5, "partition": "A", "x": 5, "y": 50, "result": 0.0},
    ]
    assertSuccess(result, expected, msg="single element in sliding frame returns 0")


# Property [Decimal128 Support]: Decimal128 values return Decimal128 type results.


def test_covariancePop_pure_decimal128_values(collection):
    """$covariancePop with pure Decimal128 values returns Decimal128 type result."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": Decimal128("2")},
        {"_id": 2, "partition": "A", "x": Decimal128("2"), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": Decimal128("6")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Server returns Decimal128 type with high precision
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("1"),
            "y": Decimal128("2"),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("2"),
            "y": Decimal128("4"),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3"),
            "y": Decimal128("6"),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
    ]
    assertSuccess(result, expected, msg="pure Decimal128 values return Decimal128 type result")


def test_covariancePop_decimal128_with_double(collection):
    """$covariancePop with mixed Decimal128 and Double returns Decimal128 type."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": 2.0},
        {"_id": 2, "partition": "A", "x": 2.0, "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": 6.0},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Server returns Decimal128 type when any input is Decimal128
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("1"),
            "y": 2.0,
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": 2.0,
            "y": Decimal128("4"),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3"),
            "y": 6.0,
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
    ]
    assertSuccess(result, expected, msg="mixed Decimal128 and Double returns Decimal128 type")


def test_covariancePop_decimal128_with_int32(collection):
    """$covariancePop with mixed Decimal128 and Int32 returns Decimal128 type."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": 2},
        {"_id": 2, "partition": "A", "x": 2, "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": 6},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Server returns Decimal128 type when any input is Decimal128
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("1"),
            "y": 2,
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": 2,
            "y": Decimal128("4"),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3"),
            "y": 6,
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
    ]
    assertSuccess(result, expected, msg="mixed Decimal128 and Int32 returns Decimal128 type")


def test_covariancePop_decimal128_with_int64(collection):
    """$covariancePop with mixed Decimal128 and Int64 returns Decimal128 type."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": Int64(2)},
        {"_id": 2, "partition": "A", "x": Int64(2), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": Int64(6)},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Server returns Decimal128 type when any input is Decimal128
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("1"),
            "y": Int64(2),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Int64(2),
            "y": Decimal128("4"),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3"),
            "y": Int64(6),
            "result": Decimal128("1.333333333333333333333333333333333"),
        },
    ]
    assertSuccess(result, expected, msg="mixed Decimal128 and Int64 returns Decimal128 type")


def test_covariancePop_decimal128_all_types_mixed(collection):
    """$covariancePop with Decimal128 + Double + Int32 + Int64 all in same frame."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": 2.0},
        {"_id": 2, "partition": "A", "x": 2.0, "y": 4},
        {"_id": 3, "partition": "A", "x": 3, "y": Int64(6)},
        {"_id": 4, "partition": "A", "x": Int64(4), "y": Decimal128("8")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[1,2,3,4], y=[2,4,6,8] -> covPop = 2.5
    # Server returns Decimal128 type when any input is Decimal128
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("1"),
            "y": 2.0,
            "result": Decimal128("2.50000000000000"),
        },
        {"_id": 2, "partition": "A", "x": 2.0, "y": 4, "result": Decimal128("2.50000000000000")},
        {
            "_id": 3,
            "partition": "A",
            "x": 3,
            "y": Int64(6),
            "result": Decimal128("2.50000000000000"),
        },
        {
            "_id": 4,
            "partition": "A",
            "x": Int64(4),
            "y": Decimal128("8"),
            "result": Decimal128("2.50000000000000"),
        },
    ]
    assertSuccess(result, expected, msg="all four numeric types mixed returns Decimal128 type")


def test_covariancePop_decimal128_sliding_window(collection):
    """$covariancePop with Decimal128 values in a sliding window."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": Decimal128("2")},
        {"_id": 2, "partition": "A", "x": Decimal128("2"), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": Decimal128("6")},
        {"_id": 4, "partition": "A", "x": Decimal128("4"), "y": Decimal128("8")},
        {"_id": 5, "partition": "A", "x": Decimal128("5"), "y": Decimal128("10")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": [-1, 0]},
        expression=["$x", "$y"],
    )
    # Window [-1, 0]:
    # Row 1: [(1,2)] -> single pair -> 0.0 (float, before Decimal128 pair contributes)
    # Row 2: [(1,2),(2,4)] -> Decimal128("0.5")
    # Row 3: [(2,4),(3,6)] -> Decimal128("0.5")
    # Row 4: [(3,6),(4,8)] -> Decimal128("0.5")
    # Row 5: [(4,8),(5,10)] -> Decimal128("0.5")
    expected = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": Decimal128("2"), "result": 0.0},
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("2"),
            "y": Decimal128("4"),
            "result": Decimal128("0.5"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3"),
            "y": Decimal128("6"),
            "result": Decimal128("0.5"),
        },
        {
            "_id": 4,
            "partition": "A",
            "x": Decimal128("4"),
            "y": Decimal128("8"),
            "result": Decimal128("0.5"),
        },
        {
            "_id": 5,
            "partition": "A",
            "x": Decimal128("5"),
            "y": Decimal128("10"),
            "result": Decimal128("0.5"),
        },
    ]
    assertSuccess(result, expected, msg="Decimal128 sliding window returns Decimal128 type")


def test_covariancePop_decimal128_identical_values(collection):
    """$covariancePop with identical Decimal128 value pairs returns Decimal128('0E+12')."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("42.5"), "y": Decimal128("99.9")},
        {"_id": 2, "partition": "A", "x": Decimal128("42.5"), "y": Decimal128("99.9")},
        {"_id": 3, "partition": "A", "x": Decimal128("42.5"), "y": Decimal128("99.9")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # Server returns Decimal128("0E+12") for identical values, not float 0.0
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("42.5"),
            "y": Decimal128("99.9"),
            "result": Decimal128("0E+12"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("42.5"),
            "y": Decimal128("99.9"),
            "result": Decimal128("0E+12"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("42.5"),
            "y": Decimal128("99.9"),
            "result": Decimal128("0E+12"),
        },
    ]
    assertSuccess(
        result, expected, msg="identical Decimal128 value pairs return Decimal128('0E+12')"
    )


# Property [Decimal128 Special Values]: Decimal128 NaN and Infinity handling


def test_covariancePop_decimal128_nan_special(collection):
    """$covariancePop with Decimal128 NaN — NaN is numeric and poisons the calculation."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": Decimal128("2")},
        {"_id": 2, "partition": "A", "x": Decimal128("NaN"), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": Decimal128("6")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": Decimal128("1"),
            "y": Decimal128("2"),
            "result": FLOAT_NAN,
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("NaN"),
            "y": Decimal128("4"),
            "result": FLOAT_NAN,
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3"),
            "y": Decimal128("6"),
            "result": FLOAT_NAN,
        },
    ]
    assertSuccessNaN(
        result, expected, msg="Decimal128 NaN is numeric and poisons covariancePop to NaN"
    )


def test_covariancePop_decimal128_infinity_special(collection):
    """$covariancePop with Decimal128 Infinity special value."""
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": Decimal128("2")},
        {"_id": 2, "partition": "A", "x": Decimal128("Infinity"), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": Decimal128("6")},
    ]
    collection.insert_many(docs)
    extra_stages = [
        {
            "$addFields": {
                "has_result": {"$ne": ["$result", None]},
            }
        },
        {"$project": {"_id": 1, "has_result": 1}},
    ]
    pipeline = [
        {
            "$setWindowFields": {
                "partitionBy": "$partition",
                "sortBy": {"_id": 1},
                "output": {
                    "result": {
                        "$covariancePop": ["$x", "$y"],
                        "window": {"documents": ["unbounded", "unbounded"]},
                    }
                },
            }
        }
    ] + extra_stages
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    expected = [
        {"_id": 1, "has_result": True},
        {"_id": 2, "has_result": True},
        {"_id": 3, "has_result": True},
    ]
    assertSuccess(result, expected, msg="Decimal128 Infinity produces a non-null result")


# Property [Decimal128 Precision Boundaries]: boundary values from test_constants


def test_covariancePop_decimal128_min_values(collection):
    """$covariancePop with DECIMAL128_MIN values — overflow in intermediate computation."""
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MIN, "y": Decimal128("1")},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MIN, "y": Decimal128("2")},
        {"_id": 3, "partition": "A", "x": DECIMAL128_MIN, "y": Decimal128("3")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # All x values identical, but intermediate computation overflows -> Infinity
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": DECIMAL128_MIN,
            "y": Decimal128("1"),
            "result": Decimal128("Infinity"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": DECIMAL128_MIN,
            "y": Decimal128("2"),
            "result": Decimal128("Infinity"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": DECIMAL128_MIN,
            "y": Decimal128("3"),
            "result": Decimal128("Infinity"),
        },
    ]
    assertSuccess(
        result, expected, msg="DECIMAL128_MIN overflows to Infinity in intermediate computation"
    )


def test_covariancePop_decimal128_large_exponent(collection):
    """$covariancePop with DECIMAL128_LARGE_EXPONENT values — high exponent Decimal128."""
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_LARGE_EXPONENT, "y": Decimal128("2")},
        {"_id": 2, "partition": "A", "x": Decimal128("2E+6144"), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3E+6144"), "y": Decimal128("6")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[1E+6144, 2E+6144, 3E+6144], y=[2,4,6]: covPop = 4/3 * 1E+6144
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": DECIMAL128_LARGE_EXPONENT,
            "y": Decimal128("2"),
            "result": Decimal128("1.333333333333333333333333333333333E+6144"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("2E+6144"),
            "y": Decimal128("4"),
            "result": Decimal128("1.333333333333333333333333333333333E+6144"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3E+6144"),
            "y": Decimal128("6"),
            "result": Decimal128("1.333333333333333333333333333333333E+6144"),
        },
    ]
    assertSuccess(result, expected, msg="DECIMAL128_LARGE_EXPONENT produces positive covPop")


def test_covariancePop_decimal128_small_exponent(collection):
    """$covariancePop with DECIMAL128_SMALL_EXPONENT values — very small Decimal128."""
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_SMALL_EXPONENT, "y": Decimal128("2")},
        {"_id": 2, "partition": "A", "x": Decimal128("2E-6143"), "y": Decimal128("4")},
        {"_id": 3, "partition": "A", "x": Decimal128("3E-6143"), "y": Decimal128("6")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[1E-6143, 2E-6143, 3E-6143], y=[2,4,6]: covPop = 4/3 * 1E-6143
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": DECIMAL128_SMALL_EXPONENT,
            "y": Decimal128("2"),
            "result": Decimal128("1.333333333333333333333333333333333E-6143"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("2E-6143"),
            "y": Decimal128("4"),
            "result": Decimal128("1.333333333333333333333333333333333E-6143"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("3E-6143"),
            "y": Decimal128("6"),
            "result": Decimal128("1.333333333333333333333333333333333E-6143"),
        },
    ]
    assertSuccess(result, expected, msg="DECIMAL128_SMALL_EXPONENT produces positive covPop")


def test_covariancePop_decimal128_negative_zero(collection):
    """$covariancePop with DECIMAL128_NEGATIVE_ZERO — treated as numeric zero."""
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_NEGATIVE_ZERO, "y": Decimal128("10")},
        {"_id": 2, "partition": "A", "x": Decimal128("10"), "y": Decimal128("20")},
        {"_id": 3, "partition": "A", "x": Decimal128("20"), "y": Decimal128("30")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[-0, 10, 20] -> mean_x=10, y=[10, 20, 30] -> mean_y=20
    # covPop = ((-10)(-10)+(0)(0)+(10)(10))/3 = (100+0+100)/3 = 200/3
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": DECIMAL128_NEGATIVE_ZERO,
            "y": Decimal128("10"),
            "result": Decimal128("66.66666666666666666666666666666667"),
        },
        {
            "_id": 2,
            "partition": "A",
            "x": Decimal128("10"),
            "y": Decimal128("20"),
            "result": Decimal128("66.66666666666666666666666666666667"),
        },
        {
            "_id": 3,
            "partition": "A",
            "x": Decimal128("20"),
            "y": Decimal128("30"),
            "result": Decimal128("66.66666666666666666666666666666667"),
        },
    ]
    assertSuccess(result, expected, msg="DECIMAL128_NEGATIVE_ZERO treated as numeric zero")


# Property [Negative Zero]: -0.0 treated as numeric zero


def test_covariancePop_negative_zero(collection):
    """$covariancePop treats -0.0 as numeric zero — participates in computation."""
    docs = [
        {"_id": 1, "partition": "A", "x": DOUBLE_NEGATIVE_ZERO, "y": 10},
        {"_id": 2, "partition": "A", "x": 10, "y": 20},
        {"_id": 3, "partition": "A", "x": 20, "y": 30},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[-0, 10, 20] -> mean_x=10, y=[10, 20, 30] -> mean_y=20
    # covPop = ((-10)(-10)+(0)(0)+(10)(10))/3 = (100+0+100)/3 = 200/3 = 66.6667
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "x": DOUBLE_NEGATIVE_ZERO,
            "y": 10,
            "result": 66.66666666666667,
        },
        {"_id": 2, "partition": "A", "x": 10, "y": 20, "result": 66.66666666666667},
        {"_id": 3, "partition": "A", "x": 20, "y": 30, "result": 66.66666666666667},
    ]
    assertSuccess(result, expected, msg="-0.0 treated as numeric zero in covariancePop")


# Property [Basic Numeric]: standard numeric inputs handled correctly


def test_covariancePop_negative_numbers(collection):
    """$covariancePop handles negative numbers correctly."""
    docs = [
        {"_id": 1, "partition": "A", "x": -10, "y": -20},
        {"_id": 2, "partition": "A", "x": 0, "y": 0},
        {"_id": 3, "partition": "A", "x": 10, "y": 20},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[-10,0,10] mean=0, y=[-20,0,20] mean=0
    # covPop = ((-10)(-20)+(0)(0)+(10)(20))/3 = (200+0+200)/3 = 400/3 = 133.3333
    expected = [
        {"_id": 1, "partition": "A", "x": -10, "y": -20, "result": 133.33333333333334},
        {"_id": 2, "partition": "A", "x": 0, "y": 0, "result": 133.33333333333334},
        {"_id": 3, "partition": "A", "x": 10, "y": 20, "result": 133.33333333333334},
    ]
    assertSuccess(result, expected, msg="negative numbers handled correctly")


def test_covariancePop_decimals(collection):
    """$covariancePop handles floating-point (double) values."""
    docs = [
        {"_id": 1, "partition": "A", "x": 1.5, "y": 3.0},
        {"_id": 2, "partition": "A", "x": 2.5, "y": 5.0},
        {"_id": 3, "partition": "A", "x": 3.5, "y": 7.0},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    # x=[1.5,2.5,3.5] mean=2.5, y=[3,5,7] mean=5
    # covPop = ((-1)(-2)+(0)(0)+(1)(2))/3 = 4/3 = 1.3333...
    expected = [
        {"_id": 1, "partition": "A", "x": 1.5, "y": 3.0, "result": 1.3333333333333333},
        {"_id": 2, "partition": "A", "x": 2.5, "y": 5.0, "result": 1.3333333333333333},
        {"_id": 3, "partition": "A", "x": 3.5, "y": 7.0, "result": 1.3333333333333333},
    ]
    assertSuccess(result, expected, msg="floating-point values handled correctly")


# ---------------------------------------------------------------------------
# Property [Intermediate Overflow]: TEST_COVERAGE.md §22 overflow requirements
#
# Covariance is computed by an online (Welford-style) update, so an
# *intermediate* value can overflow independently of whether the final result
# is representable. The four cases below are deliberately kept separate --
# a single "large values" test cannot distinguish them, and each has a
# different failure mode:
#
#   1. No overflow in the formula -- identical large x, so every deviation is
#                                    exactly 0.
#   2. Deviation overflow         -- opposing magnitudes in one column, so
#                                    x_i - mean_x overflows. The expected sign
#                                    is asserted, not merely non-finiteness.
#   3. Product overflow only      -- deviations stay finite, their product
#                                    overflows.
#   4. Result exceeds range       -- true result beyond the type maximum.
#
# A literal Infinity *input* exercises none of these: non-finite inputs are
# short-circuited before the online update runs. Those live in the
# special_floats file.
#
# All expectations below were verified against the reference server.
# ---------------------------------------------------------------------------


# --- Case 1: no overflow -- identical large values, deviations exactly 0 ---


def test_covariancePop_identical_decimal128_max_three_docs(collection):
    """$covariancePop with 3 identical DECIMAL128_MAX x values -- deviations are exactly 0.

    Nothing in (1/n)*sum((x_i - mean_x)(y_i - mean_y)) overflows: every x_i is the
    same value, so every x_i - mean_x is exactly 0 at any magnitude and the formula
    never requires sum(x_i). The server reports -Infinity because it derives the mean
    from a running sum that overflows; its sign follows the y ordering rather than
    the data (see the y-reversed test below).
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("1")},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("2")},
        {"_id": 3, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("3")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": DECIMAL128_NEGATIVE_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="identical DECIMAL128_MAX x values: The server reports -Infinity from sum-derived mean",
    )


def test_covariancePop_identical_decimal128_max_y_reversed(collection):
    """$covariancePop identical DECIMAL128_MAX x with descending y -- sign flips.

    Same x column as the previous test, same true answer (0), but reversing y
    flips The server's reported infinity from -Infinity to +Infinity. The sign
    tracks the y ordering, not the covariance, which is what identifies it as an
    overflow artifact rather than a semantic.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("3")},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("2")},
        {"_id": 3, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("1")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": DECIMAL128_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="reversing y flips the reported infinity sign for identical x",
    )


def test_covariancePop_identical_decimal128_max_two_docs(collection):
    """$covariancePop with 2 identical DECIMAL128_MAX x values -- no overflow yet.

    Count-dependence check. The true answer is 0 for any number of identical x
    values, but The server's running sum only overflows once a third value is added,
    so n=2 returns 0 while n=3 returns -Infinity. This is the baseline that makes
    the n=3 result meaningful.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("1")},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("2")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": Decimal128("0E+14")} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="two identical DECIMAL128_MAX x values do not overflow the running sum",
    )


def test_covariancePop_identical_decimal128_max_in_y(collection):
    """$covariancePop with identical DECIMAL128_MAX in the y position.

    Mirror of the x-side test: the same artifact must be probed per expression
    position, since the two arguments are accumulated separately.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1"), "y": DECIMAL128_MAX},
        {"_id": 2, "partition": "A", "x": Decimal128("2"), "y": DECIMAL128_MAX},
        {"_id": 3, "partition": "A", "x": Decimal128("3"), "y": DECIMAL128_MAX},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": DECIMAL128_NEGATIVE_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="identical DECIMAL128_MAX y values: same artifact on the y side",
    )


def test_covariancePop_identical_double_near_max_in_y(collection):
    """$covariancePop with identical DOUBLE_NEAR_MAX in y -- double path, y side.

    The double path shows the same count dependence as decimal: two identical
    1e308 x values return 0 (below), while the y-side sum here overflows.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": 1.0, "y": DOUBLE_NEAR_MAX},
        {"_id": 2, "partition": "A", "x": 2.0, "y": DOUBLE_NEAR_MAX},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": FLOAT_NEGATIVE_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="identical DOUBLE_NEAR_MAX y values overflow the running sum",
    )


def test_covariancePop_identical_double_near_max_two_docs(collection):
    """$covariancePop with 2 identical DOUBLE_NEAR_MAX x values -- returns 0.

    Double-path baseline for case 1: x=[1e308, 1e308] does not overflow the
    running sum, so the result is exactly 0.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DOUBLE_NEAR_MAX, "y": 1.0},
        {"_id": 2, "partition": "A", "x": DOUBLE_NEAR_MAX, "y": 2.0},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": 0.0} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="two identical DOUBLE_NEAR_MAX x values give exactly 0",
    )


# --- Case 2: deviation overflow -- SIGN-critical ---


def test_covariancePop_deviation_overflow_positive_decimal128(collection):
    """$covariancePop with x=y=[DECIMAL128_MAX, DECIMAL128_MIN] -- expects +Infinity.

    Opposing maximum magnitudes in the same column make x_i - mean_x overflow.
    x and y move together, so the limit is +Infinity. The sign is asserted
    rather than just non-finiteness, since -Infinity is also non-finite and
    would satisfy a weaker assertion.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": DECIMAL128_MAX},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MIN, "y": DECIMAL128_MIN},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": DECIMAL128_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="positively-correlated deviation overflow gives +Infinity",
    )


def test_covariancePop_deviation_overflow_negative_decimal128(collection):
    """$covariancePop anti-correlated DECIMAL128 extremes -- expects -Infinity.

    Same magnitudes as the previous test with y inverted, so the limit is
    -Infinity. Paired with that test, this pins the sign to the direction of the
    data rather than to the magnitudes.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": DECIMAL128_MIN},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MIN, "y": DECIMAL128_MAX},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": DECIMAL128_NEGATIVE_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="anti-correlated deviation overflow gives -Infinity",
    )


def test_covariancePop_deviation_overflow_positive_double(collection):
    """$covariancePop with x=y=[1e308, -1e308] -- double path, expects +Infinity.

    The deviation -1e308 - 1e308 overflows to -inf in the double path exactly as
    it does in decimal, so the case is covered for both numeric types.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DOUBLE_NEAR_MAX, "y": DOUBLE_NEAR_MAX},
        {"_id": 2, "partition": "A", "x": -DOUBLE_NEAR_MAX, "y": -DOUBLE_NEAR_MAX},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": FLOAT_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="double-path positively-correlated deviation overflow gives +Infinity",
    )


def test_covariancePop_deviation_overflow_negative_double(collection):
    """$covariancePop anti-correlated 1e308 extremes -- double path, expects -Infinity."""
    docs = [
        {"_id": 1, "partition": "A", "x": DOUBLE_NEAR_MAX, "y": -DOUBLE_NEAR_MAX},
        {"_id": 2, "partition": "A", "x": -DOUBLE_NEAR_MAX, "y": DOUBLE_NEAR_MAX},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": FLOAT_NEGATIVE_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="double-path anti-correlated deviation overflow gives -Infinity",
    )


def test_covariancePop_deviation_overflow_representable_result(collection):
    """$covariancePop with x=[DECIMAL128_MAX, 0] -- large magnitude, exact result.

    Deviations reach half of DECIMAL128_MAX without overflowing, and the result
    -2.5E+6144 is representable, so it is returned exactly. This establishes that
    full-range magnitudes alone do not trigger the overflow cases above.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": Decimal128("1")},
        {"_id": 2, "partition": "A", "x": Decimal128("0"), "y": Decimal128("2")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [
        {**doc, "result": Decimal128("-2.500000000000000000000000000000000E+6144")} for doc in docs
    ]
    assertSuccess(
        result,
        expected,
        msg="DECIMAL128_MAX-scale deviations with a representable result are exact",
    )


# --- Case 3: product overflow with finite deviations (control) ---


def test_covariancePop_product_overflow_finite_deviations_double(collection):
    """$covariancePop with x=y=[1e200, -1e200] -- product overflows, deviations do not.

    Control for the case-2 sign tests. Here 1e200 - (-1e200) = 2e200 stays finite
    and only the deviation *product* overflows, giving +Infinity. Keeping this
    separate from case 2 distinguishes an overflow in the deviation step from one
    in the product step.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": 1e200, "y": 1e200},
        {"_id": 2, "partition": "A", "x": -1e200, "y": -1e200},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": FLOAT_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="product overflow with finite deviations preserves the sign",
    )


def test_covariancePop_product_overflow_finite_deviations_negative(collection):
    """$covariancePop anti-correlated 1e200 -- product overflows to -Infinity.

    Negative-direction half of the control pair.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": 1e200, "y": -1e200},
        {"_id": 2, "partition": "A", "x": -1e200, "y": 1e200},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": FLOAT_NEGATIVE_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="anti-correlated product overflow gives -Infinity",
    )


def test_covariancePop_product_overflow_finite_deviations_decimal128(collection):
    """$covariancePop with x=y=[1E+3100, -1E+3100] -- decimal product overflow.

    Decimal128 half of the control: deviations reach 2E+3100 (well inside range)
    while their product exceeds E+6144.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": Decimal128("1E+3100"), "y": Decimal128("1E+3100")},
        {"_id": 2, "partition": "A", "x": Decimal128("-1E+3100"), "y": Decimal128("-1E+3100")},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": DECIMAL128_INFINITY} for doc in docs]
    assertSuccess(
        result,
        expected,
        msg="decimal product overflow with finite deviations preserves the sign",
    )


# --- Case 4: true result exceeds the type range ---


def test_covariancePop_result_exceeds_decimal128_range(collection):
    """$covariancePop with x=y=DECIMAL128_MAX repeated -- server returns NaN.

    Identical values in both columns, so the formula gives 0, but The server's
    sum-derived mean overflows in both accumulators and the indeterminate
    Infinity - Infinity yields NaN.
    """
    docs = [
        {"_id": 1, "partition": "A", "x": DECIMAL128_MAX, "y": DECIMAL128_MAX},
        {"_id": 2, "partition": "A", "x": DECIMAL128_MAX, "y": DECIMAL128_MAX},
        {"_id": 3, "partition": "A", "x": DECIMAL128_MAX, "y": DECIMAL128_MAX},
    ]
    result = run_window_operator(
        collection,
        "$covariancePop",
        docs,
        {"documents": ["unbounded", "unbounded"]},
        expression=["$x", "$y"],
    )
    expected = [{**doc, "result": Decimal128("NaN")} for doc in docs]
    assertSuccessNaN(
        result,
        expected,
        msg="DECIMAL128_MAX in both columns overflows both means to NaN",
    )
