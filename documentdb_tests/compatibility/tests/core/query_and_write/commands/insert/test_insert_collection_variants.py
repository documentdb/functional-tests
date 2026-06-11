"""
Tests for insert command with different collection variants.

Validates behavior on regular collections, capped collections, and views.
Collection names are derived from the fixture collection name to avoid
collisions under parallel execution.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.target_collection import CappedCollection, ViewCollection


@pytest.mark.insert
def test_insert_into_regular_collection(collection):
    """Test insert into regular collection succeeds."""
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"_id": 1, "a": 1}]},
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "n": 1}, msg="insert should succeed on regular collection."
    )


@pytest.mark.insert
def test_insert_into_capped_collection(collection):
    """Test insert into capped collection succeeds."""
    capped = CappedCollection(size=1_048_576).resolve(collection.database, collection)
    try:
        result = execute_command(
            capped,
            {"insert": capped.name, "documents": [{"_id": 1, "a": 1}]},
        )
        assertSuccessPartial(
            result, {"ok": 1.0, "n": 1}, msg="insert should succeed on capped collection."
        )
    finally:
        capped.drop()


@pytest.mark.insert
def test_insert_into_view_fails(collection):
    """Test insert into a view fails (views are read-only)."""
    view = ViewCollection().resolve(collection.database, collection)
    try:
        result = execute_command(
            view,
            {"insert": view.name, "documents": [{"_id": 1}]},
        )
        assertFailureCode(
            result,
            COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
            msg="insert should reject insert into view.",
        )
    finally:
        view.drop()


@pytest.mark.insert
def test_insert_capped_collection_wraps_old_documents(collection):
    """Test that capped collection wraps and does not error when full."""
    # A tiny capped collection that can hold roughly 2 small documents.
    # Inserting more succeeds — old docs are silently evicted, not an error.
    capped = CappedCollection(size=4096, max=2).resolve(collection.database, collection)
    try:
        for i in range(5):
            result = execute_command(
                capped,
                {"insert": capped.name, "documents": [{"_id": i, "x": i}]},
            )
            assertResult(
                result,
                expected={"ok": 1.0, "n": 1},
                raw_res=True,
                msg="insert into capped collection should always succeed by evicting old docs.",
            )
    finally:
        capped.drop()
