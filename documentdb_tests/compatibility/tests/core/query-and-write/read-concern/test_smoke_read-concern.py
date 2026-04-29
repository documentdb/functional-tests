"""
Smoke test for readConcern.

Tests basic readConcern functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_read_concern(collection):
    """Test basic readConcern behavior."""
    collection.insert_many([{"_id": 1, "name": "test"}])

    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "readConcern": {"level": "local"}}
    )

    expected = [{"_id": 1, "name": "test"}]
    assertSuccess(result, expected, msg="Should support readConcern")
