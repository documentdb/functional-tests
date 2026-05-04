"""
Smoke test for $documents system stage.

Tests basic $documents system stage functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_admin_command

pytestmark = pytest.mark.smoke


def test_smoke_documents(collection):
    """Test basic $documents system stage behavior."""
    result = execute_admin_command(
        collection,
        {"aggregate": 1, "pipeline": [{"$documents": [{"_id": 1, "name": "test"}]}], "cursor": {}},
    )

    expected = [{"_id": 1, "name": "test"}]
    assertSuccess(result, expected, msg="Should support $documents system stage")
