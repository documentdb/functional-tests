"""Tests for dataSize command authorization.

These tests verify RBAC behavior for the dataSize command.
They require authentication to be enabled on the server.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = [pytest.mark.admin, pytest.mark.rbac]


def test_dataSize_succeeds_with_default_connection(collection):
    """Test dataSize succeeds with default connection privileges."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_command(collection, {"dataSize": ns})
    assertSuccessPartial(result, {"ok": 1.0}, msg="Should succeed with default privileges")
