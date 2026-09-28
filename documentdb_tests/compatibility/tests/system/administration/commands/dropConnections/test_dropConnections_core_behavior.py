"""Tests for dropConnections command core behavior.

Verifies that dropConnections succeeds with valid hostAndPort values,
silently ignores elements without a colon (no port separator), and
rejects entries with invalid host:port parsing.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase

pytestmark = [pytest.mark.admin, pytest.mark.no_parallel]


@dataclass(frozen=True)
class DropConnectionsTestCase(BaseTestCase):
    """Test case for dropConnections command."""

    host_and_port: Any = None


# Property [Core Success]: dropConnections succeeds with valid hostAndPort arrays.
CORE_SUCCESS_TESTS: list[DropConnectionsTestCase] = [
    DropConnectionsTestCase(
        "empty_array",
        host_and_port=[],
        expected={"ok": 1.0},
        msg="dropConnections should succeed with empty hostAndPort array (no-op).",
    ),
    DropConnectionsTestCase(
        "single_valid_host_port",
        host_and_port=["nonexistent.host.invalid:27017"],
        expected={"ok": 1.0},
        msg="dropConnections should succeed with a valid host:port string.",
    ),
    DropConnectionsTestCase(
        "multiple_valid_host_ports",
        host_and_port=["host1.invalid:27017", "host2.invalid:27018"],
        expected={"ok": 1.0},
        msg="dropConnections should succeed with multiple valid host:port strings.",
    ),
    DropConnectionsTestCase(
        "nonexistent_host_no_connection",
        host_and_port=["no.such.host.invalid:12345"],
        expected={"ok": 1.0},
        msg="dropConnections should succeed silently for hosts with no active connection.",
    ),
    DropConnectionsTestCase(
        "idempotent_repeated_call",
        host_and_port=["nonexistent.host.invalid:27017"],
        expected={"ok": 1.0},
        msg="dropConnections should be idempotent when called with same host.",
    ),
    DropConnectionsTestCase(
        "ip_address_with_port",
        host_and_port=["192.168.1.1:27017"],
        expected={"ok": 1.0},
        msg="dropConnections should accept IP address with port.",
    ),
    DropConnectionsTestCase(
        "duplicate_entries_in_array",
        host_and_port=["host.invalid:27017", "host.invalid:27017"],
        expected={"ok": 1.0},
        msg="dropConnections should handle duplicate entries idempotently.",
    ),
    DropConnectionsTestCase(
        "ipv6_format",
        host_and_port=["[::1]:27017"],
        expected={"ok": 1.0},
        msg="dropConnections should accept IPv6 format address.",
    ),
]

# Property [Silent Ignore]: dropConnections silently ignores hostAndPort elements
# that contain no colon (no port separator).
SILENT_IGNORE_TESTS: list[DropConnectionsTestCase] = [
    DropConnectionsTestCase(
        "hostname_only_no_colon",
        host_and_port=["hostname_only"],
        expected={"ok": 1.0},
        msg="dropConnections should silently ignore entry without a colon.",
    ),
]

# Property [Host Parse Rejection]: dropConnections rejects hostAndPort entries
# that contain a colon but fail host:port parsing (empty host, invalid port).
HOST_PARSE_ERROR_TESTS: list[DropConnectionsTestCase] = [
    DropConnectionsTestCase(
        "missing_hostname_colon_port",
        host_and_port=[":27017"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject entry with empty host component.",
    ),
    DropConnectionsTestCase(
        "hostname_trailing_colon",
        host_and_port=["host:"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject entry with empty port after colon.",
    ),
    DropConnectionsTestCase(
        "empty_string",
        host_and_port=[""],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject empty string entry.",
    ),
    DropConnectionsTestCase(
        "port_zero",
        host_and_port=["host.invalid:0"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject port 0 (out of range).",
    ),
    DropConnectionsTestCase(
        "high_port_number",
        host_and_port=["host.invalid:99999"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject port exceeding valid range.",
    ),
    DropConnectionsTestCase(
        "non_numeric_port",
        host_and_port=["host.invalid:abc"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject non-numeric port.",
    ),
    DropConnectionsTestCase(
        "multiple_colons_no_brackets",
        host_and_port=["host:port:extra"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject entry with multiple colons without IPv6 brackets.",
    ),
    DropConnectionsTestCase(
        "negative_port",
        host_and_port=["host.invalid:-1"],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="dropConnections should reject negative port number.",
    ),
]

ALL_TESTS = CORE_SUCCESS_TESTS + SILENT_IGNORE_TESTS + HOST_PARSE_ERROR_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_dropConnections_core_behavior(collection, test):
    """Test dropConnections core behavior and host:port parsing."""
    result = execute_admin_command(
        collection, {"dropConnections": 1, "hostAndPort": test.host_and_port}
    )
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
