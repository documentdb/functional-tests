"""Tests for renameCollection writeConcern w sub-field."""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ONE_AND_HALF,
    DECIMAL128_TWO_AND_HALF,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_ZERO,
)

# Property [writeConcern Sub-Field - w Type]: the w field accepts
# number (int32, Int64, double, Decimal128), string, and object;
# all other BSON types produce a parse error.
RENAME_WC_W_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_w_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": v},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"w as {tid} should be rejected",
    )
    for tid, val in [
        ("bool", True),
        ("array", [1]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 1)),
        ("binary", Binary(b"data")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [writeConcern Sub-Field - w Numeric Coercion and Range]: w
# must be a non-negative integer ≤50 after truncation toward zero;
# non-finite values are rejected, and w>1 requires a replica set.
RENAME_WC_W_VALUE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": FLOAT_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=NaN should be rejected",
    ),
    CommandTestCase(
        "wc_w_pos_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=+Infinity should be rejected",
    ),
    CommandTestCase(
        "wc_w_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": FLOAT_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=-Infinity should be rejected",
    ),
    CommandTestCase(
        "wc_w_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128('NaN') should be rejected",
    ),
    CommandTestCase(
        "wc_w_decimal128_pos_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128('Infinity') should be rejected",
    ),
    CommandTestCase(
        "wc_w_decimal128_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_NEGATIVE_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128('-Infinity') should be rejected",
    ),
    CommandTestCase(
        "wc_w_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": FLOAT_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=negative NaN should be rejected",
    ),
    CommandTestCase(
        "wc_w_decimal128_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_NEGATIVE_NAN},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=Decimal128 negative NaN should be rejected",
    ),
    CommandTestCase(
        "wc_w_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": -1},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=-1 (negative) should be rejected",
    ),
    CommandTestCase(
        "wc_w_over_50",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 51},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w=51 (>50) should be rejected",
    ),
    CommandTestCase(
        "wc_w_2_standalone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 2},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=2 on standalone should be rejected",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_50_standalone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 50},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=50 on standalone should be rejected",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_decimal128_1_5_bankers_rounding",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_ONE_AND_HALF},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=Decimal128('1.5') rounds to 2 (banker's rounding) → w>1 on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_decimal128_2_5_bankers_rounding",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_TWO_AND_HALF},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=Decimal128('2.5') rounds to 2 (banker's rounding) → w>1 on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_decimal128_50_5_bankers_rounding",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": Decimal128("50.5")},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=Decimal128('50.5') rounds to 50 (banker's rounding) → w>1 on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
]

# Property [writeConcern Sub-Field - w Numeric Coercion Success]: double
# values are truncated toward zero; w=0 and w=1 are accepted on standalone.
RENAME_WC_W_VALUE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 0},
        },
        expected={"ok": 1.0},
        msg="w=0 should be accepted",
    ),
    CommandTestCase(
        "wc_w_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 1},
        },
        expected={"ok": 1.0},
        msg="w=1 should be accepted",
    ),
    CommandTestCase(
        "wc_w_double_truncated",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": 1.9},
        },
        expected={"ok": 1.0},
        msg="w=1.9 should be truncated to 1 and accepted",
    ),
    CommandTestCase(
        "wc_w_neg_double_truncated",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": -0.9},
        },
        expected={"ok": 1.0},
        msg="w=-0.9 should be truncated to 0 and accepted",
    ),
    CommandTestCase(
        "wc_w_int64_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": INT64_ZERO},
        },
        expected={"ok": 1.0},
        msg="w=Int64(0) should be accepted",
    ),
    CommandTestCase(
        "wc_w_int64_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": Int64(1)},
        },
        expected={"ok": 1.0},
        msg="w=Int64(1) should be accepted",
    ),
    CommandTestCase(
        "wc_w_decimal128_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_ZERO},
        },
        expected={"ok": 1.0},
        msg="w=Decimal128('0') should be accepted",
    ),
    CommandTestCase(
        "wc_w_decimal128_one",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": Decimal128("1")},
        },
        expected={"ok": 1.0},
        msg="w=Decimal128('1') should be accepted",
    ),
    CommandTestCase(
        "wc_w_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DOUBLE_NEGATIVE_ZERO},
        },
        expected={"ok": 1.0},
        msg="w=-0.0 should coerce to 0 and be accepted",
    ),
    CommandTestCase(
        "wc_w_decimal128_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": DECIMAL128_NEGATIVE_ZERO},
        },
        expected={"ok": 1.0},
        msg="w=Decimal128('-0') should coerce to 0 and be accepted",
    ),
]

# Property [writeConcern Sub-Field - w Null]: w=null coerces to an
# empty string, which is rejected as a non-majority write mode.
RENAME_WC_W_NULL_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": None},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=null should coerce to empty string and be rejected",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
]

# Property [writeConcern Sub-Field - w String]: only "majority" is
# accepted on standalone; other strings (case-sensitive, no trimming)
# produce a bad-value error.
RENAME_WC_W_STRING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_string_empty",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w='' (empty string) should be rejected on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_string_case_sensitive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": "Majority"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w='Majority' (wrong case) should be rejected on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_string_leading_space",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": " majority"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w=' majority' (leading space) should be rejected on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_string_other",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": "other"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="w='other' should be rejected on standalone",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
]

# Property [writeConcern Sub-Field - w String Success]: w="majority"
# is accepted on standalone.
RENAME_WC_W_STRING_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": "majority"},
        },
        expected={"ok": 1.0},
        msg="w='majority' should be accepted",
    ),
]

# Property [writeConcern Sub-Field - w Object (Tag Sets)]: w accepts
# an object where all values must be numeric; keys have no restrictions.
RENAME_WC_W_OBJECT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_object_empty",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w={} (empty object) should be rejected",
    ),
    CommandTestCase(
        "wc_w_object_string_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"tag": "value"}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w={tag:'value'} (string value) should be rejected",
    ),
    CommandTestCase(
        "wc_w_object_bool_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"tag": True}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w={tag:true} (bool value) should be rejected",
    ),
    CommandTestCase(
        "wc_w_object_null_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"tag": None}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w={tag:null} (null value) should be rejected",
    ),
    CommandTestCase(
        "wc_w_object_array_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"tag": [1]}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w={tag:[1]} (array value) should be rejected",
    ),
    CommandTestCase(
        "wc_w_object_nested_doc",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"tag": {"nested": 1}}},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="w={tag:{nested:1}} (nested doc value) should be rejected",
    ),
]

# Property [writeConcern Sub-Field - w Object Success]: w as an object
# with numeric values is accepted regardless of key format.
RENAME_WC_W_OBJECT_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_w_object_number_value",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"tag": 1}},
        },
        expected={"ok": 1.0},
        msg="w={tag:1} (number value) should be accepted",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_object_dollar_key",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"$tag": 1}},
        },
        expected={"ok": 1.0},
        msg="w={'$tag':1} (dollar-prefixed key) should be accepted",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_w_object_empty_key",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"w": {"": 1}},
        },
        expected={"ok": 1.0},
        msg="w={'':1} (empty-string key) should be accepted",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
]

RENAME_WC_W_TESTS: list[CommandTestCase] = (
    RENAME_WC_W_TYPE_ERROR_TESTS
    + RENAME_WC_W_VALUE_ERROR_TESTS
    + RENAME_WC_W_VALUE_SUCCESS_TESTS
    + RENAME_WC_W_NULL_ERROR_TESTS
    + RENAME_WC_W_STRING_ERROR_TESTS
    + RENAME_WC_W_STRING_SUCCESS_TESTS
    + RENAME_WC_W_OBJECT_ERROR_TESTS
    + RENAME_WC_W_OBJECT_SUCCESS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_WC_W_TESTS))
def test_renameCollection_wc_w(database_client, collection, register_db_cleanup, test):
    """Test renameCollection writeConcern w sub-field."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
