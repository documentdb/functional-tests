"""
Smoke test for logout command.

Tests basic logout functionality.
"""

import pytest
from pymongo import MongoClient

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_logout(collection, connection_string):
    """Test basic logout behavior.

    logout de-authenticates the connection it runs on, so it must run on a
    dedicated client. Running it on the shared, pooled session connection would
    log that connection out and make every later test on the same worker fail
    with an authorization error.
    """
    dedicated_client: MongoClient = MongoClient(connection_string)
    try:
        isolated_collection = dedicated_client[collection.database.name][collection.name]
        result = execute_command(isolated_collection, {"logout": 1})
    finally:
        dedicated_client.close()

    assertCommandSupported(result, msg="Should support logout command")
