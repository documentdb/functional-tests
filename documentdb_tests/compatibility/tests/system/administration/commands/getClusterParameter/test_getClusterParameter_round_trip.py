"""Tests for getClusterParameter cross-command interactions.

Round-trip (#12): a value written with setClusterParameter is read back by
getClusterParameter, and a never-set parameter returns its default without
error.

Differential (#16): getClusterParameter and getParameter occupy distinct
namespaces (a cluster parameter is not retrievable via getParameter and a
server parameter is not a cluster parameter), and getDefaultRWConcern is a
separate facility (defaultRWConcern is not a cluster parameter).

Marked no_parallel because the round-trip tests mutate a cluster parameter;
each restores the original value in a finally block.

DEFERRED (require a sharded cluster, not this single target):
- After a set, mongos durable value and mongod cached value converge
  eventually (#12).
- A settable-but-internal parameter's presence under '*' vs setClusterParameter
  acceptance (#12) — needs an internal parameter inventory.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertProperties
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, IsType

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


def test_getClusterParameter_set_then_get_reflects_value(collection):
    """Test a value written by setClusterParameter is read back (read-after-write)."""
    get0 = execute_admin_command(collection, {"getClusterParameter": "defaultMaxTimeMS"})
    original = int(get0["clusterParameters"][0]["readOperations"])
    new_value = 4242 if original != 4242 else 1234
    try:
        execute_admin_command(
            collection,
            {"setClusterParameter": {"defaultMaxTimeMS": {"readOperations": new_value}}},
        )
        got = execute_admin_command(collection, {"getClusterParameter": "defaultMaxTimeMS"})
        read_back = int(got["clusterParameters"][0]["readOperations"])
        assertProperties(
            {"read_back": read_back},
            {"read_back": Eq(new_value)},
            msg="getClusterParameter should read back the value set by setClusterParameter.",
            raw_res=True,
        )
    finally:
        execute_admin_command(
            collection,
            {"setClusterParameter": {"defaultMaxTimeMS": {"readOperations": original}}},
        )


def test_getClusterParameter_never_set_returns_default(collection):
    """Test a parameter that was not explicitly set still returns a default value."""
    result = execute_admin_command(collection, {"getClusterParameter": "defaultMaxTimeMS"})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters.0.readOperations": IsType("long")},
        msg="A never-set parameter should return its default without error.",
        raw_res=True,
    )


def test_getClusterParameter_cluster_param_not_retrievable_via_getParameter(collection):
    """Test a cluster parameter name is not retrievable through getParameter."""
    name = execute_admin_command(collection, {"getClusterParameter": "*"})["clusterParameters"][0][
        "_id"
    ]
    result = execute_admin_command(collection, {"getParameter": 1, name: 1})
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg=f"Cluster parameter '{name}' should not be retrievable via getParameter.",
    )


def test_getClusterParameter_server_parameter_not_a_cluster_parameter(collection):
    """Test a server parameter (logLevel) is not present in cluster parameters."""
    names = [
        p["_id"]
        for p in execute_admin_command(collection, {"getClusterParameter": "*"})[
            "clusterParameters"
        ]
    ]
    assertProperties(
        {"has_logLevel": "logLevel" in names},
        {"has_logLevel": Eq(False)},
        msg="Server parameter 'logLevel' should not be a cluster parameter.",
        raw_res=True,
    )


def test_getClusterParameter_defaultRWConcern_not_a_cluster_parameter(collection):
    """Test defaultRWConcern is not a cluster parameter (distinct from getDefaultRWConcern)."""
    names = [
        p["_id"]
        for p in execute_admin_command(collection, {"getClusterParameter": "*"})[
            "clusterParameters"
        ]
    ]
    assertProperties(
        {"has_defaultRWConcern": "defaultRWConcern" in names},
        {"has_defaultRWConcern": Eq(False)},
        msg="defaultRWConcern should not appear among cluster parameters.",
        raw_res=True,
    )
