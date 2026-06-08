"""
Smoke test for clustered-collections.

Tests basic clustered collection functionality with clustered index on _id.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_clustered_collections(collection):
    """Test basic clustered collection creation."""
    result = execute_command(
        collection,
        {
            "create": f"{collection.name}_clustered",
            "clusteredIndex": {"key": {"_id": 1}, "unique": True},
        },
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support creating clustered collections")
