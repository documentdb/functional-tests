"""
Overflow and underflow tests for $inc update field operator.

Tests int32 overflow to int64 promotion, int64 overflow errors,
int64 boundary cases, and double overflow to Infinity.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DOUBLE_MAX,
    INT32_MAX,
    INT32_MAX_MINUS_1,
    INT32_MIN,
    INT32_MIN_PLUS_1,
    INT64_MAX,
    INT64_MAX_MINUS_1,
    INT64_MIN,
    INT64_MIN_PLUS_1,
)

# Property [Int32 Overflow]: $inc promotes int32 to int64 when result exceeds int32 range.
INT32_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int32_max_plus_1",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        expected={"_id": 1, "val": Int64(2_147_483_648)},
        msg="$inc should promote INT32_MAX + 1 to int64",
    ),
    UpdateTestCase(
        "int32_max_plus_int32_max",
        setup_docs=[{"_id": 1, "val": INT32_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": INT32_MAX}},
        expected={"_id": 1, "val": Int64(4_294_967_294)},
        msg="$inc should promote INT32_MAX + INT32_MAX to int64",
    ),
    UpdateTestCase(
        "int32_min_minus_1",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        expected={"_id": 1, "val": Int64(-2_147_483_649)},
        msg="$inc should promote INT32_MIN - 1 to int64",
    ),
    UpdateTestCase(
        "int32_min_plus_int32_min",
        setup_docs=[{"_id": 1, "val": INT32_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": INT32_MIN}},
        expected={"_id": 1, "val": Int64(-4_294_967_296)},
        msg="$inc should promote INT32_MIN + INT32_MIN to int64",
    ),
    UpdateTestCase(
        "int32_max_minus_1_plus_1_stays_int32",
        setup_docs=[{"_id": 1, "val": INT32_MAX_MINUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        expected={"_id": 1, "val": INT32_MAX},
        msg="$inc should stay int32 when result is exactly INT32_MAX",
    ),
    UpdateTestCase(
        "int32_min_plus_1_minus_1_stays_int32",
        setup_docs=[{"_id": 1, "val": INT32_MIN_PLUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        expected={"_id": 1, "val": INT32_MIN},
        msg="$inc should stay int32 when result is exactly INT32_MIN",
    ),
]

# Property [Int64 Overflow]: $inc produces an error when int64 result exceeds int64 range.
INT64_OVERFLOW_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int64_max_plus_1_int32",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MAX + int32(1) overflow",
    ),
    UpdateTestCase(
        "int64_max_plus_1_int64",
        setup_docs=[{"_id": 1, "val": INT64_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(1)}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MAX + int64(1) overflow",
    ),
    UpdateTestCase(
        "int64_min_minus_1_int32",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MIN - int32(1) underflow",
    ),
    UpdateTestCase(
        "int64_min_minus_1_int64",
        setup_docs=[{"_id": 1, "val": INT64_MIN}],
        query={"_id": 1},
        update={"$inc": {"val": Int64(-1)}},
        error_code=BAD_VALUE_ERROR,
        msg="$inc should error on INT64_MIN - int64(1) underflow",
    ),
]

# Property [Int64 Boundary]: $inc stays int64 when result is at the int64 boundary.
INT64_BOUNDARY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "int64_max_minus_1_plus_1_stays_int64",
        setup_docs=[{"_id": 1, "val": INT64_MAX_MINUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": 1}},
        expected={"_id": 1, "val": INT64_MAX},
        msg="$inc should stay int64 when result is exactly INT64_MAX",
    ),
    UpdateTestCase(
        "int64_min_plus_1_minus_1_stays_int64",
        setup_docs=[{"_id": 1, "val": INT64_MIN_PLUS_1}],
        query={"_id": 1},
        update={"$inc": {"val": -1}},
        expected={"_id": 1, "val": INT64_MIN},
        msg="$inc should stay int64 when result is exactly INT64_MIN",
    ),
]

# Property [Double Overflow]: $inc produces Infinity when double exceeds max finite value.
DOUBLE_OVERFLOW_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "double_max_plus_double_max",
        setup_docs=[{"_id": 1, "val": DOUBLE_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": DOUBLE_MAX}},
        expected={"_id": 1, "val": float("inf")},
        msg="$inc should produce Infinity when DOUBLE_MAX + DOUBLE_MAX overflows",
    ),
    UpdateTestCase(
        "negative_double_max_plus_negative_double_max",
        setup_docs=[{"_id": 1, "val": -DOUBLE_MAX}],
        query={"_id": 1},
        update={"$inc": {"val": -DOUBLE_MAX}},
        expected={"_id": 1, "val": float("-inf")},
        msg="$inc should produce -Infinity when -DOUBLE_MAX + -DOUBLE_MAX overflows",
    ),
]

ALL_SUCCESS_TESTS = INT32_OVERFLOW_TESTS + INT64_BOUNDARY_TESTS + DOUBLE_OVERFLOW_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_SUCCESS_TESTS))
def test_inc_overflow_success(collection, test: UpdateTestCase):
    """Test $inc overflow and boundary behavior with successful updates."""
    collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(INT64_OVERFLOW_ERROR_TESTS))
def test_inc_int64_overflow_error(collection, test: UpdateTestCase):
    """Test $inc int64 overflow produces error."""
    collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assert test.error_code is not None
    assertFailureCode(result, test.error_code, msg=test.msg)
