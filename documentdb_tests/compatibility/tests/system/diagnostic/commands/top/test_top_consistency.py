"""Tests for top command consistency, visibility, and special collection types.

Validates idempotency, namespace visibility, system namespace structure,
and behavior with capped collections and views.

Standalone functions are used throughout because every test requires runtime
logic that DiagnosticTestCase cannot express: multi-call comparisons with
dynamic thresholds, namespace key extraction from the response, conditional
skips, or ad-hoc collection creation (capped, views).
"""

import pytest

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.property_checks import Gte, IsType

pytestmark = pytest.mark.admin


# Property [Idempotency]: repeated top calls succeed and counters are non-decreasing.


def test_top_repeated_calls_return_ok(collection):
    """Test that calling top returns ok after multiple calls."""
    for _ in range(5):
        execute_admin_command(collection, {"top": 1})
    result = execute_admin_command(collection, {"top": 1})
    assertSuccessPartial(result, {"ok": 1.0}, msg="top should succeed after repeated calls")


def test_top_counters_non_decreasing_count(collection):
    """Test that total.count is non-decreasing across two consecutive calls."""
    collection.insert_one({"_id": 1})
    ns = f"{collection.database.name}.{collection.name}"
    result1 = execute_admin_command(collection, {"top": 1})
    ns_data1 = result1["totals"].get(ns)
    if ns_data1 is None:
        raise AssertionError(f"Namespace {ns} not found in first top call")
    count1 = ns_data1["total"]["count"]
    result2 = execute_admin_command(collection, {"top": 1})
    ns_data2 = result2["totals"].get(ns)
    if ns_data2 is None:
        raise AssertionError(f"Namespace {ns} not found in second top call")
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
    ns_data1 = result1["totals"].get(ns)
    if ns_data1 is None:
        raise AssertionError(f"Namespace {ns} not found in first top call")
    time1 = ns_data1["total"]["time"]
    result2 = execute_admin_command(collection, {"top": 1})
    ns_data2 = result2["totals"].get(ns)
    if ns_data2 is None:
        raise AssertionError(f"Namespace {ns} not found in second top call")
    assertProperties(
        ns_data2,
        {"total.time": Gte(time1)},
        msg="total.time should be non-decreasing",
        raw_res=True,
    )


# Property [Collection Visibility]: active collections appear in totals as db.collection keys.


def test_top_newly_created_collection_appears(collection):
    """Test that a newly created collection appears in top totals."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(
        ns_data,
        {"total": IsType("object")},
        msg=f"Namespace {ns} should appear in top totals",
        raw_res=True,
    )


def test_top_multiple_collections_appear(collection):
    """Test that multiple collections appear in top totals."""
    db = collection.database
    coll1 = db.create_collection(f"{collection.name}_multi1")
    coll2 = db.create_collection(f"{collection.name}_multi2")
    coll1.insert_one({"_id": 1})
    coll2.insert_one({"_id": 1})
    result = execute_admin_command(coll1, {"top": 1})
    ns1 = f"{db.name}.{coll1.name}"
    ns2 = f"{db.name}.{coll2.name}"
    ns1_data = result["totals"].get(ns1)
    ns2_data = result["totals"].get(ns2)
    if ns1_data is None:
        raise AssertionError(f"Namespace {ns1} not found in top totals")
    if ns2_data is None:
        raise AssertionError(f"Namespace {ns2} not found in top totals")
    assertProperties(
        {"ns1": ns1_data, "ns2": ns2_data},
        {"ns1": IsType("object"), "ns2": IsType("object")},
        msg="Both namespaces should appear in top totals",
        raw_res=True,
    )


# Property [System Collections]: system namespaces have the standard event field structure.


def test_top_system_collections_have_event_structure(collection):
    """Test that a system namespace in totals has the expected event field structure."""
    collection.insert_one({"_id": 1})
    result = execute_admin_command(collection, {"top": 1})
    system_ns = None
    for ns_key in result["totals"]:
        if ".system." in ns_key or ns_key.startswith("admin.") or ns_key.startswith("local."):
            system_ns = ns_key
            break
    if system_ns is None:
        pytest.skip("No system namespace found in top totals")
    ns_data = result["totals"][system_ns]
    assertProperties(
        ns_data,
        {"total": IsType("object"), "total.time": Gte(0), "total.count": Gte(0)},
        msg=f"System namespace {system_ns} should have event fields with time/count",
        raw_res=True,
    )


# Property [Special Collection Types]: capped collections and views are handled by top.


def test_top_tracks_capped_collection(collection):
    """Test that a capped collection appears in top totals with expected structure."""
    db = collection.database
    coll = db.create_collection(f"{collection.name}_capped", capped=True, size=4096)
    coll.insert_one({"_id": 1})
    result = execute_admin_command(coll, {"top": 1})
    ns = f"{db.name}.{coll.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(
        ns_data,
        {"total": IsType("object"), "total.time": Gte(0), "total.count": Gte(0)},
        msg="Capped collection should appear in top totals with expected structure",
        raw_res=True,
    )


def test_top_tracks_view(collection):
    """Test that a view namespace appears in top totals."""
    db = collection.database
    source_coll = db.create_collection(f"{collection.name}_view_src")
    source_coll.insert_one({"_id": 1})
    view_name = f"{collection.name}_view"
    db.command("create", view_name, viewOn=source_coll.name, pipeline=[])
    result = execute_admin_command(source_coll, {"top": 1})
    view_ns = f"{db.name}.{view_name}"
    view_data = result["totals"].get(view_ns)
    if view_data is None:
        raise AssertionError(f"Namespace {view_ns} not found in top totals")
    assertProperties(
        view_data,
        {"total": IsType("object")},
        msg=f"View namespace {view_ns} should appear in top totals",
        raw_res=True,
    )
