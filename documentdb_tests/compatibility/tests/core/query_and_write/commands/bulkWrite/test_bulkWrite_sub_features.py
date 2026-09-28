"""Tests for bulkWrite sub-features: arrayFilters, hint, collation, and bypassDocumentValidation."""

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
    IndexModel,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

BULKWRITE_SUB_FEATURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "arrayFilters_modifies_matching_elements",
        docs=[{"_id": 1, "items": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": {"$set": {"items.$[elem].x": 99}},
                    "arrayFilters": [{"elem.x": {"$gt": 1}}],
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite arrayFilters should modify matching array elements",
    ),
    CommandTestCase(
        "update_with_hint",
        indexes=[IndexModel([("x", 1)], name="x_1")],
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"x": 10},
                    "updateMods": {"$set": {"x": 20}},
                    "hint": "x_1",
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 1, "nModified": 1},
        msg="bulkWrite update with a valid hint should succeed",
    ),
    CommandTestCase(
        "delete_with_hint",
        indexes=[IndexModel([("x", 1)], name="x_1")],
        docs=[{"_id": 1, "x": 10}],
        command={
            "bulkWrite": 1,
            "ops": [{"delete": 0, "filter": {"x": 10}, "hint": "x_1"}],
        },
        expected={"ok": 1.0, "nDeleted": 1},
        msg="bulkWrite delete with a valid hint should succeed",
    ),
    CommandTestCase(
        "update_with_collation",
        # Comparison semantics are owned by tests/core/collation/; this only checks wiring.
        docs=[{"_id": 1, "name": "café"}, {"_id": 2, "name": "cafe"}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"name": "cafe"},
                    "updateMods": {"$set": {"matched": True}},
                    "collation": {"locale": "en", "strength": 1},
                    "multi": True,
                }
            ],
        },
        expected={"ok": 1.0, "nMatched": 2, "nModified": 2},
        msg="bulkWrite should forward a per-op collation to the update (wiring check)",
    ),
    CommandTestCase(
        "bypassDocumentValidation_true",
        target_collection=CustomCollection(
            options={"validator": {"$jsonSchema": {"required": ["name"]}}}
        ),
        command={
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1, "x": 1}}],  # missing "name"
            "bypassDocumentValidation": True,
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite bypassDocumentValidation:true should allow a validator-violating write",
    ),
    CommandTestCase(
        "update_mixed_collation",
        docs=[{"_id": 1, "name": "Apple", "v": 1}, {"_id": 2, "name": "apple", "v": 1}],
        command={
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"name": "apple"},
                    "updateMods": {"$set": {"v": 2}},
                    "collation": {"locale": "en", "strength": 2},
                    "multi": True,
                },
                {
                    "update": 0,
                    "filter": {"name": "Apple"},
                    "updateMods": {"$set": {"v": 3}},
                },
            ],
        },
        # First op matches both (case-insensitive), second matches only exact "Apple".
        expected={"ok": 1.0, "nMatched": 3, "nModified": 3},
        msg="bulkWrite collation on one op should not leak to another op",
    ),
    CommandTestCase(
        "collection_uuid_match",
        docs=[{"_id": 0}],
        command=lambda ctx: {
            "bulkWrite": 1,
            "ops": [{"insert": 0, "document": {"_id": 1}}],
            "nsInfo": [{"ns": ctx.namespace, "collectionUUID": ctx.uuids[ctx.collection]}],
        },
        expected={"ok": 1.0, "nInserted": 1},
        msg="bulkWrite with a collectionUUID matching the target collection should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BULKWRITE_SUB_FEATURE_TESTS))
def test_bulkWrite_sub_features(database_client, collection, test):
    """Test bulkWrite sub-features: arrayFilters, hint, collation, and bypassDocumentValidation."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    command = test.build_command(ctx)
    if "nsInfo" not in command:
        command = {**command, "nsInfo": [{"ns": ctx.namespace}]}
    result = execute_admin_command(collection, command)
    assertSuccessPartial(result, test.build_expected(ctx), msg=test.msg)


def test_bulkWrite_arrayFilters_modifies_correct_nested_elements(collection):
    """Test a valid arrayFilters + $[identifier] update changes only matching nested elements."""
    collection.insert_one(
        {"_id": 1, "items": [{"x": 1, "k": "a"}, {"x": 2, "k": "b"}, {"x": 3, "k": "c"}]}
    )
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": {"$set": {"items.$[elem].x": 99}},
                    "arrayFilters": [{"elem.x": {"$gt": 1}}],
                }
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "items": [{"x": 1, "k": "a"}, {"x": 99, "k": "b"}, {"x": 99, "k": "c"}]}],
        msg="bulkWrite arrayFilters should modify only the elements matching the identifier "
        "predicate and leave the rest unchanged",
    )


def test_bulkWrite_collation_affects_arrayFilters_selection(collection):
    """Test op-level collation makes arrayFilters match array elements case-insensitively.

    Which array elements arrayFilters changed is only observable via read-back. With a
    strength:2 (case-insensitive) collation, the filter {e: "apple"} matches BOTH "Apple" and
    "apple"; without collation it would match only the exact "apple". This interaction is not
    exercised by the sibling arrayFilters suite.
    """
    collection.insert_one({"_id": 1, "items": ["Apple", "apple", "banana"]})
    ns = f"{collection.database.name}.{collection.name}"
    execute_admin_command(
        collection,
        {
            "bulkWrite": 1,
            "ops": [
                {
                    "update": 0,
                    "filter": {"_id": 1},
                    "updateMods": {"$set": {"items.$[e]": "X"}},
                    "arrayFilters": [{"e": "apple"}],
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
            "nsInfo": [{"ns": ns}],
        },
    )
    assertSuccess(
        execute_command(collection, {"find": collection.name, "filter": {"_id": 1}}),
        [{"_id": 1, "items": ["X", "X", "banana"]}],
        msg="bulkWrite collation should make arrayFilters match case-insensitively (both Apples)",
    )
