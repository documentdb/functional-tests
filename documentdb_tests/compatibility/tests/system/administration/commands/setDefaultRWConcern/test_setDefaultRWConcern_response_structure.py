"""Response structure tests for setDefaultRWConcern."""

import pytest

from documentdb_tests.compatibility.tests.system.administration.utils.admin_test_case import (
    AdminTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel, pytest.mark.requires(cluster_admin=True)]

READ_CONCERN_CMD = {"setDefaultRWConcern": 1, "defaultReadConcern": {"level": "local"}}
WRITE_CONCERN_CMD = {"setDefaultRWConcern": 1, "defaultWriteConcern": {"w": 1}}


RESPONSE_TESTS: list[AdminTestCase] = [
    AdminTestCase(
        "ok_field",
        command=READ_CONCERN_CMD,
        expected={"ok": Eq(1.0)},
        msg="success response contains ok field with value 1",
    ),
    AdminTestCase(
        "echoes_write_concern",
        command=WRITE_CONCERN_CMD,
        expected={"defaultWriteConcern": {"w": Eq(1), "wtimeout": Eq(0)}},
        msg="success response echoes the configured defaultWriteConcern",
    ),
    AdminTestCase(
        "echoes_read_concern",
        command=READ_CONCERN_CMD,
        expected={"defaultReadConcern": {"level": Eq("local")}},
        msg="success response echoes the configured defaultReadConcern",
    ),
    AdminTestCase(
        "update_op_time_is_timestamp",
        command=READ_CONCERN_CMD,
        expected={"updateOpTime": IsType("timestamp")},
        msg="success response contains updateOpTime field of timestamp type",
    ),
    AdminTestCase(
        "update_wall_clock_time_is_date",
        command=READ_CONCERN_CMD,
        expected={"updateWallClockTime": IsType("date")},
        msg="success response contains updateWallClockTime field of date type",
    ),
    AdminTestCase(
        "local_update_wall_clock_time_is_date",
        command=READ_CONCERN_CMD,
        expected={"localUpdateWallClockTime": IsType("date")},
        msg="success response contains localUpdateWallClockTime field of date type",
    ),
    AdminTestCase(
        "write_concern_source_is_string",
        command=READ_CONCERN_CMD,
        expected={"defaultWriteConcernSource": IsType("string")},
        msg="success response contains defaultWriteConcernSource field of string type",
    ),
    AdminTestCase(
        "read_concern_source_is_string",
        command=READ_CONCERN_CMD,
        expected={"defaultReadConcernSource": IsType("string")},
        msg="success response contains defaultReadConcernSource field of string type",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESPONSE_TESTS))
def test_setDefaultRWConcern_response_structure(collection, test):
    """Run a setDefaultRWConcern response-structure case."""
    result = execute_admin_command(collection, test.command)
    assertResult(result, expected=test.expected, msg=test.msg, raw_res=True)
