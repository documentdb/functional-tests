"""Tests for top command consistency, visibility, and special collection types.

Validates idempotency, namespace visibility, format, admin database requirement,
and behavior with capped collections and views.
"""

import pytest

from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertProperties,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import UNAUTHORIZED_ERROR
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.property_checks import Exists, Gte, IsType

pytestmark = pytest.mark.admin


# ---------- Consistency and Idempotency ----------


def test_top_repeated_calls_succeed(collection):
    """Test that calling top 5 times in a row all succeed."""
    for _ in range(5):
        result = execute_admin_command(collection, {"top": 1})
        assertSuccessPartial(result, {"ok": 1.0}, msg="Repeated top call should succeed")


def test_top_counters_non_decreasing_count(collection):
    """Test that total.count is non-decreasing across two consecutive calls."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result1 = execute_admin_command(collection, {"top": 1})
    count1 = result1["totals"][ns]["total"]["count"]
    result2 = execute_admin_command(collection, {"top": 1})
    ns_data2 = result2["totals"][ns]
    assertProperties(
        ns_data2,
        {"total.count": Gte(count1)},
        msg="total.count should be non-decreasing",
        raw_res=True,
    )


def test_top_counters_non_decreasing_time(collection):
    """Test that total.time is non-decreasing across two consecutive calls."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result1 = execute_admin_command(collection, {"top": 1})
    time1 = result1["totals"][ns]["total"]["time"]
    result2 = execute_admin_command(collection, {"top": 1})
    ns_data2 = result2["totals"][ns]
    assertProperties(
        ns_data2,
        {"total.time": Gte(time1)},
        msg="total.time should be non-decreasing",
        raw_res=True,
    )


# ---------- Collection Visibility and Namespace Format ----------


def test_top_newly_created_collection_appears(collection):
    """Test that a newly created collection appears in top totals."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    # Look up namespace directly — dotted path traversal can't handle keys with dots.
    ns_data = result["totals"].get(ns)
    assertProperties(
        {"ns_entry": ns_data},
        {"ns_entry": Exists()},
        msg=f"Namespace {ns} should appear in top totals",
        raw_res=True,
    )


def test_top_multiple_collections_appear(database_client):
    """Test that multiple collections appear in top totals."""
    coll1 = database_client.create_collection("top_multi_coll_1")
    coll2 = database_client.create_collection("top_multi_coll_2")
    coll1.insert_one({"_id": 1})
    coll2.insert_one({"_id": 1})
    result = execute_admin_command(coll1, {"top": 1})
    ns1 = f"{database_client.name}.{coll1.name}"
    ns2 = f"{database_client.name}.{coll2.name}"
    # Look up namespaces directly — dotted path traversal can't handle keys with dots.
    assertProperties(
        {"ns1": result["totals"].get(ns1), "ns2": result["totals"].get(ns2)},
        {"ns1": Exists(), "ns2": Exists()},
        msg="Both namespaces should appear in top totals",
        raw_res=True,
    )


def test_top_namespace_format_db_dot_collection(collection):
    """Test that namespace keys in totals are formatted as db.collection."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    # Look up namespace directly — dotted path traversal can't handle keys with dots.
    ns_data = result["totals"].get(ns)
    assertProperties(
        {"ns_entry": ns_data},
        {"ns_entry": Exists()},
        msg=f"Namespace key should be '{ns}' (db.collection format)",
        raw_res=True,
    )


def test_top_returns_totals_even_with_no_user_operations(collection):
    """Test that top returns totals object even with minimal operations."""
    result = execute_admin_command(collection, {"top": 1})
    assertProperties(
        result,
        {"totals": IsType("object")},
        msg="totals should be an object even with no user operations",
        raw_res=True,
    )


# ---------- Admin Database Requirement ----------


def test_top_admin_db_succeeds(collection):
    """Test that top succeeds when run on admin database."""
    result = execute_admin_command(collection, {"top": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="top should succeed on admin db")


def test_top_non_admin_db_fails(collection):
    """Test that top fails when run on a non-admin database."""
    result = execute_command(collection, {"top": 1})
    assertFailureCode(result, UNAUTHORIZED_ERROR, msg="top should fail on non-admin db")


# ---------- System Collections ----------


def test_top_system_collections_have_event_structure(collection):
    """Test that system namespaces in totals have the expected event field structure."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    # Find any system namespace in totals
    system_ns = None
    for ns_key in result["totals"]:
        if ".system." in ns_key or ns_key.startswith("admin.") or ns_key.startswith("local."):
            system_ns = ns_key
            break
    if system_ns is None:
        pytest.skip("No system namespace found in top totals")
    ns_data = result["totals"][system_ns]
    checks = {}
    for event in [
        "total",
        "readLock",
        "writeLock",
        "queries",
        "getmore",
        "insert",
        "update",
        "remove",
        "commands",
    ]:
        checks[event] = IsType("object")
        checks[f"{event}.time"] = Gte(0)
        checks[f"{event}.count"] = Gte(0)
    assertProperties(
        ns_data,
        checks,
        msg=f"System namespace {system_ns} should have all event fields with time/count",
        raw_res=True,
    )


# ---------- Special Collection Types ----------


def test_top_tracks_capped_collection(database_client):
    """Test that a capped collection appears in top totals with expected structure."""
    coll = database_client.create_collection("top_capped_test", capped=True, size=4096)
    coll.insert_one({"_id": 1})
    result = execute_admin_command(coll, {"top": 1})
    ns = f"{database_client.name}.{coll.name}"
    # Look up namespace directly — dotted path traversal can't handle keys with dots.
    ns_data = result["totals"][ns]
    assertProperties(
        ns_data,
        {"total": IsType("object"), "total.time": Gte(0), "total.count": Gte(0)},
        msg="Capped collection should appear in top totals with expected structure",
        raw_res=True,
    )


def test_top_tracks_view(database_client):
    """Test whether a view namespace appears in top totals."""
    source_coll = database_client.create_collection("top_view_source")
    source_coll.insert_one({"_id": 1})
    database_client.command("create", "top_view_test", viewOn="top_view_source", pipeline=[])
    result = execute_admin_command(source_coll, {"top": 1})
    # Views may or may not appear in top totals depending on implementation.
    # This test documents the actual behavior — verifies totals is present regardless.
    assertProperties(
        result,
        {"totals": IsType("object")},
        msg="top should return totals even when views exist",
        raw_res=True,
    )
