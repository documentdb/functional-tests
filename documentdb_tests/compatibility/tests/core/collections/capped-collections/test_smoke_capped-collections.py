"""
Smoke test for capped-collections.

Tests basic capped collection functionality with size limit.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_capped_collections(collection):
    """Test basic capped collection creation."""
    result = execute_command(
        collection, {"create": f"{collection.name}_capped", "capped": True, "size": 1024.0}
    )

    expected = {"ok": 1.0}
    assertSuccessPartial(result, expected, msg="Should support creating capped collections")
