"""Tests for getClusterParameter round-trip and differential behavior.

Verifies read-after-write consistency with setClusterParameter, that
never-set parameters return their defaults, and that getClusterParameter
and getParameter operate on distinct namespaces.

Categories: #12, #16
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
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


# ---------------------------------------------------------------------------
# §12  Round-trip with setClusterParameter
# ---------------------------------------------------------------------------


def test_getClusterParameter_reads_value_after_set(collection):
    """Test getClusterParameter returns the value set by setClusterParameter."""
    original = _get_expire_after_seconds(collection)
    # Server stores expireAfterSeconds as Int64; use same type for expected comparison.
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


# ---------------------------------------------------------------------------
# §16  Differential: getClusterParameter vs getParameter have distinct namespaces
# ---------------------------------------------------------------------------


def test_getClusterParameter_name_not_retrievable_via_getParameter(collection):
    """Test a cluster parameter name cannot be retrieved via getParameter."""
    result = execute_admin_command(collection, {"getParameter": _PARAM})
    assertFailureCode(
        result,
        INVALID_OPTIONS_ERROR,
        msg="Cluster parameter name should not be retrievable via getParameter",
    )
