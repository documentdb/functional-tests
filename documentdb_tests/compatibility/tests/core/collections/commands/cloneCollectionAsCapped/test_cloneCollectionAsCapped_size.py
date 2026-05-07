"""Tests for cloneCollectionAsCapped size parameter validation."""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_HALF,
    DECIMAL128_INFINITY,
    DECIMAL128_JUST_BELOW_HALF,
    DECIMAL128_LARGE_EXPONENT,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_HALF,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ONE_AND_HALF,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_SMALL_EXPONENT,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_MAX,
)

# Property [Size Upper Bound Success]: the maximum accepted size is
# 1 PiB (1,125,899,906,842,624 bytes), inclusive.
SIZE_UPPER_BOUND_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "one_pib",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Int64(1_125_899_906_842_624),
        },
        expected={"ok": 1.0},
        msg="1 PiB should be accepted",
    ),
]

# Property [Size Upper Bound Error]: values exceeding 1 PiB or
# positive infinity produce BAD_VALUE_ERROR.
SIZE_BAD_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "one_over_pib",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Int64(1_125_899_906_842_625),
        },
        error_code=BAD_VALUE_ERROR,
        msg="1 PiB + 1 should exceed limit",
    ),
    CommandTestCase(
        "int64_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": INT64_MAX,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Int64 max should exceed PiB limit",
    ),
    CommandTestCase(
        "float_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": FLOAT_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="float +Infinity should exceed PiB limit",
    ),
    CommandTestCase(
        "decimal128_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 +Infinity should exceed PiB limit",
    ),
    CommandTestCase(
        "decimal128_large_exponent",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_LARGE_EXPONENT,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Extreme large exponent should exceed PiB limit",
    ),
]

# Property [Size Type Errors]: non-numeric BSON types and missing
# size field produce INVALID_OPTIONS_ERROR.
SIZE_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "string",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": "100",
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="string size should fail",
    ),
    CommandTestCase(
        "bool",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": True,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="bool size should fail",
    ),
    CommandTestCase(
        "null",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": None,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="null size should fail",
    ),
    CommandTestCase(
        "array",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": [1, 2],
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="array size should fail",
    ),
    CommandTestCase(
        "object",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": {"a": 1},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="object size should fail",
    ),
    CommandTestCase(
        "objectid",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": ObjectId("000000000000000000000001"),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="ObjectId size should fail",
    ),
    CommandTestCase(
        "datetime",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="datetime size should fail",
    ),
    CommandTestCase(
        "timestamp",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Timestamp(1, 1),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Timestamp size should fail",
    ),
    CommandTestCase(
        "binary",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Binary(b"\x01"),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Binary size should fail",
    ),
    CommandTestCase(
        "regex",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Regex("abc", "i"),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Regex size should fail",
    ),
    CommandTestCase(
        "code",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Code("function(){}"),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Code size should fail",
    ),
    CommandTestCase(
        "code_with_scope",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Code("function(){}", {"x": 1}),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Code with scope size should fail",
    ),
    CommandTestCase(
        "minkey",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": MinKey(),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="MinKey size should fail",
    ),
    CommandTestCase(
        "maxkey",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": MaxKey(),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="MaxKey size should fail",
    ),
    CommandTestCase(
        "missing",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="missing size should fail",
    ),
]

# Property [Size Invalid Numeric Values]: zero, NaN, negative values,
# and fractional values that truncate or round to zero or negative
# produce INVALID_OPTIONS_ERROR.
SIZE_INVALID_NUMERIC_TESTS: list[CommandTestCase] = [
    # Zero values
    CommandTestCase(
        "int32_zero",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 0,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="int32 zero should fail",
    ),
    CommandTestCase(
        "double_zero",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DOUBLE_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="double 0.0 should fail",
    ),
    CommandTestCase(
        "double_negative_zero",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DOUBLE_NEGATIVE_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="double -0.0 should fail",
    ),
    CommandTestCase(
        "decimal128_zero",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128('0') should fail",
    ),
    CommandTestCase(
        "decimal128_negative_zero",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_NEGATIVE_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128('-0') should fail",
    ),
    # Negative integers
    CommandTestCase(
        "negative_int32",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": -1,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="negative int32 should fail with invalid options error",
    ),
    CommandTestCase(
        "negative_int64",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": Int64(-100),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="negative Int64 should fail with invalid options error",
    ),
    # NaN and infinity
    CommandTestCase(
        "float_nan",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": FLOAT_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="float NaN should fail",
    ),
    CommandTestCase(
        "decimal128_nan",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 NaN should fail",
    ),
    CommandTestCase(
        "float_negative_nan",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": FLOAT_NEGATIVE_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="float -NaN should fail",
    ),
    CommandTestCase(
        "decimal128_negative_nan",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 -NaN should fail",
    ),
    CommandTestCase(
        "float_negative_infinity",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="float -Infinity should fail with invalid options error, not bad value",
    ),
    CommandTestCase(
        "decimal128_negative_infinity",
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 -Infinity should fail with invalid options error, not bad value",
    ),
    # Double truncation to zero or negative
    CommandTestCase(
        "double_fractional_below_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": 0.5,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="0.5 truncates to 0 and should fail",
    ),
    CommandTestCase(
        "double_negative_fractional_near_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": -0.5,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="-0.5 truncates to 0 and should fail",
    ),
    CommandTestCase(
        "double_negative_1_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": -1.5,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="-1.5 should fail with INVALID_OPTIONS_ERROR",
    ),
    # Decimal128 rounding to zero or negative
    CommandTestCase(
        "decimal128_half_rounds_to_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_HALF,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="0.5 rounds to 0 and should fail",
    ),
    CommandTestCase(
        "decimal128_just_below_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_JUST_BELOW_HALF,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="34-digit value at 0.5 boundary rounds to 0",
    ),
    CommandTestCase(
        "decimal128_negative_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_NEGATIVE_HALF,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="-0.5 rounds to 0 and should fail",
    ),
    CommandTestCase(
        "decimal128_negative_one_and_half",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_NEGATIVE_ONE_AND_HALF,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="-1.5 rounds to -2 and should fail",
    ),
    CommandTestCase(
        "decimal128_small_exponent",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_capped",
            "size": DECIMAL128_SMALL_EXPONENT,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Extreme small exponent rounds to 0",
    ),
]

SIZE_TESTS: list[CommandTestCase] = (
    SIZE_UPPER_BOUND_SUCCESS_TESTS
    + SIZE_BAD_VALUE_ERROR_TESTS
    + SIZE_TYPE_ERROR_TESTS
    + SIZE_INVALID_NUMERIC_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(SIZE_TESTS))
def test_clone_collection_as_capped_size(database_client, collection, test):
    """Test cloneCollectionAsCapped size parameter validation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
