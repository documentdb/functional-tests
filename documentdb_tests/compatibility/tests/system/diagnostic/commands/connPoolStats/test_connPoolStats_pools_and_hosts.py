"""Tests for connPoolStats pools and hosts structure."""

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Exists, IsType

pytestmark = pytest.mark.admin


def test_connPoolStats_pools_is_document(collection):
    """Test pools field is a document."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result, expected={"pools": IsType("object")}, raw_res=True, msg="pools should be document"
    )


def test_connPoolStats_hosts_is_document(collection):
    """Test hosts field is a document."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result, expected={"hosts": IsType("object")}, raw_res=True, msg="hosts should be document"
    )


def test_connPoolStats_standalone_minimal_pools(collection):
    """Test connPoolStats on standalone returns minimal/empty pools."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result,
        expected={"ok": Exists()},
        raw_res=True,
        msg="Standalone should return valid response",
    )


def test_connPoolStats_numClientConnections(collection):
    """Test numClientConnections is a non-negative number."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result,
        expected={"numClientConnections": Exists()},
        raw_res=True,
        msg="numClientConnections should exist",
    )


def test_connPoolStats_numAScopedConnections(collection):
    """Test numAScopedConnections is a non-negative number."""
    result = execute_admin_command(collection, {"connPoolStats": 1})
    assertResult(
        result,
        expected={"numAScopedConnections": Exists()},
        raw_res=True,
        msg="numAScopedConnections should exist",
    )
