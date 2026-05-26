"""Tests for connPoolStats command core behavior and response structure."""

import pytest

from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Gte, IsType

pytestmark = pytest.mark.admin


def test_connPoolStats_returns_ok(collection):
    """Test connPoolStats returns ok: 1."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should return ok: 1")


def test_connPoolStats_returns_totalInUse(collection):
    """Test connPoolStats returns totalInUse as a non-negative number."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result, expected={"totalInUse": Gte(0)}, raw_res=True, msg="totalInUse should be >= 0"
    )


def test_connPoolStats_returns_totalAvailable(collection):
    """Test connPoolStats returns totalAvailable as a non-negative number."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result,
        expected={"totalAvailable": Gte(0)},
        raw_res=True,
        msg="totalAvailable should be >= 0",
    )


def test_connPoolStats_returns_totalCreated(collection):
    """Test connPoolStats returns totalCreated as a non-negative number."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result, expected={"totalCreated": Gte(0)}, raw_res=True, msg="totalCreated should be >= 0"
    )


def test_connPoolStats_returns_totalRefreshing(collection):
    """Test connPoolStats returns totalRefreshing as a non-negative number."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result,
        expected={"totalRefreshing": Gte(0)},
        raw_res=True,
        msg="totalRefreshing should be >= 0",
    )


def test_connPoolStats_returns_pools(collection):
    """Test connPoolStats returns pools as a document."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result, expected={"pools": IsType("object")}, raw_res=True, msg="pools should be a document"
    )


def test_connPoolStats_returns_hosts(collection):
    """Test connPoolStats returns hosts as a document."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result, expected={"hosts": IsType("object")}, raw_res=True, msg="hosts should be a document"
    )
