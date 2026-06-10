"""
Update method and context tests for $currentDate update field operator.

Tests $currentDate in updateOne, updateMany, findAndModify, and upsert contexts.
"""

from documentdb_tests.framework.assertions import assertProperties, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists, IsType

# ---------------------------------------------------------------------------
# Property [Update Contexts]: $currentDate works in updateOne, updateMany, findAndModify
# ---------------------------------------------------------------------------


def test_currentDate_updateOne(collection):
    """Test $currentDate in updateOne produces Date type field."""
    collection.insert_one({"_id": 1, "name": "test"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$currentDate": {"modified": True}}}],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"modified": IsType("date")}, msg="Field should be Date after updateOne"
    )


def test_currentDate_updateMany(collection):
    """Test $currentDate in updateMany affects multiple documents."""
    collection.insert_many(
        [
            {"_id": 1, "val": "a"},
            {"_id": 2, "val": "b"},
            {"_id": 3, "val": "c"},
        ]
    )

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$currentDate": {"modified": True}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result, {"n": 3, "nModified": 3}, msg="updateMany should modify all 3 docs"
    )


def test_currentDate_findAndModify_returns_new(collection):
    """Test $currentDate in findAndModify with new:true returns updated document."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$currentDate": {"modified": True}},
            "new": True,
        },
    )
    assertProperties(
        result,
        {"value": {"modified": IsType("date")}},
        raw_res=True,
        msg="findAndModify with new:true should return document with Date field",
    )


def test_currentDate_findAndModify_returns_old(collection):
    """Test $currentDate in findAndModify without new returns old document."""
    collection.insert_one({"_id": 1, "name": "test"})

    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"_id": 1},
            "update": {"$currentDate": {"modified": True}},
        },
    )
    # Old document should not have 'modified' field
    assertSuccessPartial(
        result,
        {"value": {"_id": 1, "name": "test"}},
        msg="findAndModify without new should return old doc",
    )


# ---------------------------------------------------------------------------
# Property [Upsert]: $currentDate with upsert creates field on new document
# ---------------------------------------------------------------------------


def test_currentDate_upsert_creates_doc(collection):
    """Test $currentDate with upsert=true creates new document with Date field."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$currentDate": {"created": True}}, "upsert": True}
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(result, {"created": IsType("date")}, msg="Upserted doc should have Date field")


def test_currentDate_upsert_creates_doc_with_timestamp(collection):
    """Test $currentDate with upsert=true and $type:'timestamp' creates Timestamp field."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"ts": {"$type": "timestamp"}}},
                    "upsert": True,
                }
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result, {"ts": IsType("timestamp")}, msg="Upserted doc should have Timestamp field"
    )


def test_currentDate_upsert_with_filter_fields(collection):
    """Test $currentDate with upsert includes filter equality fields in new document."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1, "category": "A"},
                    "u": {"$currentDate": {"ts": True}},
                    "upsert": True,
                }
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"category": Exists(), "ts": IsType("date")},
        msg="Upserted doc should include filter fields and Date field",
    )
