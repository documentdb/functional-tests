"""Tests for getDefaultRWConcern command input acceptance and rejection behavior."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    NOT_SUPPORTED_ON_STANDALONE_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType

# Property [Output Schema and Return Shape]: a successful response always
# returns the full defaults schema, for both an on-disk and an in-memory read.
GETDEFAULTRWCONCERN_OUTPUT_SCHEMA_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "output_schema",
        command={"getDefaultRWConcern": 1},
        expected={
            "ok": Eq(1.0),
            "defaultReadConcern": IsType("object"),
            "defaultWriteConcern": IsType("object"),
            "defaultReadConcernSource": IsType("string"),
            "defaultWriteConcernSource": IsType("string"),
            "localUpdateWallClockTime": IsType("date"),
        },
        msg="getDefaultRWConcern should always return the read/write concern "
        "defaults, their sources, and localUpdateWallClockTime",
    ),
    CommandTestCase(
        "output_schema_in_memory",
        command={"getDefaultRWConcern": 1, "inMemory": True},
        expected={
            "ok": Eq(1.0),
            "inMemory": Eq(True),
            "defaultReadConcern": IsType("object"),
            "defaultWriteConcern": IsType("object"),
            "defaultReadConcernSource": IsType("string"),
            "defaultWriteConcernSource": IsType("string"),
            "localUpdateWallClockTime": IsType("date"),
        },
        msg="getDefaultRWConcern should return the full defaults schema for an "
        "in-memory read and echo inMemory true",
    ),
]


@pytest.mark.requires(cluster_admin=True)
@pytest.mark.parametrize("test", pytest_params(GETDEFAULTRWCONCERN_OUTPUT_SCHEMA_TESTS))
def test_getDefaultRWConcern_output_schema(collection, test):
    """Test getDefaultRWConcern always returns the full defaults schema."""
    result = execute_admin_command(collection, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )


# Property [Topology Errors]: on a standalone node the command is unsupported
# and is rejected.
@pytest.mark.requires(cluster_admin=False)
def test_getDefaultRWConcern_topology_error(collection):
    """Test getDefaultRWConcern is unsupported on standalone nodes."""
    result = execute_admin_command(collection, {"getDefaultRWConcern": 1})
    assertResult(
        result,
        error_code=NOT_SUPPORTED_ON_STANDALONE_ERROR,
        msg="getDefaultRWConcern should be unsupported on a standalone node",
        raw_res=True,
    )


# Property [Default Concern Source Semantics]: setting a default flips the
# corresponding source from implicit to global and surfaces the update
# timestamps. This mutates global state irreversibly (the default write concern
# cannot be unset), so it runs no_parallel.
@pytest.mark.requires(cluster_admin=True)
@pytest.mark.no_parallel
def test_getDefaultRWConcern_source_global_after_set(collection):
    """Test getDefaultRWConcern reports global sources once defaults are set."""
    execute_admin_command(
        collection,
        {
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "defaultWriteConcern": {"w": "majority", "wtimeout": 0},
        },
    )
    result = execute_admin_command(collection, {"getDefaultRWConcern": 1})
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "defaultReadConcernSource": Eq("global"),
            "defaultWriteConcernSource": Eq("global"),
            "updateOpTime": IsType("timestamp"),
            "updateWallClockTime": IsType("date"),
        },
        msg="getDefaultRWConcern should report global sources and present update "
        "timestamps once defaults are set",
        raw_res=True,
    )


# Property [Default Concern Source Semantics]: unsetting the default read concern
# reverts its source to implicit, while the write concern source stays global
# because it cannot be unset. This mutates global state irreversibly, so it runs
# no_parallel.
@pytest.mark.requires(cluster_admin=True)
@pytest.mark.no_parallel
def test_getDefaultRWConcern_read_source_reverts_on_unset(collection):
    """Test getDefaultRWConcern reverts the read source to implicit on unset."""
    execute_admin_command(
        collection,
        {
            "setDefaultRWConcern": 1,
            "defaultReadConcern": {"level": "local"},
            "defaultWriteConcern": {"w": "majority", "wtimeout": 0},
        },
    )
    execute_admin_command(collection, {"setDefaultRWConcern": 1, "defaultReadConcern": {}})
    result = execute_admin_command(collection, {"getDefaultRWConcern": 1})
    assertResult(
        result,
        expected={
            "ok": Eq(1.0),
            "defaultReadConcernSource": Eq("implicit"),
            "defaultWriteConcernSource": Eq("global"),
        },
        msg="getDefaultRWConcern should revert the read concern source to implicit "
        "after unset while the write concern source remains global",
        raw_res=True,
    )
