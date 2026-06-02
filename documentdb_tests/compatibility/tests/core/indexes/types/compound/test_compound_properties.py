"""Tests for compound index properties.

Validates numeric equivalence in compound indexes.
"""

import pytest
from bson import Int64

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.index


def test_compound_numeric_int_query_matches_long(collection):
    """Test query with int matches document with long via compound index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1, "b": 1}, "name": "ab"}]},
    )
    collection.insert_one({"_id": 1, "a": Int64(1), "b": Int64(2)})
    result = execute_command(collection, {"find": collection.name, "filter": {"a": 1, "b": 2}})
    assertSuccess(
        result, [{"_id": 1, "a": Int64(1), "b": Int64(2)}], msg="int query matches long in compound"
    )
