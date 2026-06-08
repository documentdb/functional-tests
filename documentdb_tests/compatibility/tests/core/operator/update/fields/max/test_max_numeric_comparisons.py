"""
Numeric comparison tests for $max update field operator.

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
    INT32_OVERFLOW,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Numeric Comparison]: $max correctly compares same-type and cross-type numerics
# including boundaries and special values.
TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_greater_updates",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 20}},
        expected={"_id": 1, "val": 20},
        msg="$max with Int32 specified > current should update",
    ),
    UpdateTestCase(
        "int32_less_unchanged",
        setup_docs=[{"_id": 1, "val": 20}],
        query={"_id": 1},
        update={"$max": {"val": 10}},
        expected={"_id": 1, "val": 20},
        msg="$max with Int32 specified < current should not update",
    ),
    UpdateTestCase(
        "int64_greater_updates",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$max": {"val": Int64(20)}},
        expected={"_id": 1, "val": Int64(20)},
        msg="$max with Int64 specified > current should update",
    ),
    UpdateTestCase(
        "int64_less_unchanged",
        setup_docs=[{"_id": 1, "val": Int64(20)}],
        query={"_id": 1},
        update={"$max": {"val": Int64(10)}},
        expected={"_id": 1, "val": Int64(20)},
        msg="$max with Int64 specified < current should not update",
    ),
    UpdateTestCase(
        "double_greater_updates",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$max": {"val": 20.5}},
        expected={"_id": 1, "val": 20.5},
        msg="$max with Double specified > current should update",
    ),
    UpdateTestCase(
        "double_less_unchanged",
        setup_docs=[{"_id": 1, "val": 20.5}],
        query={"_id": 1},
        update={"$max": {"val": 10.5}},
        expected={"_id": 1, "val": 20.5},
        msg="$max with Double specified < current should not update",
    ),
    UpdateTestCase(
        "decimal128_greater_updates",
        setup_docs=[{"_id": 1, "val": Decimal128("10.5")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("20.5")}},
        expected={"_id": 1, "val": Decimal128("20.5")},
        msg="$max with Decimal128 specified > current should update",
    ),
    UpdateTestCase(
        "decimal128_less_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("20.5")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("10.5")}},
        expected={"_id": 1, "val": Decimal128("20.5")},
        msg="$max with Decimal128 specified < current should not update",
    ),
    UpdateTestCase(
        "int32_to_int64_updates",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": Int64(20)}},
        expected={"_id": 1, "val": Int64(20)},
        msg="$max with current Int32(10), specified Int64(20) should update",
    ),
    UpdateTestCase(
        "int32_to_double_updates",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 20.5}},
        expected={"_id": 1, "val": 20.5},
        msg="$max with current Int32(10), specified Double(20.5) should update",
    ),
    UpdateTestCase(
        "int64_to_decimal128_updates",
        setup_docs=[{"_id": 1, "val": Int64(10)}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("20")}},
        expected={"_id": 1, "val": Decimal128("20")},
        msg="$max with current Int64(10), specified Decimal128(20) should update",
    ),
    UpdateTestCase(
        "double_to_int32_updates",
        setup_docs=[{"_id": 1, "val": 10.5}],
        query={"_id": 1},
        update={"$max": {"val": 20}},
        expected={"_id": 1, "val": 20},
        msg="$max with current Double(10.5), specified Int32(20) should update",
    ),
    UpdateTestCase(
        "int32_equal_double_unchanged",
        setup_docs=[{"_id": 1, "val": 1}],
        query={"_id": 1},
        update={"$max": {"val": 1.0}},
        expected={"_id": 1, "val": 1},
        msg="$max comparing Int32(1) with Double(1.0) should not update (equal)",
    ),
    UpdateTestCase(
        "double_greater_than_int32_unchanged",
        setup_docs=[{"_id": 1, "val": 1.5}],
        query={"_id": 1},
        update={"$max": {"val": 1}},
        expected={"_id": 1, "val": 1.5},
        msg="$max current Double(1.5) > specified Int32(1), no update",
    ),
    UpdateTestCase(
        "double_less_than_int32_updates",
        setup_docs=[{"_id": 1, "val": 1.5}],
        query={"_id": 1},
        update={"$max": {"val": 2}},
        expected={"_id": 1, "val": 2},
        msg="$max current Double(1.5) < specified Int32(2) should update",
    ),
    UpdateTestCase(
        "double_tiny_difference",
        setup_docs=[{"_id": 1, "val": 1.0000000000000002}],
        query={"_id": 1},
        update={"$max": {"val": 1.0000000000000004}},
        expected={"_id": 1, "val": 1.0000000000000004},
        msg="$max with very small double difference should update",
    ),
    UpdateTestCase(
        "int32_max_boundary",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$max": {"val": Int64(INT32_OVERFLOW)}},
        expected={"_id": 1, "val": Int64(INT32_OVERFLOW)},
        msg="$max at Int32 max boundary should update to Int64",
    ),
    UpdateTestCase(
        "int32_min_boundary",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$max": {"val": INT32_MIN_PLUS_1}},
        expected={"_id": 1, "val": INT32_MIN_PLUS_1},
        msg="$max at Int32 min boundary should update",
    ),
    UpdateTestCase(
        "int64_max_boundary",
        setup_docs=[{"_id": 1, "val": INT64_MAX_MINUS_1}],
        query={"_id": 1},
        update={"$max": {"val": INT64_MAX}},
        expected={"_id": 1, "val": INT64_MAX},
        msg="$max at Int64 near max should update to Int64 max",
    ),
    UpdateTestCase(
        "int64_min_boundary",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$max": {"val": INT64_MIN_PLUS_1}},
        expected={"_id": 1, "val": INT64_MIN_PLUS_1},
        msg="$max at Int64 min boundary should update",
    ),
    UpdateTestCase(
        "double_max_value",
        setup_docs=[{"_id": 1, "val": 1.0}],
        query={"_id": 1},
        update={"$max": {"val": DOUBLE_MAX}},
        expected={"_id": 1, "val": DOUBLE_MAX},
        msg="$max with Double MAX_VALUE should update",
    ),
    UpdateTestCase(
        "decimal128_large_value",
        setup_docs=[{"_id": 1, "val": Decimal128("10")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("9999999999999999999999999999999999")}},
        expected={"_id": 1, "val": Decimal128("9999999999999999999999999999999999")},
        msg="$max with large Decimal128 value should update",
    ),
    UpdateTestCase(
        "positive_infinity_updates",
        setup_docs=[{"_id": 1, "val": 999999999}],
        query={"_id": 1},
        update={"$max": {"val": float("inf")}},
        expected={"_id": 1, "val": float("inf")},
        msg="$max with Infinity specified vs finite current should update",
    ),
    UpdateTestCase(
        "finite_vs_infinity_unchanged",
        setup_docs=[{"_id": 1, "val": float("inf")}],
        query={"_id": 1},
        update={"$max": {"val": 999999999}},
        expected={"_id": 1, "val": float("inf")},
        msg="$max with finite vs Infinity current should not update",
    ),
    UpdateTestCase(
        "finite_vs_neg_infinity_updates",
        setup_docs=[{"_id": 1, "val": float("-inf")}],
        query={"_id": 1},
        update={"$max": {"val": -5}},
        expected={"_id": 1, "val": -5},
        msg="$max with finite specified vs -Infinity current should update",
    ),
    UpdateTestCase(
        "neg_infinity_vs_positive_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$max": {"val": float("-inf")}},
        expected={"_id": 1, "val": 5},
        msg="$max with -Infinity specified vs positive current should not update",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_current_updates",
        setup_docs=[{"_id": 1, "val": Decimal128("-Infinity")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("-999")}},
        expected={"_id": 1, "val": Decimal128("-999")},
        msg="$max with Decimal128 -Infinity current should update to finite",
    ),
    UpdateTestCase(
        "decimal128_infinity_specified_updates",
        setup_docs=[{"_id": 1, "val": Decimal128("999")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("Infinity")}},
        expected={"_id": 1, "val": Decimal128("Infinity")},
        msg="$max with Decimal128 Infinity specified should update",
    ),
    UpdateTestCase(
        "decimal128_infinity_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("Infinity")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("999")}},
        expected={"_id": 1, "val": Decimal128("Infinity")},
        msg="$max with Decimal128 Infinity current should not update",
    ),
    UpdateTestCase(
        "decimal128_neg_infinity_specified_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("-Infinity")}},
        expected={"_id": 1, "val": 5},
        msg="$max with Decimal128 -Infinity specified should not update",
    ),
    UpdateTestCase(
        "decimal128_neg_zero_vs_zero_unchanged",
        setup_docs=[{"_id": 1, "val": Decimal128("0")}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("-0")}},
        expected={"_id": 1, "val": Decimal128("0")},
        msg="$max with Decimal128('-0') vs Decimal128('0') should not update",
    ),
]

# Property [NaN Ordering]: NaN is less than all numbers in BSON, so $max with NaN never updates.
NAN_RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "double_nan_unchanged",
        setup_docs=[{"_id": 1, "val": 0}],
        query={"_id": 1},
        update={"$max": {"val": float("nan")}},
        expected={"n": 1, "nModified": 0},
        msg="$max with Double NaN should not be greater than 0",
    ),
    UpdateTestCase(
        "decimal128_nan_unchanged",
        setup_docs=[{"_id": 1, "val": 0}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("NaN")}},
        expected={"n": 1, "nModified": 0},
        msg="$max with Decimal128 NaN should not be greater than 0",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_max_numeric_comparisons(collection, test: UpdateTestCase):
    """Test $max numeric comparisons produce expected document."""
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


@pytest.mark.parametrize("test", pytest_params(NAN_RESULT_TESTS))
def test_max_nan_no_update(collection, test: UpdateTestCase):
    """Test $max with NaN values does not update (NaN comparison is special)."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)
