"""
Smoke test for explain command.

Tests basic explain command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_explain(collection):
    """Test basic explain command behavior."""
    collection.insert_one({"_id": 1, "x": 1})

    result = execute_command(collection, {"explain": {"find": collection.name, "filter": {"x": 1}}})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support explain command")
