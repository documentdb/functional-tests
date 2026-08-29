"""
Smoke test for $sampleRate expression.

Tests basic $sampleRate match expression functionality.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.smoke


def test_smoke_sampleRate_rate_one(collection):
    """Test $sampleRate: 1.0 returns all documents (deterministic upper boundary)."""
    collection.insert_many([{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}, {"_id": 3, "val": "c"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$sampleRate": 1.0}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}, {"_id": 3, "val": "c"}]
    assertSuccess(result, expected, msg="$sampleRate: 1.0 should return all documents")


def test_smoke_sampleRate_rate_zero(collection):
    """Test $sampleRate: 0.0 returns no documents (deterministic lower boundary)."""
    collection.insert_many([{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}, {"_id": 3, "val": "c"}])

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"$sampleRate": 0.0}}],
            "cursor": {},
        },
    )

    expected = []
    assertSuccess(result, expected, msg="$sampleRate: 0.0 should return no documents")
