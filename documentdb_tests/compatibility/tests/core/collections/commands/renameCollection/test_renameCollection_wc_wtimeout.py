"""Tests for renameCollection writeConcern wtimeout sub-field."""

import pytest
from bson import Decimal128, Int64

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
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_OVERFLOW,
)

# Property [writeConcern Sub-Field - wtimeout]: values exceeding
# INT32_MAX or positive infinity produce a parse error.
RENAME_WC_WTIMEOUT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_wtimeout_over_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": INT32_OVERFLOW},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout > INT32_MAX should be rejected",
    ),
    CommandTestCase(
        "wc_wtimeout_int64_over_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": Int64(INT32_OVERFLOW)},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout as Int64 > INT32_MAX should be rejected",
    ),
    CommandTestCase(
        "wc_wtimeout_pos_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": FLOAT_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout=+Infinity should be rejected",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_pos_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": DECIMAL128_INFINITY},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="wtimeout=Decimal128('Infinity') should be rejected",
    ),
]

# Property [writeConcern Sub-Field - wtimeout Success]: any value
# that fits within int32 range (including negative) or is non-numeric
# is accepted without error.
RENAME_WC_WTIMEOUT_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_wtimeout_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": 0},
        },
        expected={"ok": 1.0},
        msg="wtimeout=0 should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_positive",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": 1000},
        },
        expected={"ok": 1.0},
        msg="wtimeout=1000 should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_int32_max",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": INT32_OVERFLOW - 1},
        },
        expected={"ok": 1.0},
        msg="wtimeout=INT32_MAX should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_negative",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": -1},
        },
        expected={"ok": 1.0},
        msg="wtimeout=-1 (negative) should be accepted",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_wtimeout_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": FLOAT_NEGATIVE_INFINITY},
        },
        expected={"ok": 1.0},
        msg="wtimeout=-Infinity should be accepted",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_wtimeout_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": FLOAT_NAN},
        },
        expected={"ok": 1.0},
        msg="wtimeout=NaN should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": "1000"},
        },
        expected={"ok": 1.0},
        msg="wtimeout as string should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": True},
        },
        expected={"ok": 1.0},
        msg="wtimeout as bool should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": None},
        },
        expected={"ok": 1.0},
        msg="wtimeout=null should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": [1000]},
        },
        expected={"ok": 1.0},
        msg="wtimeout as array should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": {"ms": 1000}},
        },
        expected={"ok": 1.0},
        msg="wtimeout as object should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": Int64(1000)},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Int64 should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": Decimal128("1000")},
        },
        expected={"ok": 1.0},
        msg="wtimeout as Decimal128 should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": FLOAT_NEGATIVE_NAN},
        },
        expected={"ok": 1.0},
        msg="wtimeout=negative NaN should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": DECIMAL128_NAN},
        },
        expected={"ok": 1.0},
        msg="wtimeout=Decimal128('NaN') should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_neg_nan",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_NAN},
        },
        expected={"ok": 1.0},
        msg="wtimeout=Decimal128 negative NaN should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_neg_infinity",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_INFINITY},
        },
        expected={"ok": 1.0},
        msg="wtimeout=Decimal128('-Infinity') should be accepted",
        marks=(pytest.mark.requires(quorum_write_concern=False),),
    ),
    CommandTestCase(
        "wc_wtimeout_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": DOUBLE_NEGATIVE_ZERO},
        },
        expected={"ok": 1.0},
        msg="wtimeout=-0.0 should be accepted",
    ),
    CommandTestCase(
        "wc_wtimeout_decimal128_neg_zero",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"wtimeout": DECIMAL128_NEGATIVE_ZERO},
        },
        expected={"ok": 1.0},
        msg="wtimeout=Decimal128('-0') should be accepted",
    ),
]

RENAME_WC_WTIMEOUT_TESTS: list[CommandTestCase] = (
    RENAME_WC_WTIMEOUT_ERROR_TESTS + RENAME_WC_WTIMEOUT_SUCCESS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_WC_WTIMEOUT_TESTS))
def test_renameCollection_wc_wtimeout(database_client, collection, register_db_cleanup, test):
    """Test renameCollection writeConcern wtimeout sub-field."""
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
