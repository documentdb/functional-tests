"""Tests for bulkWrite mixed and multi-namespace operations."""

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command


def test_bulkWrite_insert_update_delete_mixed(collection):
    """Test bulkWrite combines insert, update, and delete in one command."""
    collection.insert_one({"_id": 1, "x": 10})
    ns = f"{collection.database.name}.{collection.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 2, "x": 20}},
                {"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 99}}},
                {"delete": 0, "filter": {"_id": 2}},
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "nInserted": 1, "nMatched": 1, "nModified": 1, "nDeleted": 1},
        msg="bulkWrite should combine insert, update, and delete in one command",
    )


def test_bulkWrite_operations_across_multiple_namespaces(collection):
    """Test bulkWrite operates across multiple namespaces listed in the nsInfo array."""
    sibling = collection.database[f"{collection.name}_b"]
    sibling.drop()
    ns = f"{collection.database.name}.{collection.name}"
    ns_b = f"{collection.database.name}.{sibling.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1, "src": "a"}},
                {"insert": 1, "document": {"_id": 1, "src": "b"}},
            ],
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "nInserted": 2},
        msg="bulkWrite should operate across multiple namespaces in the nsInfo array",
    )
    sibling.drop()


def test_bulkWrite_ops_reference_correct_namespace_by_index(collection):
    """Test bulkWrite ops target the namespace selected by their index into nsInfo."""
    sibling = collection.database[f"{collection.name}_b"]
    sibling.drop()
    collection.insert_one({"_id": 1, "x": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_b = f"{collection.database.name}.{sibling.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 1, "document": {"_id": 10, "y": 1}},
                {"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 99}}},
            ],
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "nInserted": 1, "nMatched": 1, "nModified": 1},
        msg="bulkWrite ops should reference the correct namespace by index",
    )
    sibling.drop()


def test_bulkWrite_interleaved_namespaces(collection):
    """Test bulkWrite executes operations interleaved across multiple namespaces."""
    sibling = collection.database[f"{collection.name}_b"]
    sibling.drop()
    ns = f"{collection.database.name}.{collection.name}"
    ns_b = f"{collection.database.name}.{sibling.name}"
    result = execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 1}},
                {"insert": 1, "document": {"_id": 1}},
                {"insert": 0, "document": {"_id": 2}},
                {"insert": 1, "document": {"_id": 2}},
            ],
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "nInserted": 4},
        msg="bulkWrite should execute operations interleaved across namespaces",
    )
    sibling.drop()


def _run_routing_bulkwrite(collection, sibling):
    """Run a 2-namespace bulkWrite with overlapping _ids to catch mis-routing via content."""
    sibling.drop()
    collection.insert_one({"_id": 1, "x": 1})  # seeds ns0 only
    ns = f"{collection.database.name}.{collection.name}"
    ns_b = f"{collection.database.name}.{sibling.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {"insert": 0, "document": {"_id": 2, "tag": "a"}},  # ns0
                {"update": 0, "filter": {"_id": 1}, "updateMods": {"$set": {"x": 99}}},  # ns0
                {"insert": 1, "document": {"_id": 1, "tag": "b"}},  # ns1 (same _id as ns0)
                {"insert": 1, "document": {"_id": 2, "tag": "b2"}},  # ns1 (same _id as ns0)
            ],
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
        },
    )


def test_bulkWrite_routes_index0_ops_to_namespace0_read_back(collection):
    """Test index-0 ops land only in namespace 0, verified by read-back."""
    sibling = collection.database[f"{collection.name}_b"]
    _run_routing_bulkwrite(collection, sibling)
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}),
        [{"_id": 1, "x": 99}, {"_id": 2, "tag": "a"}],
        msg="bulkWrite ops with namespace index 0 should land only in namespace 0",
    )


def test_bulkWrite_routes_index1_ops_to_namespace1_read_back(collection):
    """Test index-1 ops land only in namespace 1, verified by read-back."""
    sibling = collection.database[f"{collection.name}_b"]
    _run_routing_bulkwrite(collection, sibling)
    assertSuccess(
        execute_command(sibling, {"find": sibling.name, "filter": {}, "sort": {"_id": 1}}),
        [{"_id": 1, "tag": "b"}, {"_id": 2, "tag": "b2"}],
        msg="bulkWrite ops with namespace index 1 should land only in namespace 1",
    )


def _seed_two_namespaces(collection, sibling):
    """Seed ns0 with {_id:1,x:1} and {_id:50}, ns1 with {_id:1,y:1}; return (ns0, ns1)."""
    sibling.drop()
    collection.insert_many([{"_id": 1, "x": 1}, {"_id": 50}])
    sibling.insert_one({"_id": 1, "y": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_b = f"{collection.database.name}.{sibling.name}"
    return ns, ns_b


def _mixed_cross_ns_ops():
    """Insert+update+delete across two namespaces, with a dup-key failure at idx 2."""
    return [
        {"insert": 0, "document": {"_id": 2, "v": "i0"}},  # ns0 insert — good
        {"update": 1, "filter": {"_id": 1}, "updateMods": {"$set": {"y": 99}}},  # ns1 update — good
        {"insert": 0, "document": {"_id": 1, "v": "dup"}},  # ns0 insert — dup key, FAILS (idx 2)
        {"delete": 0, "filter": {"_id": 50}},  # ns0 delete — good, but after the failure
    ]


def test_bulkWrite_ordered_true_skips_delete_after_mid_batch_failure(collection):
    """Test ordered:true mixed-op/multi-ns batch stops at the failure, skipping the later delete."""
    sibling = collection.database[f"{collection.name}_b"]
    ns, ns_b = _seed_two_namespaces(collection, sibling)
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": _mixed_cross_ns_ops(),
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
            "ordered": True,
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}),
        [{"_id": 1, "x": 1}, {"_id": 2, "v": "i0"}, {"_id": 50}],
        msg="ordered:true should skip the delete after the mid-batch failure (_id:50 kept)",
    )


def test_bulkWrite_ordered_false_runs_delete_after_mid_batch_failure(collection):
    """Test ordered:false mixed-op/multi-ns batch runs the later delete despite the failure."""
    sibling = collection.database[f"{collection.name}_b"]
    ns, ns_b = _seed_two_namespaces(collection, sibling)
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": _mixed_cross_ns_ops(),
            "nsInfo": [{"ns": ns}, {"ns": ns_b}],
            "ordered": False,
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}),
        [{"_id": 1, "x": 1}, {"_id": 2, "v": "i0"}],
        msg="ordered:false should run the delete after the mid-batch failure (_id:50 removed)",
    )
