"""
Smoke test for collMod command.

Tests basic collMod command functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_collMod(collection):
    """Test basic collMod command behavior."""
    collection.insert_one({"_id": 1, "value": 10})

    result = execute_command(collection, {"collMod": collection.name, "validationLevel": "off"})

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support collMod command")
