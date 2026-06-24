"""
readConcern afterClusterTime validation tests (replica set).

Verifies that afterClusterTime in readConcern rejects invalid types.
These tests require a replica set topology.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.requires(cluster_read_concern=True)


def test_find_afterClusterTime_rejects_string(collection):
    """Test find rejects non-Timestamp afterClusterTime (string)."""
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": {"level": "local", "afterClusterTime": "invalid"},
        },
    )
    assertFailureCode(
        result, TYPE_MISMATCH_ERROR, msg="find should reject non-Timestamp afterClusterTime string."
    )


def test_find_afterClusterTime_rejects_integer(collection):
    """Test find rejects non-Timestamp afterClusterTime (integer)."""
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": {"level": "local", "afterClusterTime": 12345},
        },
    )
    assertFailureCode(
        result,
        TYPE_MISMATCH_ERROR,
        msg="find should reject non-Timestamp afterClusterTime integer.",
    )


def test_find_afterClusterTime_rejects_null(collection):
    """Test find rejects null afterClusterTime."""
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "readConcern": {"level": "local", "afterClusterTime": None},
        },
    )
    assertFailureCode(result, TYPE_MISMATCH_ERROR, msg="find should reject null afterClusterTime.")
