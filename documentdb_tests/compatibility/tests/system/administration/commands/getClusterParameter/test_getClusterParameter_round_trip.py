"""Tests for getClusterParameter round-trip and differential behavior.

Verifies read-after-write consistency with setClusterParameter, that
never-set parameters return their defaults, and that getClusterParameter
and getParameter operate on distinct namespaces.

Categories: #12, #16
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]

_PARAM = "changeStreamOptions"
_NESTED_KEY = "preAndPostImages"
_VALUE_KEY = "expireAfterSeconds"


def _get_expire_after_seconds(collection):
    """Read the current expireAfterSeconds value from changeStreamOptions."""
    r = execute_admin_command(collection, {"getClusterParameter": _PARAM})
    assertSuccessPartial(r, {"ok": 1.0}, msg="getClusterParameter should succeed in setup")
    return r["clusterParameters"][0][_NESTED_KEY][_VALUE_KEY]


def _set_expire_after_seconds(collection, value):
    """Set expireAfterSeconds on changeStreamOptions."""
    execute_admin_command(
        collection,
        {"setClusterParameter": {_PARAM: {_NESTED_KEY: {_VALUE_KEY: value}}}},
    )


def test_getClusterParameter_reads_value_after_set(collection):
    """Test getClusterParameter returns the value set by setClusterParameter."""
    original = _get_expire_after_seconds(collection)
    new_value = Int64(7200) if int(original) != 7200 else Int64(3600)
    try:
        _set_expire_after_seconds(collection, int(new_value))
        result = execute_admin_command(collection, {"getClusterParameter": _PARAM})
        assertProperties(
            result,
            {"clusterParameters.0.preAndPostImages.expireAfterSeconds": Eq(new_value)},
            msg=f"expireAfterSeconds should equal {new_value} after set",
            raw_res=True,
        )
    finally:
        _set_expire_after_seconds(collection, int(original))


def test_getClusterParameter_never_set_returns_default(collection):
    """Test a parameter that was never explicitly set returns a default without error."""
    result = execute_admin_command(
        collection, {"getClusterParameter": "internalQueryCutoffForSampleFromRandomCursor"}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="Never-set parameter should return default without error",
        raw_res=True,
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
