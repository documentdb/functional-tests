"""Tests for renameCollection writeConcern j sub-field."""

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
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [writeConcern Sub-Field - j Type]: the j field accepts
# bool, null, int32, Int64, double, and Decimal128 (including NaN and
# infinity); all other BSON types produce a type mismatch error.
RENAME_WC_J_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_j_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"j": v},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"j as {tid} should be rejected",
    )
    for tid, val in [
        ("string", "true"),
        ("array", [True]),
        ("object", {"j": True}),
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

# Property [writeConcern Sub-Field - j Type Success]: j accepts bool,
# null, and numeric types including NaN and infinity.
RENAME_WC_J_TYPE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"wc_j_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": {"j": v},
        },
        expected={"ok": 1.0},
        msg=f"j={tid} should be accepted",
    )
    for tid, val in [
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("nan", FLOAT_NAN),
        ("infinity", FLOAT_INFINITY),
        ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
        ("decimal128_nan", DECIMAL128_NAN),
        ("decimal128_infinity", DECIMAL128_INFINITY),
        ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ("neg_nan", FLOAT_NEGATIVE_NAN),
        ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
        ("neg_zero", DOUBLE_NEGATIVE_ZERO),
        ("decimal128_neg_zero", DECIMAL128_NEGATIVE_ZERO),
    ]
]

RENAME_WC_J_TESTS: list[CommandTestCase] = (
    RENAME_WC_J_TYPE_ERROR_TESTS + RENAME_WC_J_TYPE_SUCCESS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_WC_J_TESTS))
def test_renameCollection_wc_j(database_client, collection, register_db_cleanup, test):
    """Test renameCollection writeConcern j sub-field."""
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
