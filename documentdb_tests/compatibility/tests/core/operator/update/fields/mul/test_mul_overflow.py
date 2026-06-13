"""
Overflow and boundary tests for $mul update field operator.

Tests int32 to int64 promotion on overflow, double overflow to infinity,
and Decimal128 precision/overflow/underflow.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessNaN
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_MANY_TRAILING_ZEROS,
    DECIMAL128_MAX,
    DECIMAL128_MIN,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_TRAILING_ZERO,
    DOUBLE_MAX,
    DOUBLE_MIN,
    DOUBLE_MIN_SUBNORMAL,
    INT32_MAX,
    INT32_MIN,
    INT64_MAX,
    INT64_MIN,
)

INT32_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_max_x_2",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": 2}},
        expected={"_id": 1, "val": Int64(4294967294)},
        msg="INT32_MAX × 2 should promote to int64",
    ),
    UpdateTestCase(
        "int32_min_x_neg1",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": -1}},
        expected={"_id": 1, "val": Int64(2147483648)},
        msg="INT32_MIN × (-1) should promote to int64 (two's complement asymmetry)",
    ),
    UpdateTestCase(
        "int32_min_x_2",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": 2}},
        expected={"_id": 1, "val": Int64(-4294967296)},
        msg="INT32_MIN × 2 should promote to int64",
    ),
    UpdateTestCase(
        "int32_half_max_x_2",
        setup_docs=[{"_id": 1, "val": 1073741824}],
        query={"_id": 1},
        update={"$mul": {"val": 2}},
        expected={"_id": 1, "val": Int64(2147483648)},
        msg="int32(1073741824) × 2 should promote to int64 (exceeds INT32_MAX)",
    ),
    UpdateTestCase(
        "int32_max_x_int32_max",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": INT32_MAX}},
        expected={"_id": 1, "val": Int64(4611686014132420609)},
        msg="INT32_MAX × INT32_MAX should promote to int64",
    ),
]

NO_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_max_x_1",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": 1}},
        expected={"_id": 1, "val": INT32_MAX},
        msg="INT32_MAX × 1 should stay int32",
    ),
    UpdateTestCase(
        "int32_max_x_neg1",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": -1}},
        expected={"_id": 1, "val": -INT32_MAX},
        msg="INT32_MAX × (-1) should stay int32 (no overflow)",
    ),
    UpdateTestCase(
        "int64_max_x_1",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(1)}},
        expected={"_id": 1, "val": INT64_MAX},
        msg="INT64_MAX × 1 should stay int64",
    ),
    UpdateTestCase(
        "int64_min_x_1",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": Int64(1)}},
        expected={"_id": 1, "val": INT64_MIN},
        msg="INT64_MIN × 1 should stay int64",
    ),
]

DOUBLE_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "double_max_x_2",
        setup_docs=[{"_id": 1, "val": DOUBLE_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": 2.0}},
        expected={"_id": 1, "val": float("inf")},
        msg="DOUBLE_MAX × 2 should produce Infinity",
    ),
    UpdateTestCase(
        "double_max_x_neg2",
        setup_docs=[{"_id": 1, "val": DOUBLE_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": -2.0}},
        expected={"_id": 1, "val": float("-inf")},
        msg="DOUBLE_MAX × (-2) should produce -Infinity",
    ),
    UpdateTestCase(
        "double_min_x_2",
        setup_docs=[{"_id": 1, "val": DOUBLE_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": 2.0}},
        expected={"_id": 1, "val": float("-inf")},
        msg="DOUBLE_MIN × 2 should produce -Infinity",
    ),
    UpdateTestCase(
        "double_subnormal_underflow",
        setup_docs=[{"_id": 1, "val": DOUBLE_MIN_SUBNORMAL}],
        query={"_id": 1},
        update={"$mul": {"val": DOUBLE_MIN_SUBNORMAL}},
        expected={"_id": 1, "val": 0.0},
        msg="DOUBLE_MIN_SUBNORMAL × DOUBLE_MIN_SUBNORMAL should underflow to 0.0",
    ),
]

DECIMAL128_PRECISION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "decimal128_max_x_1",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_MAX},
        msg="DECIMAL128_MAX × 1 should preserve value",
    ),
    UpdateTestCase(
        "decimal128_min_x_1",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_MIN},
        msg="DECIMAL128_MIN × 1 should preserve value",
    ),
    UpdateTestCase(
        "decimal128_trailing_zero_x_1",
        setup_docs=[{"_id": 1, "val": DECIMAL128_TRAILING_ZERO}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_TRAILING_ZERO},
        msg="Decimal128 trailing zero should be preserved",
    ),
    UpdateTestCase(
        "decimal128_many_trailing_zeros_x_1",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MANY_TRAILING_ZEROS}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_MANY_TRAILING_ZEROS},
        msg="Decimal128 many trailing zeros should be preserved",
    ),
    UpdateTestCase(
        "decimal128_small_exponent_x_1",
        setup_docs=[{"_id": 1, "val": DECIMAL128_SMALL_EXPONENT}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_SMALL_EXPONENT},
        msg="Decimal128 small exponent should be preserved",
    ),
    UpdateTestCase(
        "decimal128_large_exponent_x_1",
        setup_docs=[{"_id": 1, "val": DECIMAL128_LARGE_EXPONENT}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1")}},
        expected={"_id": 1, "val": DECIMAL128_LARGE_EXPONENT},
        msg="Decimal128 large exponent should be preserved",
    ),
    UpdateTestCase(
        "decimal128_underflow",
        setup_docs=[{"_id": 1, "val": Decimal128("1E-6176")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("0.1")}},
        expected={"_id": 1, "val": Decimal128("0E-6176")},
        msg="Decimal128 underflow should produce zero or clamped value",
    ),
    UpdateTestCase(
        "decimal128_rounding_exceeds_34_digits",
        setup_docs=[{"_id": 1, "val": Decimal128("1234567890123456789012345678901234")}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("1.1")}},
        expected={"_id": 1, "val": Decimal128("1358024679135802467913580246791357")},
        msg="Decimal128 multiplication exceeding 34 digits should round",
    ),
]

DECIMAL128_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "decimal128_max_x_2",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("2")}},
        expected={"_id": 1, "val": Decimal128("Infinity")},
        msg="DECIMAL128_MAX × 2 should produce Decimal128 Infinity",
    ),
    UpdateTestCase(
        "decimal128_min_x_2",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MIN}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("2")}},
        expected={"_id": 1, "val": Decimal128("-Infinity")},
        msg="DECIMAL128_MIN × 2 should produce Decimal128 -Infinity",
    ),
    UpdateTestCase(
        "decimal128_max_x_neg2",
        setup_docs=[{"_id": 1, "val": DECIMAL128_MAX}],
        query={"_id": 1},
        update={"$mul": {"val": Decimal128("-2")}},
        expected={"_id": 1, "val": Decimal128("-Infinity")},
        msg="DECIMAL128_MAX × (-2) should produce Decimal128 -Infinity",
    ),
]

ALL_SUCCESS_TESTS = (
    INT32_OVERFLOW_TESTS + NO_OVERFLOW_TESTS + DOUBLE_OVERFLOW_TESTS + DECIMAL128_PRECISION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_SUCCESS_TESTS))
def test_mul_overflow(collection, test: UpdateTestCase):
    """Test $mul overflow and boundary behavior."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(DECIMAL128_OVERFLOW_TESTS))
def test_mul_overflow_infinity(collection, test: UpdateTestCase):
    """Test $mul overflow producing Decimal128 Infinity/-Infinity."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccessNaN(result, [test.expected], msg=test.msg)
