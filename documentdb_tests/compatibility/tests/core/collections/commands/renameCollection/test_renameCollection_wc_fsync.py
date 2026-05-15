"""Tests for renameCollection writeConcern fsync sub-field."""

from datetime import datetime, timezone

import pytest
from bson import Code, MaxKey, MinKey, ObjectId, Regex, Timestamp
from bson.binary import Binary

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DECIMAL128_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    DOUBLE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT64_ZERO,
)

# Property [writeConcern Sub-Field - fsync Type]: the fsync field
# accepts the same types as j (bool, null, int32, Int64, double,
# Decimal128); all other BSON types produce a type mismatch error.
RENAME_WC_FSYNC_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_fsync_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"fsync as {tid} should be rejected",
    )
    for tid, val in [
        ("string", "true"),
        ("array", [True]),
        ("object", {"f": True}),
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

# Property [writeConcern Sub-Field - fsync and j Conflict]: when both
# fsync and j are truthy, the command fails with a parse error.
RENAME_WC_FSYNC_J_CONFLICT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_fsync_{tid}_j_true",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": v, "j": True},
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg=f"fsync={tid} (truthy) and j=True should conflict",
    )
    for tid, val in [
        ("true", True),
        ("int1", 1),
        ("nan", FLOAT_NAN),
        ("neg_nan", FLOAT_NEGATIVE_NAN),
        ("neg1", -1),
        ("inf", FLOAT_INFINITY),
        ("neg_inf", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
        ("decimal128_inf", DECIMAL128_INFINITY),
        ("decimal128_neg_inf", DECIMAL128_NEGATIVE_INFINITY),
    ]
]

# Property [writeConcern Sub-Field - fsync Truthiness]: numeric zero
# representations, null, and False are falsy; all other accepted
# values are truthy.
RENAME_WC_FSYNC_TRUTHINESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_fsync_{tid}_j_true",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": v, "j": True},
        },
        expected={"ok": 1.0},
        msg=f"fsync={tid} (falsy) should not conflict with j=True",
    )
    for tid, val in [
        ("false", False),
        ("int0", 0),
        ("double_zero", DOUBLE_ZERO),
        ("neg_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_zero", DECIMAL128_ZERO),
        ("decimal128_neg_zero", DECIMAL128_NEGATIVE_ZERO),
        ("int64_zero", INT64_ZERO),
        ("null", None),
    ]
]

# Property [writeConcern Sub-Field - fsync Alone]: fsync accepts
# numeric and boolean values when used without j.
RENAME_WC_FSYNC_ALONE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_fsync_true_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": True},
        },
        expected={"ok": 1.0},
        msg="fsync=True alone (without j) should succeed",
    ),
    CommandTestCase(
        "wc_fsync_false_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": False},
        },
        expected={"ok": 1.0},
        msg="fsync=False alone (without j) should succeed",
    ),
    CommandTestCase(
        "wc_fsync_nan_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": FLOAT_NAN},
        },
        expected={"ok": 1.0},
        msg="fsync=NaN alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_neg_nan_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": FLOAT_NEGATIVE_NAN},
        },
        expected={"ok": 1.0},
        msg="fsync=negative NaN alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_infinity_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": FLOAT_INFINITY},
        },
        expected={"ok": 1.0},
        msg="fsync=Infinity alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_neg_infinity_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": FLOAT_NEGATIVE_INFINITY},
        },
        expected={"ok": 1.0},
        msg="fsync=-Infinity alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_decimal128_nan_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": DECIMAL128_NAN},
        },
        expected={"ok": 1.0},
        msg="fsync=Decimal128('NaN') alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_decimal128_neg_nan_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": DECIMAL128_NEGATIVE_NAN},
        },
        expected={"ok": 1.0},
        msg="fsync=Decimal128 negative NaN alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_decimal128_infinity_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": DECIMAL128_INFINITY},
        },
        expected={"ok": 1.0},
        msg="fsync=Decimal128('Infinity') alone should succeed",
    ),
    CommandTestCase(
        "wc_fsync_decimal128_neg_infinity_alone",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": DECIMAL128_NEGATIVE_INFINITY},
        },
        expected={"ok": 1.0},
        msg="fsync=Decimal128('-Infinity') alone should succeed",
    ),
]

# Property [writeConcern Sub-Field - fsync and j Combinations]: when
# fsync is not truthy alongside j=True, the combination succeeds.
RENAME_WC_FSYNC_J_COMBINATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "wc_fsync_true_j_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": True, "j": False},
        },
        expected={"ok": 1.0},
        msg="fsync=True with j=False should succeed",
    ),
    CommandTestCase(
        "wc_fsync_false_j_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"fsync": False, "j": False},
        },
        expected={"ok": 1.0},
        msg="fsync=False with j=False should succeed",
    ),
]

RENAME_WC_FSYNC_TESTS: list[CommandTestCase] = (
    RENAME_WC_FSYNC_TYPE_ERROR_TESTS
    + RENAME_WC_FSYNC_J_CONFLICT_TESTS
    + RENAME_WC_FSYNC_TRUTHINESS_TESTS
    + RENAME_WC_FSYNC_ALONE_SUCCESS_TESTS
    + RENAME_WC_FSYNC_J_COMBINATION_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_WC_FSYNC_TESTS))
def test_renameCollection_wc_fsync(database_client, collection, register_db_cleanup, test):
    """Test renameCollection writeConcern fsync sub-field."""
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
