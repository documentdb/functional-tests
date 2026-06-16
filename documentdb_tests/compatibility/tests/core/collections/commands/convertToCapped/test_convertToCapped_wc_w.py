"""Tests for convertToCapped writeConcern w field validation."""

from datetime import datetime, timezone

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

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [WriteConcern w Acceptance]: w accepts 0, 1, "majority",
# and numeric types that coerce to valid values on standalone.
WRITECONCERN_W_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_0",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": 0},
        },
        expected={"ok": 1.0},
        msg="w=0 should succeed",
    ),
    CommandTestCase(
        "w_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0},
        msg="w=1 should succeed",
    ),
    CommandTestCase(
        "w_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": "majority"},
        },
        expected={"ok": 1.0},
        msg="w='majority' should succeed",
    ),
    CommandTestCase(
        "w_double_truncation",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": 1.5},
        },
        expected={"ok": 1.0},
        msg="w=1.5 (double) should truncate to 1 and succeed",
    ),
    CommandTestCase(
        "w_int64_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Int64(1)},
        },
        expected={"ok": 1.0},
        msg="w=Int64(1) should succeed",
    ),
    CommandTestCase(
        "w_decimal128_1",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Decimal128("1")},
        },
        expected={"ok": 1.0},
        msg="w=Decimal128('1') should succeed",
    ),
    CommandTestCase(
        "w_object_tag",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {"dc1": 1}},
        },
        expected={"ok": 1.0},
        msg="w=object with numeric tag value should succeed",
    ),
]

# Property [WriteConcern w Type Rejection]: non-string, non-numeric,
# non-object types for w produce FAILED_TO_PARSE_ERROR.
WRITECONCERN_W_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": True},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=bool should fail with failed to parse",
    ),
    CommandTestCase(
        "w_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": [1, 2]},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=array should fail with failed to parse",
    ),
    CommandTestCase(
        "w_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": None},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=null should coerce to empty string and fail with bad value",
    ),
    CommandTestCase(
        "w_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": ObjectId("000000000000000000000001")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=ObjectId should fail with failed to parse",
    ),
    CommandTestCase(
        "w_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=datetime should fail with failed to parse",
    ),
    CommandTestCase(
        "w_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Timestamp(1, 1)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Timestamp should fail with failed to parse",
    ),
    CommandTestCase(
        "w_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Binary(b"\x01")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Binary should fail with failed to parse",
    ),
    CommandTestCase(
        "w_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Regex("abc", "i")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Regex should fail with failed to parse",
    ),
    CommandTestCase(
        "w_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Code("function(){}")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Code should fail with failed to parse",
    ),
    CommandTestCase(
        "w_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": MinKey()},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=MinKey should fail with failed to parse",
    ),
    CommandTestCase(
        "w_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": MaxKey()},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=MaxKey should fail with failed to parse",
    ),
]

# Property [WriteConcern w Numeric Range]: w values outside 0-50,
# NaN, and infinity produce FAILED_TO_PARSE_ERROR.
WRITECONCERN_W_NUMERIC_RANGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": -1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=-1 should fail with failed to parse",
    ),
    CommandTestCase(
        "w_over_50",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": 51},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=51 should fail with failed to parse",
    ),
    CommandTestCase(
        "w_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": FLOAT_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=NaN should fail with failed to parse",
    ),
    CommandTestCase(
        "w_negative_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": FLOAT_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=-NaN should fail with failed to parse",
    ),
    CommandTestCase(
        "w_positive_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=+Infinity should fail with failed to parse",
    ),
    CommandTestCase(
        "w_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=-Infinity should fail with failed to parse",
    ),
    CommandTestCase(
        "w_decimal128_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Decimal128("-1")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128('-1') should fail with failed to parse",
    ),
    CommandTestCase(
        "w_decimal128_over_50",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Decimal128("51")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128('51') should fail with failed to parse",
    ),
    CommandTestCase(
        "w_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": Decimal128("NaN")},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128 NaN should fail with failed to parse",
    ),
    CommandTestCase(
        "w_decimal128_negative_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128 -NaN should fail with failed to parse",
    ),
    CommandTestCase(
        "w_decimal128_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": DECIMAL128_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128 Infinity should fail with failed to parse",
    ),
    CommandTestCase(
        "w_decimal128_negative_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128 -Infinity should fail with failed to parse",
    ),
]

# Property [WriteConcern w Object Tag Rejection]: w as object rejects
# non-numeric tag values and empty objects with FAILED_TO_PARSE_ERROR.
WRITECONCERN_W_OBJECT_TAG_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_obj_empty",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=empty object should fail with failed to parse",
    ),
    CommandTestCase(
        "w_obj_null_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {"dc1": None}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=object with null tag value should fail",
    ),
    CommandTestCase(
        "w_obj_bool_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {"dc1": True}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=object with bool tag value should fail",
    ),
    CommandTestCase(
        "w_obj_string_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {"dc1": "hello"}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=object with string tag value should fail",
    ),
    CommandTestCase(
        "w_obj_nested_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {"dc1": {"nested": 1}}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=object with nested object tag value should fail",
    ),
    CommandTestCase(
        "w_obj_array_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": {"dc1": [1]}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=object with array tag value should fail",
    ),
]

# Property [WriteConcern w Standalone Rejection]: w > 1 or unrecognized
# string values produce BAD_VALUE_ERROR on standalone.
WRITECONCERN_W_STANDALONE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "w_2_standalone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": 2},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=2 on standalone should fail with bad value",
    ),
    CommandTestCase(
        "w_custom_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": "custom"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w='custom' on standalone should fail with bad value",
    ),
    CommandTestCase(
        "w_majority_case_sensitive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": "Majority"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w='Majority' (wrong case) on standalone should fail with bad value",
    ),
    CommandTestCase(
        "w_decimal128_1_5",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": DECIMAL128_ONE_AND_HALF},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=Decimal128('1.5') rounds to 2 and should fail with bad value on standalone",
    ),
    CommandTestCase(
        "w_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "convertToCapped": ctx.collection,
            "size": 100_000,
            "writeConcern": {"w": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=empty string should fail with bad value",
    ),
]

WC_W_TESTS: list[CommandTestCase] = (
    WRITECONCERN_W_ACCEPTANCE_TESTS
    + WRITECONCERN_W_TYPE_REJECTION_TESTS
    + WRITECONCERN_W_NUMERIC_RANGE_TESTS
    + WRITECONCERN_W_OBJECT_TAG_TESTS
    + WRITECONCERN_W_STANDALONE_REJECTION_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WC_W_TESTS))
def test_convert_to_capped_wc_w(database_client, collection, test):
    """Test convertToCapped writeConcern w field validation."""
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
