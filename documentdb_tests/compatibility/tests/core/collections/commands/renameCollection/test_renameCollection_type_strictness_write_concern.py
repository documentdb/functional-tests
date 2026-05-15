"""Tests for renameCollection type strictness of writeConcern field."""

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

# Property [Type Strictness - writeConcern Field]: only null and
# object (document) types are accepted for writeConcern; all other
# BSON types produce a type mismatch error.
RENAME_TYPE_STRICTNESS_WRITE_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_wc_{tid}",
        docs=[{"_id": 1}],
        command=lambda ctx, v=val: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_dest",
            "writeConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"writeConcern as {tid} should produce TypeMismatch",
    )
    for tid, val in [
        ("string", "majority"),
        ("int32", 1),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [{"w": 1}]),
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


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_TYPE_STRICTNESS_WRITE_CONCERN_TESTS))
def test_renameCollection_type_strictness_write_concern(
    database_client, collection, register_db_cleanup, test
):
    """Test renameCollection type strictness of writeConcern field."""
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
