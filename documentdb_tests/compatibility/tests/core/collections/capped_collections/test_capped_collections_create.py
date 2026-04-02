"""
Tests for capped collection operations.

Capped collections are fixed-size collections that maintain insertion order.
This feature may not be supported on all engines.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


@pytest.mark.collection_mgmt
def test_create_capped_collection(collection):
    """Test creating a capped collection."""
    result = execute_command(
        collection, {"create": collection.name + "_capped", "capped": True, "size": 100000}
    )
    assertSuccessPartial(result, {"ok": 1.0}, "Should create capped collection")
