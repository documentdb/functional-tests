"""Tests for hello command response structure.

Validates common response fields (all instances), topologyVersion
fields, and wire version fields using property checks.
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
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Gte, IsType

# Property [Common Response Fields]: hello response includes all required
# fields with correct types and values.
RESPONSE_COMMON_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "response_isWritablePrimary",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"isWritablePrimary": IsType("bool")},
        msg="hello should return isWritablePrimary as boolean",
    ),
    ReplicationTestCase(
        "response_maxBsonObjectSize",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"maxBsonObjectSize": Eq(16_777_216)},
        msg="hello should return maxBsonObjectSize equal to 16777216",
    ),
    ReplicationTestCase(
        "response_maxMessageSizeBytes",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"maxMessageSizeBytes": Eq(48_000_000)},
        msg="hello should return maxMessageSizeBytes equal to 48000000",
    ),
    ReplicationTestCase(
        "response_maxWriteBatchSize",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"maxWriteBatchSize": Eq(100_000)},
        msg="hello should return maxWriteBatchSize equal to 100000",
    ),
    ReplicationTestCase(
        "response_localTime",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"localTime": IsType("date")},
        msg="hello should return localTime as date",
    ),
    ReplicationTestCase(
        "response_logicalSessionTimeoutMinutes",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"logicalSessionTimeoutMinutes": Gte(1)},
        msg="hello should return logicalSessionTimeoutMinutes as positive integer",
    ),
    ReplicationTestCase(
        "response_connectionId",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"connectionId": Gte(1)},
        msg="hello should return connectionId as positive integer",
    ),
    ReplicationTestCase(
        "response_readOnly",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"readOnly": IsType("bool")},
        msg="hello should return readOnly as boolean",
    ),
    ReplicationTestCase(
        "response_ok",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"ok": Eq(1.0)},
        msg="hello should return ok equal to 1.0",
    ),
]

# Property [topologyVersion]: hello response contains topologyVersion with
# processId (ObjectId) and counter (non-negative int64).
RESPONSE_TOPOLOGY_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "topology_processId",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"topologyVersion": {"processId": IsType("objectId")}},
        msg="hello should return topologyVersion.processId as ObjectId",
    ),
    ReplicationTestCase(
        "topology_counter",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"topologyVersion": {"counter": Gte(0)}},
        msg="hello should return topologyVersion.counter as non-negative",
    ),
]

# Property [Wire Version]: wire version fields indicate protocol compatibility.
RESPONSE_WIRE_VERSION_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "wire_min_non_negative",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"minWireVersion": Gte(0)},
        msg="hello should return minWireVersion >= 0",
    ),
    ReplicationTestCase(
        "wire_max_reasonable",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"maxWireVersion": Gte(21)},
        msg="hello should return maxWireVersion >= 21 for MongoDB 7.0+",
    ),
    ReplicationTestCase(
        "wire_max_gte_min",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected=lambda ctx, result: {
            "maxWireVersion": Gte(result.get("minWireVersion", 0)),
        },
        msg="hello should return maxWireVersion >= minWireVersion",
    ),
]

HELLO_RESPONSE_ALL_TESTS: list[ReplicationTestCase] = (
    RESPONSE_COMMON_TESTS + RESPONSE_TOPOLOGY_TESTS + RESPONSE_WIRE_VERSION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(HELLO_RESPONSE_ALL_TESTS))
def test_hello_response_structure(collection, test):
    """Test hello response field types and values."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx, result),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [topologyVersion Stability]: processId remains stable across calls.
def test_hello_response_topologyVersion_processId_stable(collection):
    """Test hello topologyVersion.processId is stable across calls."""
    r1 = execute_command(collection, {"hello": 1})
    r2 = execute_command(collection, {"hello": 1})
    assertResult(
        r2,
        expected={"topologyVersion": {"processId": Eq(r1["topologyVersion"]["processId"])}},
        msg="hello should return stable topologyVersion.processId across calls",
        raw_res=True,
    )
