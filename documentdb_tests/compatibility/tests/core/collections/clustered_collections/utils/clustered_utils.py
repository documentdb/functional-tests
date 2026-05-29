"""Shared utilities for clustered collection tests."""

from __future__ import annotations

from documentdb_tests.framework.executor import execute_command


def create_clustered(collection):
    """Create a clustered collection and return its name."""
    name = f"{collection.name}_clustered"
    execute_command(
        collection,
        {"create": name, "clusteredIndex": {"key": {"_id": 1}, "unique": True}},
    )
    return name
