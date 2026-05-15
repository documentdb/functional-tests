"""Tests for renameCollection stayTemp option."""

from datetime import datetime, timezone

import pytest
from bson import Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp
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
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [stayTemp Success]: stayTemp accepts bool (true/false) and
# null without error.
RENAME_STAY_TEMP_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "stay_temp_true",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "stayTemp": True,
        },
        expected={"ok": 1.0},
        msg="stayTemp=true should succeed",
    ),
    CommandTestCase(
        "stay_temp_false",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "stayTemp": False,
        },
        expected={"ok": 1.0},
        msg="stayTemp=false should succeed",
    ),
    CommandTestCase(
        "stay_temp_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "stayTemp": None,
        },
        expected={"ok": 1.0},
        msg="stayTemp=null should succeed",
    ),
]

# Property [stayTemp Type Strictness]: stayTemp only accepts bool and
# null; all other BSON types produce a type mismatch error.
RENAME_STAY_TEMP_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"stay_temp_type_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "stayTemp": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"stayTemp as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.0),
        ("decimal128", Decimal128("1")),
        ("string", "true"),
        ("array", [True]),
        ("object", {"value": True}),
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

RENAME_STAY_TEMP_TESTS: list[CommandTestCase] = (
    RENAME_STAY_TEMP_SUCCESS_TESTS + RENAME_STAY_TEMP_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_STAY_TEMP_TESTS))
def test_renameCollection_stay_temp(database_client, collection, register_db_cleanup, test):
    """Test renameCollection stayTemp option."""
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
