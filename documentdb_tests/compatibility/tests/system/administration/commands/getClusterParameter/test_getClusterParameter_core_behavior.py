"""Tests for getClusterParameter core retrieval behavior.

Covers the three accepted argument forms, default values on a fresh
deployment, idempotency of repeated calls, and that requesting one name
does not return unrelated parameters.

Categories: #4 (core behavior + deployment variants), #7, #14
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Eq, Len

pytestmark = pytest.mark.admin

_VALID_PARAM = "changeStreamOptions"
_VALID_PARAM_2 = "changeStreams"


# ---------------------------------------------------------------------------
# §4 / §7  Core behavior — three argument forms
# ---------------------------------------------------------------------------


def test_getClusterParameter_single_name_succeeds(collection):
    """Test single valid name returns ok:1 with clusterParameters length 1."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(1)},
        msg="Single valid name should return ok:1 with one parameter",
        raw_res=True,
    )


def test_getClusterParameter_wildcard_returns_all_params(collection):
    """Test '*' returns ok:1."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Wildcard should return ok:1")


def test_getClusterParameter_wildcard_includes_known_param(collection):
    """Test '*' result includes the known parameter 'changeStreamOptions'."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    ids = [p["_id"] for p in result["clusterParameters"]]
    assertProperties(
        {"found": 1 if _VALID_PARAM in ids else 0},
        {"found": Eq(1)},
        msg=f"Wildcard result should include '{_VALID_PARAM}'",
        raw_res=True,
    )


def test_getClusterParameter_array_two_names_succeeds(collection):
    """Test array of two valid names returns ok:1 with clusterParameters length 2."""
    result = execute_admin_command(
        collection, {"getClusterParameter": [_VALID_PARAM, _VALID_PARAM_2]}
    )
    assertProperties(
        result,
        {"ok": Eq(1.0), "clusterParameters": Len(2)},
        msg="Array of two names should return ok:1 with two parameters",
        raw_res=True,
    )


# ---------------------------------------------------------------------------
# §4 / §7  Defaults available on any deployment
# ---------------------------------------------------------------------------


def test_getClusterParameter_wildcard_returns_defaults(collection):
    """Test '*' returns defaults without error on any deployment."""
    result = execute_admin_command(collection, {"getClusterParameter": "*"})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Defaults should be returned without prior set")


# ---------------------------------------------------------------------------
# §4 / §7  Requested name isolation
# ---------------------------------------------------------------------------


def test_getClusterParameter_single_name_id_equals_request(collection):
    """Test requesting one name returns element with _id equal to requested name."""
    result = execute_admin_command(collection, {"getClusterParameter": _VALID_PARAM})
    assertProperties(
        result,
        {"clusterParameters.0._id": Eq(_VALID_PARAM)},
        msg=f"_id should equal the requested name '{_VALID_PARAM}'",
        raw_res=True,
    )


# ---------------------------------------------------------------------------
# §14  Idempotency — repeated calls produce stable structure
# ---------------------------------------------------------------------------


def test_getClusterParameter_wildcard_idempotent(collection):
    """Test repeated '*' calls return the same parameter count."""
    r1 = execute_admin_command(collection, {"getClusterParameter": "*"})
    r2 = execute_admin_command(collection, {"getClusterParameter": "*"})
    count1 = len(r1["clusterParameters"])
    assertProperties(
        {"count": len(r2["clusterParameters"])},
        {"count": Eq(count1)},
        msg="Repeated wildcard calls should return stable parameter count",
        raw_res=True,
    )
