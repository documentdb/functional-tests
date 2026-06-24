"""Tests for hello command consistency, idempotency, legacy compatibility,
execution context, standalone behavior, and read-only behavior.

Validates that hello returns consistent results, works across databases,
is compatible with legacy isMaster, and does not modify state.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
)
from documentdb_tests.compatibility.tests.system.replication.utils.replication_test_case import (  # noqa: E501
    ReplicationTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte, NotExists

# Property [Execution Context]: hello succeeds on any database context.
HELLO_CONTEXT_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "context_admin_database",
        command=lambda ctx: {"hello": 1},
        use_admin=True,
        expected={"ok": Eq(1.0)},
        msg="hello should succeed on admin database",
    ),
    ReplicationTestCase(
        "context_user_database",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should succeed on non-admin database",
    ),
]

# Property [Primary/Standalone Defaults]: on a standalone or primary node,
# isWritablePrimary is true and readOnly is false.
HELLO_STANDALONE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "primary_isWritablePrimary_true",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"isWritablePrimary": Eq(True)},
        msg="hello should return isWritablePrimary true on standalone/primary",
    ),
    ReplicationTestCase(
        "primary_readOnly_false",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"readOnly": Eq(False)},
        msg="hello should return readOnly false on standalone/primary",
    ),
]

# Property [Legacy isMaster Compatibility]: isMaster and ismaster still work
# and return compatible output.
HELLO_LEGACY_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "legacy_isMaster_succeeds",
        command=lambda ctx: {"isMaster": 1},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should support isMaster alias with ok: 1.0",
    ),
    ReplicationTestCase(
        "legacy_ismaster_lowercase_succeeds",
        command=lambda ctx: {"ismaster": 1},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should support ismaster (lowercase) alias with ok: 1.0",
    ),
]

HELLO_CONSISTENCY_ALL_TESTS: list[ReplicationTestCase] = (
    HELLO_CONTEXT_TESTS + HELLO_STANDALONE_TESTS + HELLO_LEGACY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(HELLO_CONSISTENCY_ALL_TESTS))
def test_hello_consistency(collection, test):
    """Test hello command consistency, context, and legacy compatibility."""
    ctx = CommandContext.from_collection(collection)
    if test.use_admin:
        result = execute_admin_command(collection, test.build_command(ctx))
    else:
        result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx, result),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Static Field Consistency]: static fields are identical across
# consecutive hello calls.
def test_hello_consistency_static_fields(collection):
    """Test hello returns identical static fields across consecutive calls."""
    r1 = execute_command(collection, {"hello": 1})
    r2 = execute_command(collection, {"hello": 1})
    assertResult(
        r2,
        expected={
            "maxBsonObjectSize": Eq(r1["maxBsonObjectSize"]),
            "maxMessageSizeBytes": Eq(r1["maxMessageSizeBytes"]),
            "maxWriteBatchSize": Eq(r1["maxWriteBatchSize"]),
            "minWireVersion": Eq(r1["minWireVersion"]),
            "maxWireVersion": Eq(r1["maxWireVersion"]),
        },
        msg="hello should return identical static fields across consecutive calls",
        raw_res=True,
    )


# Property [Admin and User DB Consistency]: static fields match between admin
# and user databases.
def test_hello_admin_and_user_db_static_fields_match(collection):
    """Test hello static fields match between admin and user databases."""
    r_admin = execute_admin_command(collection, {"hello": 1})
    r_user = execute_command(collection, {"hello": 1})
    assertResult(
        r_user,
        expected={
            "maxBsonObjectSize": Eq(r_admin["maxBsonObjectSize"]),
            "maxMessageSizeBytes": Eq(r_admin["maxMessageSizeBytes"]),
            "maxWriteBatchSize": Eq(r_admin["maxWriteBatchSize"]),
            "minWireVersion": Eq(r_admin["minWireVersion"]),
            "maxWireVersion": Eq(r_admin["maxWireVersion"]),
        },
        msg="hello should return matching static fields on admin and user db",
        raw_res=True,
    )


# Property [localTime Monotonicity]: localTime is non-decreasing across calls.
def test_hello_localTime_monotonic(collection):
    """Test hello localTime is monotonically non-decreasing."""
    r1 = execute_command(collection, {"hello": 1})
    r2 = execute_command(collection, {"hello": 1})
    assertResult(
        r2,
        expected={"localTime": Gte(r1["localTime"])},
        msg="hello should return non-decreasing localTime across calls",
        raw_res=True,
    )


# Property [connectionId Stability]: connectionId is stable on the same connection.
def test_hello_connectionId_stable(collection):
    """Test hello connectionId remains stable on same connection."""
    r1 = execute_command(collection, {"hello": 1})
    r2 = execute_command(collection, {"hello": 1})
    assertResult(
        r2,
        expected={"connectionId": Eq(r1["connectionId"])},
        msg="hello should return stable connectionId on same connection",
        raw_res=True,
    )


# Property [Legacy Field Compatibility]: hello and isMaster return the same
# values for common fields.
def test_hello_legacy_isMaster_fields_match(collection):
    """Test hello and isMaster return same values for common fields."""
    r_hello = execute_command(collection, {"hello": 1})
    r_ismaster = execute_command(collection, {"isMaster": 1})
    assertResult(
        r_ismaster,
        expected={
            "maxBsonObjectSize": Eq(r_hello["maxBsonObjectSize"]),
            "maxMessageSizeBytes": Eq(r_hello["maxMessageSizeBytes"]),
            "maxWriteBatchSize": Eq(r_hello["maxWriteBatchSize"]),
            "minWireVersion": Eq(r_hello["minWireVersion"]),
            "maxWireVersion": Eq(r_hello["maxWireVersion"]),
            "readOnly": Eq(r_hello["readOnly"]),
            "connectionId": Eq(r_hello["connectionId"]),
            "logicalSessionTimeoutMinutes": Eq(r_hello["logicalSessionTimeoutMinutes"]),
        },
        msg="hello should return matching fields with isMaster alias",
        raw_res=True,
    )


# Property [Read-Only Behavior]: hello does not modify server state.
def test_hello_read_only_behavior(collection):
    """Test hello static fields unchanged after inserting a document."""
    r_before = execute_command(collection, {"hello": 1})
    collection.insert_one({"_id": 1, "data": "test"})
    r_after = execute_command(collection, {"hello": 1})
    assertResult(
        r_after,
        expected={
            "maxBsonObjectSize": Eq(r_before["maxBsonObjectSize"]),
            "maxMessageSizeBytes": Eq(r_before["maxMessageSizeBytes"]),
            "maxWriteBatchSize": Eq(r_before["maxWriteBatchSize"]),
            "minWireVersion": Eq(r_before["minWireVersion"]),
            "maxWireVersion": Eq(r_before["maxWireVersion"]),
        },
        msg="hello should return unchanged static fields after insert",
        raw_res=True,
    )


# Property [Standalone RS Fields Absent]: on standalone, replica set fields
# are absent from the hello response.
@pytest.mark.requires(change_streams=False)
def test_hello_standalone_rs_fields_absent(collection):
    """Test hello does not return replica set fields on standalone."""
    result = execute_command(collection, {"hello": 1})
    assertResult(
        result,
        expected={
            "hosts": NotExists(),
            "setName": NotExists(),
            "setVersion": NotExists(),
            "secondary": NotExists(),
            "primary": NotExists(),
            "me": NotExists(),
            "electionId": NotExists(),
            "lastWrite": NotExists(),
            "passives": NotExists(),
            "arbiters": NotExists(),
        },
        msg="hello should not return replica set fields on standalone",
        raw_res=True,
    )
