"""
Smoke test for $indexStats stage.

Tests basic $indexStats functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_indexStats(collection):
    """Test basic $indexStats behavior."""
    collection.create_index([("field", 1)])
    collection.insert_one({"_id": 1, "field": "value"})

    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$indexStats": {}}], "cursor": {}}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support $indexStats stage")
