"""Smoke test for the $$KEEP system variable: the engine accepts it in $redact."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_keep(collection):
    """Test the engine accepts $$KEEP as a $redact result."""
    collection.insert_one({"_id": 1, "o": {"a": 1}})

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$redact": "$$KEEP"}], "cursor": {}},
    )

    assertCommandSupported(result, msg="Should support $$KEEP system variable")
