"""Tests for text index creation and sparse query behavior.

Validates compound text index creation, and that documents lacking the
indexed field are excluded from $text query results (text indexes are sparse).
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command

pytestmark = pytest.mark.text_search


def test_text_compound_index(collection):
    """Test compound text index creation succeeds."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "content": "text", "b": -1}, "name": "a_content_b"}],
        },
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="Compound text index creation should succeed")


def test_text_excludes_docs_without_indexed_field(collection):
    """Test $text excludes documents missing the indexed field (text index is sparse)."""
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "hello world"},
            {"_id": 2, "other": "no text field"},
            {"_id": 3, "content": "hello there"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "hello"}},
            "projection": {"_id": 1},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1}, {"_id": 3}],
        msg="$text should exclude documents without the indexed field",
    )
