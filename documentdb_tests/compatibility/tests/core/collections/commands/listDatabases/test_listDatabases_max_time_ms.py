"""Tests for listDatabases maxTimeMS parameter."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    basic_success,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
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
    INT32_MAX,
    INT64_ZERO,
)

# Property [maxTimeMS Accepted Values]: maxTimeMS accepts int32,
# Int64, double, and Decimal128 whole numbers up to INT32_MAX,
# including negative-zero representations.
MAX_TIME_MS_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": 1_000},
        expected=basic_success,
        msg="maxTimeMS with int32 should be accepted",
        id="max_time_ms_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": INT64_ZERO},
        expected=basic_success,
        msg="maxTimeMS with Int64 zero should be accepted",
        id="max_time_ms_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": 1_000.0},
        expected=basic_success,
        msg="maxTimeMS with double should be accepted",
        id="max_time_ms_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Decimal128("1000")},
        expected=basic_success,
        msg="maxTimeMS with Decimal128 should be accepted",
        id="max_time_ms_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": INT32_MAX},
        expected=basic_success,
        msg="maxTimeMS with max 32-bit integer should be accepted",
        id="max_time_ms_int32_max",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": DOUBLE_NEGATIVE_ZERO},
        expected=basic_success,
        msg="maxTimeMS with -0.0 should be accepted as zero",
        id="max_time_ms_neg_zero",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": DECIMAL128_NEGATIVE_ZERO},
        expected=basic_success,
        msg="maxTimeMS with Decimal128 -0 should be accepted as zero",
        id="max_time_ms_decimal128_neg_zero",
    ),
]

# Property [maxTimeMS Type Errors]: maxTimeMS rejects non-numeric
# BSON types with a TypeMismatch error.
MAX_TIME_MS_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with bool should produce TypeMismatch",
        id="max_time_ms_bool_true",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": "abc"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with string should produce TypeMismatch",
        id="max_time_ms_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": [1]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with array should produce TypeMismatch",
        id="max_time_ms_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": {}},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with object should produce TypeMismatch",
        id="max_time_ms_object",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with ObjectId should produce TypeMismatch",
        id="max_time_ms_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with datetime should produce TypeMismatch",
        id="max_time_ms_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with Timestamp should produce TypeMismatch",
        id="max_time_ms_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with Binary should produce TypeMismatch",
        id="max_time_ms_binary",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "maxTimeMS": Binary(
                b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10",
                subtype=4,
            ),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with Binary UUID should produce TypeMismatch",
        id="max_time_ms_binary_uuid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with Regex should produce TypeMismatch",
        id="max_time_ms_regex",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with Code should produce TypeMismatch",
        id="max_time_ms_code",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Code("function(){}", {"x": 1})},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with CodeWithScope should produce TypeMismatch",
        id="max_time_ms_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with MinKey should produce TypeMismatch",
        id="max_time_ms_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="maxTimeMS with MaxKey should produce TypeMismatch",
        id="max_time_ms_maxkey",
    ),
]

# Property [maxTimeMS Fractional and Non-Finite Errors]: maxTimeMS
# rejects fractional values, NaN, and Infinity with a parse error.
MAX_TIME_MS_FRACTIONAL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": 1.5},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with fractional double should produce FailedToParse",
        id="max_time_ms_fractional_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": DECIMAL128_ONE_AND_HALF},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with fractional Decimal128 should produce FailedToParse",
        id="max_time_ms_fractional_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": FLOAT_NAN},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with NaN should produce FailedToParse",
        id="max_time_ms_nan",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": FLOAT_INFINITY},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with Infinity should produce FailedToParse",
        id="max_time_ms_infinity",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": FLOAT_NEGATIVE_INFINITY},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with -Infinity should produce FailedToParse",
        id="max_time_ms_neg_infinity",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": DECIMAL128_NAN},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with Decimal128 NaN should produce FailedToParse",
        id="max_time_ms_decimal128_nan",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": DECIMAL128_INFINITY},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with Decimal128 Infinity should produce FailedToParse",
        id="max_time_ms_decimal128_infinity",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": DECIMAL128_NEGATIVE_INFINITY},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="maxTimeMS with Decimal128 -Infinity should produce FailedToParse",
        id="max_time_ms_decimal128_neg_infinity",
    ),
]

# Property [maxTimeMS Negative and Overflow Errors]: maxTimeMS
# rejects negative finite values and values exceeding INT32_MAX with a
# bad value error.
MAX_TIME_MS_NEGATIVE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": -1},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS with negative int32 should produce BadValue",
        id="max_time_ms_neg_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Int64(-100)},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS with negative Int64 should produce BadValue",
        id="max_time_ms_neg_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": -1.0},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS with negative double should produce BadValue",
        id="max_time_ms_neg_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Decimal128("-1")},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS with negative Decimal128 should produce BadValue",
        id="max_time_ms_neg_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": INT32_MAX + 1},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS exceeding INT32_MAX as int should produce BadValue",
        id="max_time_ms_exceeds_int32_max_int",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Int64(INT32_MAX + 1)},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS exceeding INT32_MAX as Int64 should produce BadValue",
        id="max_time_ms_exceeds_int32_max_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": float(INT32_MAX + 1)},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS exceeding INT32_MAX as double should produce BadValue",
        id="max_time_ms_exceeds_int32_max_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "maxTimeMS": Decimal128(str(INT32_MAX + 1))},
        error_code=BAD_VALUE_ERROR,
        msg="maxTimeMS exceeding INT32_MAX as Decimal128 should produce BadValue",
        id="max_time_ms_exceeds_int32_max_decimal128",
    ),
]

MAX_TIME_MS_TESTS: list[CommandTestCase] = (
    MAX_TIME_MS_ACCEPTED_TESTS
    + MAX_TIME_MS_TYPE_ERROR_TESTS
    + MAX_TIME_MS_FRACTIONAL_ERROR_TESTS
    + MAX_TIME_MS_NEGATIVE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(MAX_TIME_MS_TESTS))
def test_listDatabases_max_time_ms(collection, test):
    """Test listDatabases maxTimeMS parameter behavior."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
