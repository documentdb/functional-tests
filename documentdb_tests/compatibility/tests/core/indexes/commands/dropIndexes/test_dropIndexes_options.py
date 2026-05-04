"""
Tests for dropIndexes command — options and collection variants.

Covers writeConcern, comment options, and behavior on regular, capped,
timeseries, and clustered collections.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

WRITE_CONCERN_CASES: list[IndexTestCase] = [
    IndexTestCase("wc_w1", write_concern={"w": 1}, msg="Should succeed with writeConcern w:1"),
    IndexTestCase(
        "wc_majority",
        write_concern={"w": "majority"},
        msg="Should succeed with writeConcern w:majority",
    ),
    IndexTestCase("wc_w0", write_concern={"w": 0}, msg="Should succeed with writeConcern w:0"),
    IndexTestCase(
        "wc_journal_true",
        write_concern={"w": 1, "j": True},
        msg="Should succeed with writeConcern w:1, j:true",
    ),
    IndexTestCase(
        "wc_journal_false",
        write_concern={"j": False},
        msg="Should succeed with writeConcern j:false",
    ),
    IndexTestCase(
        "wc_majority_journal",
        write_concern={"w": "majority", "j": True},
        msg="Should succeed with writeConcern w:majority, j:true",
    ),
    IndexTestCase(
        "wc_w1_wtimeout",
        write_concern={"w": 1, "wtimeout": 1000},
        msg="Should succeed with writeConcern w:1, wtimeout:1000",
    ),
    IndexTestCase(
        "wc_majority_wtimeout",
        write_concern={"w": "majority", "wtimeout": 5000},
        msg="Should succeed with writeConcern w:majority, wtimeout:5000",
    ),
    IndexTestCase(
        "wc_wtimeout_negative",
        write_concern={"w": 1, "wtimeout": -1},
        msg="Should succeed with writeConcern wtimeout:-1",
    ),
    IndexTestCase(
        "wc_wtimeout_non_numeric",
        write_concern={"w": 1, "wtimeout": "fast"},
        msg="Should succeed with writeConcern wtimeout as string",
    ),
    IndexTestCase("wc_null", write_concern=None, msg="Should succeed with null writeConcern"),
    IndexTestCase(
        "wc_empty_object", write_concern={}, msg="Should succeed with empty writeConcern object"
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_CASES))
def test_dropIndexes_writeConcern(collection, test):
    """Test dropIndexes accepts valid writeConcern options."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection,
        {
            "dropIndexes": collection.name,
            "index": "*",
            "writeConcern": test.write_concern,
        },
    )

    assertSuccessPartial(result, expected={"nIndexesWas": 2, "ok": 1.0}, msg=test.msg)


COMMENT_CASES: list[IndexTestCase] = [
    IndexTestCase(
        "comment_string", comment="dropping indexes", msg="Should succeed with string comment"
    ),
    IndexTestCase("comment_int", comment=42, msg="Should succeed with int comment"),
    IndexTestCase(
        "comment_object", comment={"reason": "cleanup"}, msg="Should succeed with object comment"
    ),
    IndexTestCase("comment_array", comment=[1, 2, 3], msg="Should succeed with array comment"),
    IndexTestCase("comment_bool", comment=True, msg="Should succeed with boolean comment"),
]


@pytest.mark.parametrize("test", pytest_params(COMMENT_CASES))
def test_dropIndexes_comment(collection, test):
    """Test dropIndexes accepts comment of various BSON types."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection,
        {
            "dropIndexes": collection.name,
            "index": "*",
            "comment": test.comment,
        },
    )

    assertSuccessPartial(result, expected={"nIndexesWas": 2, "ok": 1.0}, msg=test.msg)


def test_dropIndexes_capped_collection(database_client, collection):
    """Test dropIndexes on capped collection with secondary index."""
    capped_name = f"{collection.name}_capped"
    database_client.create_collection(capped_name, capped=True, size=4096)
    capped = database_client[capped_name]
    capped.insert_one({"_id": 1, "a": 1})
    capped.create_index("a")

    result = execute_command(capped, {"dropIndexes": capped_name, "index": "*"})

    assertSuccessPartial(
        result, expected={"nIndexesWas": 2, "ok": 1.0}, msg="Should succeed on capped collection"
    )


def test_dropIndexes_timeseries_collection(database_client, collection):
    """Test dropIndexes on timeseries collection with secondary index."""
    ts_name = f"{collection.name}_ts"
    database_client.create_collection(ts_name, timeseries={"timeField": "ts", "metaField": "meta"})
    ts_coll = database_client[ts_name]
    ts_coll.create_index("meta", name="meta_idx")

    result = execute_command(ts_coll, {"dropIndexes": ts_name, "index": "meta_idx"})

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should succeed on timeseries collection",
    )


def test_dropIndexes_clustered_collection(database_client, collection):
    """Test dropIndexes on clustered collection with secondary index."""
    cl_name = f"{collection.name}_clustered"
    database_client.create_collection(cl_name, clusteredIndex={"key": {"_id": 1}, "unique": True})
    cl_coll = database_client[cl_name]
    cl_coll.insert_one({"_id": 1, "a": 1})
    cl_coll.create_index("a", name="a_idx")

    result = execute_command(cl_coll, {"dropIndexes": cl_name, "index": "a_idx"})

    assertSuccessPartial(
        result, expected={"nIndexesWas": 1, "ok": 1.0}, msg="Should succeed on clustered collection"
    )


def test_dropIndexes_system_buckets_collection(database_client, collection):
    """Test dropIndexes directly on system.buckets backing collection."""
    ts_name = f"{collection.name}_ts"
    database_client.create_collection(ts_name, timeseries={"timeField": "ts", "metaField": "meta"})
    buckets_coll = database_client[f"system.buckets.{ts_name}"]

    result = execute_command(
        buckets_coll, {"dropIndexes": f"system.buckets.{ts_name}", "index": "*"}
    )

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 1, "ok": 1.0},
        msg="Should succeed on system.buckets backing collection",
    )
