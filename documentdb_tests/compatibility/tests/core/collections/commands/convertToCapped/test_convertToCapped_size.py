"""Tests for convertToCapped command - size parameter validation."""

import datetime

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
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
    DECIMAL128_MIN_POSITIVE,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_ZERO,
)

# Property [Size Parameter Success]: all numeric types that can represent a
# positive integer are accepted as the size parameter.
SIZE_PARAM_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_int32_exact",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Int32 value should be accepted",
    ),
    CommandTestCase(
        "size_int64_exact",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": Int64(8192)},
        expected={"ok": 1.0},
        msg="Int64 value should be accepted",
    ),
    CommandTestCase(
        "size_double_whole_number",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096.0},
        expected={"ok": 1.0},
        msg="Whole-number double should be accepted",
    ),
    CommandTestCase(
        "size_decimal128_whole_number",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": Decimal128("4096")},
        expected={"ok": 1.0},
        msg="Decimal128 whole number should be accepted",
    ),
    CommandTestCase(
        "size_minimum_value_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 1},
        expected={"ok": 1.0},
        msg="Minimum accepted effective value 1 should succeed",
    ),
    CommandTestCase(
        "size_maximum_value_1pb",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": Int64(1_125_899_906_842_624),
        },
        expected={"ok": 1.0},
        msg="Maximum accepted value (1 PB) should succeed",
    ),
    CommandTestCase(
        "size_double_fractional",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 3.9},
        expected={"ok": 1.0},
        msg="Double 3.9 (truncates to 3) should be accepted",
    ),
    CommandTestCase(
        "size_decimal128_rounds_up",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": Decimal128("0.51")},
        expected={"ok": 1.0},
        msg="Decimal128 0.51 (rounds to 1) should be accepted",
    ),
    CommandTestCase(
        "size_decimal128_rounds_0_6",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": Decimal128("0.6")},
        expected={"ok": 1.0},
        msg="Decimal128 0.6 rounds to 1, accepted as positive",
    ),
    CommandTestCase(
        "size_decimal128_bankers_round_1_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_ONE_AND_HALF,
        },
        expected={"ok": 1.0},
        msg="Decimal128 1.5 (banker's rounds to 2) should be accepted",
    ),
    CommandTestCase(
        "size_decimal128_bankers_round_2_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_TWO_AND_HALF,
        },
        expected={"ok": 1.0},
        msg="Decimal128 2.5 (banker's rounds to 2) should be accepted",
    ),
]

# Property [Missing Size]: omitting size produces an invalid options error.
MISSING_SIZE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "missing_size",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Omitting size entirely should produce an invalid options error",
    ),
]

# Property [Size Parameter Errors - Non-Numeric Types]: all non-numeric
# types for the size field produce an invalid-options error.
SIZE_PARAM_NON_NUMERIC_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"size_{id}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {"convertToCapped": ctx.collection, "size": v},
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"{id} size should be rejected as non-numeric",
    )
    for id, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("string", "4096"),
        ("array", [4096]),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"hello")),
        ("regex", Regex("pat", "i")),
        ("code", Code("function() {}")),
        ("code_with_scope", Code("function() {}", {"x": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Size Parameter Errors - Zero and Negative]: zero, negative,
# and NaN values produce an invalid-options error.
SIZE_PARAM_ZERO_NEGATIVE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_int32_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 0},
        error_code=INVALID_OPTIONS_ERROR,
        msg="int32 zero should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_int64_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": INT64_ZERO},
        error_code=INVALID_OPTIONS_ERROR,
        msg="int64 zero should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": DOUBLE_ZERO},
        error_code=INVALID_OPTIONS_ERROR,
        msg="double 0.0 should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DOUBLE_NEGATIVE_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="double -0.0 should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128('0') should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_negative_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_NEGATIVE_ZERO,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128('-0') should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_int32_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": -1},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Negative int32 should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_int64_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": Int64(-100),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Negative int64 should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": -3.14},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Negative double should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": Decimal128("-100"),
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Negative Decimal128 should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_coerces_to_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 0.9},
        error_code=INVALID_OPTIONS_ERROR,
        msg="double 0.9 truncates to 0, should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_0_6_truncates_to_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 0.6},
        error_code=INVALID_OPTIONS_ERROR,
        msg="double 0.6 truncates to 0, rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_coerces_to_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_HALF,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 0.5 rounds to 0 via banker's rounding, rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_subnormal",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_MIN_POSITIVE,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 subnormal coerces to 0, rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": FLOAT_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="double NaN should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 NaN should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_negative_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": FLOAT_NEGATIVE_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="double -NaN should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_negative_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_NEGATIVE_NAN,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 -NaN should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_double_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": FLOAT_NEGATIVE_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="double negative infinity should be rejected as not greater than zero",
    ),
    CommandTestCase(
        "size_decimal128_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_NEGATIVE_INFINITY,
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="Decimal128 negative infinity should be rejected as not greater than zero",
    ),
]

# Property [Size Parameter Errors - Exceeds Upper Limit]: positive infinity
# and values exceeding 1 PB produce a bad-value error.
SIZE_PARAM_EXCEEDS_LIMIT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "size_double_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": FLOAT_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="double positive infinity should be rejected as exceeding upper limit",
    ),
    CommandTestCase(
        "size_decimal128_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": DECIMAL128_INFINITY,
        },
        error_code=BAD_VALUE_ERROR,
        msg="Decimal128 positive infinity should be rejected as exceeding upper limit",
    ),
    CommandTestCase(
        "size_int64_exceeds_1pb",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": Int64(1_125_899_906_842_625),
        },
        error_code=BAD_VALUE_ERROR,
        msg="int64 one above 1 PB should be rejected as exceeding upper limit",
    ),
    CommandTestCase(
        "size_double_exceeds_limit_due_to_precision",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 1_125_899_906_842_624.9,
        },
        error_code=BAD_VALUE_ERROR,
        msg="double rounds to 1125899906842625 due to precision, exceeding 1PB limit",
    ),
]

CONVERT_TO_CAPPED_SIZE_TESTS: list[CommandTestCase] = (
    SIZE_PARAM_SUCCESS_TESTS
    + MISSING_SIZE_TESTS
    + SIZE_PARAM_NON_NUMERIC_ERROR_TESTS
    + SIZE_PARAM_ZERO_NEGATIVE_ERROR_TESTS
    + SIZE_PARAM_EXCEEDS_LIMIT_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CONVERT_TO_CAPPED_SIZE_TESTS))
def test_convert_to_capped_size(database_client, collection, test):
    """Test convertToCapped command size parameter validation."""
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
