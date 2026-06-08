"""
Numeric comparison tests for $min update field operator.

Tests same-type numeric comparisons, cross-type numeric comparisons,
special numeric values (NaN, Infinity), and precision edge cases.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX,
    INT32_MAX,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Numeric Comparison]: $min correctly compares same-type and cross-type numerics
# including boundaries and special values.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_less_updates",
        setup_docs=[{"_id": 1, "val": 20}],
        query={"_id": 1},
        update={"$min": {"val": 10}},
        expected={"_id": 1, "val": 10},
        msg="$min with Int32 specified < current should update",
    ),
    UpdateTestCase(
        "int32_greater_unchanged",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$min": {"val": 20}},
        expected={"_id": 1, "val": 10},
        msg="$min with Int32 specified > current should not update",
    ),
    UpdateTestCase(
        "int64_less_updates",
        setup_docs=[{"_id": 1, "val": Int64(20)}],
        query={"_id": 1},
        update={"$min": {"val": Int64(10)}},
        expected={"_id": 1, "val": Int64(10)},
        msg="$min with Int64 specified < current should update",
    ),
    UpdateTestCase(
        "int64_greater_unchanged",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$min": {"val": Int64(20)}},
        expected={"_id": 1, "val": Int64(10)},
        msg="$min with Int64 specified > current should not update",
    ),
    UpdateTestCase(
        "double_less_updates",
        setup_docs=[{"_id": 1, "val": 20.5}],
        query={"_id": 1},
        update={"$min": {"val": 10.5}},
        expected={"_id": 1, "val": 10.5},
        msg="$min with Double specified < current should update",
    ),
    UpdateTestCase(
        "double_greater_unchanged",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$min": {"val": 20.5}},
        expected={"_id": 1, "val": 10.5},
        msg="$min with Double specified > current should not update",
    ),
    UpdateTestCase(
        "decimal128_less_updates",
        setup_docs=[{"_id": 1, "val": Decimal128("20.5")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("10.5")}},
        expected={"_id": 1, "val": Decimal128("10.5")},
        msg="$min with Decimal128 specified < current should update",
    ),
    UpdateTestCase(
        "decimal128_greater_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("10.5")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("20.5")}},
        expected={"_id": 1, "val": Decimal128("10.5")},
        msg="$min with Decimal128 specified > current should not update",
    ),
    UpdateTestCase(
        "int32_less_than_int64_updates",
        setup_docs=[{"_id": 1, "val": Int64(20)}],
        query={"_id": 1},
        update={"$min": {"val": 10}},
        expected={"_id": 1, "val": 10},
        msg="$min with current Int64(20), specified Int32(10) should update",
    ),
    UpdateTestCase(
        "double_less_than_int32_updates",
        setup_docs=[{"_id": 1, "val": 20}],
        query={"_id": 1},
        update={"$min": {"val": 10.5}},
        expected={"_id": 1, "val": 10.5},
        msg="$min with current Int32(20), specified Double(10.5) should update",
    ),
    UpdateTestCase(
        "int64_less_than_decimal128_updates",
        setup_docs=[{"_id": 1, "val": Decimal128("20")}],
        query={"_id": 1},
        update={"$min": {"val": Int64(10)}},
        expected={"_id": 1, "val": Int64(10)},
        msg="$min with current Decimal128(20), specified Int64(10) should update",
    ),
    UpdateTestCase(
        "int32_less_than_double_updates",
        setup_docs=[{"_id": 1, "val": 20.5}],
        query={"_id": 1},
        update={"$min": {"val": 10}},
        expected={"_id": 1, "val": 10},
        msg="$min with current Double(20.5), specified Int32(10) should update",
    ),
    UpdateTestCase(
        "int32_equal_double_unchanged",
        setup_docs=[{"_id": 1, "val": 1}],
        query={"_id": 1},
        update={"$min": {"val": 1.0}},
        expected={"_id": 1, "val": 1},
        msg="$min comparing Int32(1) with Double(1.0) should not update (equal)",
    ),
    UpdateTestCase(
        "double_less_than_int32_current_updates",
        setup_docs=[{"_id": 1, "val": 2}],
        query={"_id": 1},
        update={"$min": {"val": 1.5}},
        expected={"_id": 1, "val": 1.5},
        msg="$min current Int32(2) > specified Double(1.5) should update",
    ),
    UpdateTestCase(
        "int32_greater_than_double_current_unchanged",
        setup_docs=[{"_id": 1, "val": 1.5}],
        query={"_id": 1},
        update={"$min": {"val": 2}},
        expected={"_id": 1, "val": 1.5},
        msg="$min current Double(1.5) < specified Int32(2), no update",
    ),
    UpdateTestCase(
        "double_tiny_difference",
        setup_docs=[{"_id": 1, "val": 1.0000000000000004}],
        query={"_id": 1},
        update={"$min": {"val": 1.0000000000000002}},
        expected={"_id": 1, "val": 1.0000000000000002},
        msg="$min with very small double difference should update",
    ),
    UpdateTestCase(
        "int32_min_boundary",
        setup_docs=[{"_id": 1, "val": INT32_MIN_PLUS_1}],
        query={"_id": 1},
        update={"$min": {"val": INT32_MIN}},
        expected={"_id": 1, "val": INT32_MIN},
        msg="$min at Int32 min boundary should update",
    ),
    UpdateTestCase(
        "int32_max_boundary_unchanged",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$min": {"val": Int64(INT32_MAX + 1)}},
        expected={"_id": 1, "val": INT32_MAX},
        msg="$min at Int32 max boundary with larger Int64 should not update",
    ),
    UpdateTestCase(
        "int64_min_boundary",
        setup_docs=[{"_id": 1, "val": INT64_MIN_PLUS_1}],
        query={"_id": 1},
        update={"$min": {"val": INT64_MIN}},
        expected={"_id": 1, "val": INT64_MIN},
        msg="$min at Int64 min boundary should update",
    ),
    UpdateTestCase(
        "int64_max_boundary_unchanged",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$min": {"val": INT64_MAX_MINUS_1}},
        expected={"_id": 1, "val": INT64_MAX_MINUS_1},
        msg="$min at Int64 max should update to max-1",
    ),
    UpdateTestCase(
        "double_max_value",
        setup_docs=[{"_id": 1, "val": DOUBLE_MAX}],
        query={"_id": 1},
        update={"$min": {"val": 1.0}},
        expected={"_id": 1, "val": 1.0},
        msg="$min with Double MAX_VALUE current should update to smaller",
    ),
    UpdateTestCase(
        "decimal128_large_value",
        setup_docs=[{"_id": 1, "val": Decimal128("9999999999999999999999999999999999")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("10")}},
        expected={"_id": 1, "val": Decimal128("10")},
        msg="$min with large Decimal128 current should update to smaller",
    ),
    UpdateTestCase(
        "negative_infinity_updates",
        setup_docs=[{"_id": 1, "val": 999999999}],
        query={"_id": 1},
        update={"$min": {"val": float("-inf")}},
        expected={"_id": 1, "val": float("-inf")},
        msg="$min with -Infinity specified vs finite current should update",
    ),
    UpdateTestCase(
        "positive_infinity_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$min": {"val": float("inf")}},
        expected={"_id": 1, "val": 5},
        msg="$min with Infinity specified vs finite current should not update",
    ),
    UpdateTestCase(
        "finite_vs_neg_infinity_unchanged",
        setup_docs=[{"_id": 1, "val": float("-inf")}],
        query={"_id": 1},
        update={"$min": {"val": -999999999}},
        expected={"_id": 1, "val": float("-inf")},
        msg="$min with finite vs -Infinity current should not update",
    ),
    UpdateTestCase(
        "finite_vs_infinity_updates",
        setup_docs=[{"_id": 1, "val": float("inf")}],
        query={"_id": 1},
        update={"$min": {"val": 5}},
        expected={"_id": 1, "val": 5},
        msg="$min with finite specified vs Infinity current should update",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_updates",
        setup_docs=[{"_id": 1, "val": Decimal128("999")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("-Infinity")}},
        expected={"_id": 1, "val": Decimal128("-Infinity")},
        msg="$min with Decimal128 -Infinity specified should update",
    ),
    UpdateTestCase(
        "decimal128_infinity_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("999")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("Infinity")}},
        expected={"_id": 1, "val": Decimal128("999")},
        msg="$min with Decimal128 Infinity specified should not update",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_current_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("-Infinity")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("-999")}},
        expected={"_id": 1, "val": Decimal128("-Infinity")},
        msg="$min with Decimal128 -Infinity current should not update",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_vs_zero_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("0")}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("-0")}},
        expected={"_id": 1, "val": Decimal128("0")},
        msg="$min with Decimal128('-0') vs Decimal128('0') should not update (equal)",
    ),
]

# Property [NaN Ordering]: NaN is less than all numbers in BSON comparison order.
NAN_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "double_nan_updates",
        setup_docs=[{"_id": 1, "val": 0}],
        query={"_id": 1},
        update={"$min": {"val": float("nan")}},
        expected={"n": 1, "nModified": 1},
        msg="$min with Double NaN should update (NaN < all numbers in BSON)",
    ),
    UpdateTestCase(
        "decimal128_nan_updates",
        setup_docs=[{"_id": 1, "val": 0}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("NaN")}},
        expected={"n": 1, "nModified": 1},
        msg="$min with Decimal128 NaN should update (NaN < all numbers in BSON)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_min_numeric_comparisons(collection, test: UpdateTestCase):
    """Test $min numeric comparisons produce expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(NAN_TESTS))
def test_min_nan_updates(collection, test: UpdateTestCase):
    """Test $min with NaN values updates (NaN is less than numbers in BSON)."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)
