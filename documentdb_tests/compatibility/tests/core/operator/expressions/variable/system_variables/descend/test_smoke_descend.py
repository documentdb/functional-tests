"""Smoke test for the $$DESCEND system variable: the engine accepts it in $redact."""

import pytest

from documentdb_tests.framework.assertions import assertCommandSupported
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_descend(collection):
    """Test the engine accepts $$DESCEND as a $redact result."""
    collection.insert_one({"_id": 1, "o": {"a": 1}})

    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$redact": "$$DESCEND"}], "cursor": {}},
    )

    assertCommandSupported(result, msg="Should support $$DESCEND system variable")
