"""
Smoke test for listCollections command.

Tests basic listCollections command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_listCollections(collection):
    """Test basic listCollections command behavior."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(collection, {"listCollections": 1})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support listCollections command")
