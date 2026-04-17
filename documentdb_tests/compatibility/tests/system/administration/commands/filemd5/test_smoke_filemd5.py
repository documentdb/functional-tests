"""
Smoke test for filemd5 command.

Tests basic filemd5 functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_filemd5(collection):
    """Test basic filemd5 behavior."""
    chunks = collection.database["fs.chunks"]
    chunks.create_index([("files_id", 1), ("n", 1)])
    chunks.insert_one({"_id": 1, "files_id": 1, "n": 0, "data": b"test"})

    result = execute_command(collection, {"filemd5": 1, "root": "fs"})

    expected = {"ok": 1.0, "numChunks": 1}
    assertSuccessPartial(result, expected, msg="Should support filemd5 command")
