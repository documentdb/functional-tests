"""Tests for hello command replica set response fields.

Validates required replica set fields, conditional fields, and
behavioral checks when connected to a replica set member.
All tests in this file require a replica set connection.
"""

from __future__ import annotations

from datetime import datetime, timezone

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
from documentdb_tests.framework.property_checks import (
    ContainsElement,
    Eq,
    Gte,
    IsType,
    Lte,
    NonEmptyStr,
)

pytestmark = [pytest.mark.requires(replication=True)]

# Property [Required Replica Set Fields]: hello response includes hosts,
# setName, setVersion, secondary, primary, me, and lastWrite when connected
# to a replica set member.
RS_REQUIRED_FIELD_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "rs_hosts_is_array",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"hosts": IsType("array")},
        msg="hello should return hosts as array on replica set member",
    ),
    ReplicationTestCase(
        "rs_setName",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"setName": NonEmptyStr()},
        msg="hello should return setName as non-empty string",
    ),
    ReplicationTestCase(
        "rs_setVersion",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"setVersion": Gte(1)},
        msg="hello should return setVersion as positive integer",
    ),
    ReplicationTestCase(
        "rs_secondary_is_bool",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"secondary": IsType("bool")},
        msg="hello should return secondary as boolean",
    ),
    ReplicationTestCase(
        "rs_primary",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"primary": NonEmptyStr()},
        msg="hello should return primary as non-empty string",
    ),
    ReplicationTestCase(
        "rs_me",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"me": NonEmptyStr()},
        msg="hello should return me as non-empty string",
    ),
    ReplicationTestCase(
        "rs_lastWrite_opTime",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"lastWrite": {"opTime": IsType("object")}},
        msg="hello should return lastWrite.opTime as object",
    ),
    ReplicationTestCase(
        "rs_lastWrite_lastWriteDate",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"lastWrite": {"lastWriteDate": IsType("date")}},
        msg="hello should return lastWrite.lastWriteDate as date",
    ),
    ReplicationTestCase(
        "rs_lastWrite_majorityOpTime",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"lastWrite": {"majorityOpTime": IsType("object")}},
        msg="hello should return lastWrite.majorityOpTime as object",
    ),
    ReplicationTestCase(
        "rs_lastWrite_majorityWriteDate",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"lastWrite": {"majorityWriteDate": IsType("date")}},
        msg="hello should return lastWrite.majorityWriteDate as date",
    ),
    ReplicationTestCase(
        "rs_electionId_on_primary",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"electionId": IsType("objectId")},
        msg="hello should return electionId as ObjectId on primary",
    ),
]

# Property [Primary Node Invariants]: on a primary, isWritablePrimary is true,
# secondary is false, primary equals me, and hosts contains both.
RS_PRIMARY_INVARIANT_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "rs_primary_isWritablePrimary_and_not_secondary",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected={"isWritablePrimary": Eq(True), "secondary": Eq(False)},
        msg="hello should return isWritablePrimary=true and secondary=false on primary",
    ),
    ReplicationTestCase(
        "rs_primary_equals_me",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected=lambda ctx, result: {"primary": Eq(result.get("me", "MISSING"))},
        msg="hello should return primary equal to me on primary node",
    ),
    ReplicationTestCase(
        "rs_hosts_contains_primary",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected=lambda ctx, result: {"hosts": ContainsElement(result.get("primary", "MISSING"))},
        msg="hello should return hosts array containing the primary",
    ),
    ReplicationTestCase(
        "rs_me_in_hosts",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected=lambda ctx, result: {"hosts": ContainsElement(result.get("me", "MISSING"))},
        msg="hello should return hosts array containing me",
    ),
]

# Property [lastWrite Date Ordering]: lastWrite dates have expected ordering.
RS_LASTWRITE_DATE_TESTS: list[ReplicationTestCase] = [
    ReplicationTestCase(
        "rs_lastWriteDate_not_future",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected=lambda ctx, result: {
            "lastWrite": {"lastWriteDate": Lte(datetime.now(tz=timezone.utc))},
        },
        msg="hello lastWrite.lastWriteDate should be <= current time",
    ),
    ReplicationTestCase(
        "rs_majorityWriteDate_lte_lastWriteDate",
        command=lambda ctx: {"hello": 1},
        use_admin=False,
        expected=lambda ctx, result: {
            "lastWrite": {
                "majorityWriteDate": Lte(result["lastWrite"]["lastWriteDate"]),
            },
        },
        msg="hello majorityWriteDate should be <= lastWriteDate",
    ),
]

HELLO_RS_ALL_TESTS: list[ReplicationTestCase] = (
    RS_REQUIRED_FIELD_TESTS + RS_PRIMARY_INVARIANT_TESTS + RS_LASTWRITE_DATE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(HELLO_RS_ALL_TESTS))
def test_hello_replica_set(collection, test):
    """Test hello replica set response fields."""
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx, result),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
