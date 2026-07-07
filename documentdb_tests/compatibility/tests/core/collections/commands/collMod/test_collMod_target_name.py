"""Tests for collMod target name (the collMod command value) acceptance."""

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
    INVALID_NAMESPACE_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Target Name Resolution]: a string naming an existing collection or
# view in the current database resolves successfully, and with no option field
# present the command is a no-op success regardless of the target's type.
COLLMOD_TARGET_NAME_RESOLUTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "plain_collection",
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection},
        expected={"ok": Eq(1.0)},
        msg="collMod should resolve a plain collection name as a no-op success",
    ),
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection},
        expected={"ok": Eq(1.0)},
        msg="collMod should resolve a capped collection name as a no-op success",
    ),
    CommandTestCase(
        "view",
        target_collection=ViewCollection(),
        command=lambda ctx: {"collMod": ctx.collection},
        expected={"ok": Eq(1.0)},
        msg="collMod should resolve a view name as a no-op success",
    ),
    CommandTestCase(
        "timeseries_collection",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {"collMod": ctx.collection},
        expected={"ok": Eq(1.0)},
        msg="collMod should resolve a time series collection name as a no-op success",
    ),
    CommandTestCase(
        "clustered_collection",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"collMod": ctx.collection},
        expected={"ok": Eq(1.0)},
        msg="collMod should resolve a clustered collection name as a no-op success",
    ),
]

# Property [Target Name Validation Wiring]: a structurally invalid name and a
# valid name that matches no collection each produce the expected namespace
# error.
COLLMOD_TARGET_NAME_WIRING_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "invalid_namespace_empty_string",
        command={"collMod": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="collMod should reject a structurally invalid namespace as an invalid namespace",
    ),
    CommandTestCase(
        "not_found_nonexistent",
        docs=None,
        command=lambda ctx: {"collMod": ctx.collection},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="collMod should reject a valid name that matches no collection as not found",
    ),
]

# Property [Non-String Target Type Errors]: any non-string type for the target
# (including null and any array shape) produces an invalid namespace error.
COLLMOD_TARGET_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"type_{tid}",
        command={"collMod": val},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"collMod should reject a {tid} target as an invalid namespace type",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(1)),
        ("double", 1.5),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
        ("object", {"x": 1}),
        ("objectid", ObjectId("507f1f77bcf86cd799439011")),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"\x01\x02\x03")),
        ("regex", Regex(".*", "i")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
        ("array_empty", []),
        ("array_string", ["target"]),
    ]
]

COLLMOD_TARGET_NAME_TESTS: list[CommandTestCase] = (
    COLLMOD_TARGET_NAME_RESOLUTION_TESTS
    + COLLMOD_TARGET_NAME_WIRING_ERROR_TESTS
    + COLLMOD_TARGET_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLMOD_TARGET_NAME_TESTS))
def test_collMod_target_name(database_client, collection, test):
    """Test collMod target name resolution, no-op success, and validation wiring."""
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
