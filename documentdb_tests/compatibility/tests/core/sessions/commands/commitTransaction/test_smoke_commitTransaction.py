"""
Smoke test for commitTransaction command.

Tests basic commitTransaction command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = [pytest.mark.smoke, pytest.mark.admin, pytest.mark.requires(transactions=True)]


def test_smoke_commitTransaction(collection):
    """Test basic commitTransaction command behavior."""
    client = collection.database.client
    with client.start_session() as session:
        session.start_transaction()
        collection.insert_one({"_id": 1}, session=session)
        result = execute_admin_command(collection, {"commitTransaction": 1}, session=session)

    assertCommandSupported(result, msg="Should support commitTransaction command")
