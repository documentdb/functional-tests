"""
Tests for listIndexes command — collection variants, edge cases, and comment field.

Covers regular, capped, timeseries, clustered collections, long names, special characters,
system collections, system.buckets, rename, and comment field behavior.
"""

from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command


def test_listIndexes_capped_collection(database_client):
    """Test listIndexes on capped collection returns _id index."""
    coll_name = "test_capped_coll"
    database_client.create_collection(coll_name, capped=True, size=4096)
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
    finally:
        coll.drop()


def test_listIndexes_capped_collection_with_secondary(database_client):
    """Test listIndexes on capped collection with secondary index returns both."""
    coll_name = "test_capped_secondary"
    database_client.create_collection(coll_name, capped=True, size=4096)
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1, "a": 1})
    coll.create_index("a", name="a_1")

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(
            result,
            [{"v": 2, "key": {"_id": 1}, "name": "_id_"}, {"v": 2, "key": {"a": 1}, "name": "a_1"}],
        )
    finally:
        coll.drop()


def test_listIndexes_timeseries_collection(database_client):
    """Test listIndexes on timeseries collection with no secondary indexes returns empty."""
    coll_name = "test_ts_coll"
    database_client.create_collection(coll_name, timeseries={"timeField": "ts"})
    coll = database_client[coll_name]

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(result, [])
    finally:
        database_client.drop_collection(coll_name)


def test_listIndexes_timeseries_with_secondary(database_client):
    """Test listIndexes on timeseries collection with secondary index returns both."""
    coll_name = "test_ts_secondary"
    database_client.create_collection(
        coll_name, timeseries={"timeField": "ts", "metaField": "meta"}
    )
    coll = database_client[coll_name]
    coll.create_index("meta", name="meta_1")

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(
            result,
            [
                {"v": 2, "key": {"meta": 1, "ts": 1}, "name": "meta_1_ts_1"},
                {"v": 2, "key": {"meta": 1}, "name": "meta_1"},
            ],
            ignore_doc_order=True,
        )
    finally:
        database_client.drop_collection(coll_name)


def test_listIndexes_clustered_collection(database_client):
    """Test listIndexes on clustered collection returns index with clustered: true."""
    coll_name = "test_clustered_coll"
    database_client.create_collection(coll_name, clusteredIndex={"key": {"_id": 1}, "unique": True})
    coll = database_client[coll_name]

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(
            result,
            [{"v": 2, "key": {"_id": 1}, "name": "_id_", "unique": True, "clustered": True}],
        )
    finally:
        coll.drop()


def test_listIndexes_clustered_unchanged_after_failed_createIndex(database_client):
    """Test listIndexes output unchanged after failed createIndex with clustered option."""
    coll_name = "test_clustered_fail"
    database_client.create_collection(coll_name, clusteredIndex={"key": {"_id": 1}, "unique": True})
    coll = database_client[coll_name]

    try:
        execute_command(
            coll,
            {
                "createIndexes": coll_name,
                "indexes": [{"key": {"a": 1}, "name": "a_1", "clustered": True}],
            },
        )

        after = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(
            after,
            [{"v": 2, "key": {"_id": 1}, "name": "_id_", "unique": True, "clustered": True}],
        )
    finally:
        coll.drop()


def test_listIndexes_long_collection_name(database_client):
    """Test listIndexes on collection with very long name succeeds."""
    coll_name = "a" * 200
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
    finally:
        coll.drop()


def test_listIndexes_long_name_correct_index_names(database_client):
    """Test listIndexes returns correct index names on long-named collection."""
    coll_name = "a" * 100
    coll = database_client[coll_name]
    doc = {"_id": 1}
    for i in range(10):
        doc[f"f{i}"] = 1
    coll.insert_one(doc)
    indexes = [{"key": {f"f{i}": 1}, "name": f"f{i}_1"} for i in range(10)]
    execute_command(coll, {"createIndexes": coll_name, "indexes": indexes})

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        expected = [{"v": 2, "key": {"_id": 1}, "name": "_id_"}]
        for i in range(10):
            expected.append({"v": 2, "key": {f"f{i}": 1}, "name": f"f{i}_1"})
        assertSuccess(result, expected)
    finally:
        coll.drop()


def test_listIndexes_long_name_drop_secondary_indexes(database_client):
    """Test dropIndexes by name on long-named collection then listIndexes returns only _id."""
    coll_name = "b" * 100
    coll = database_client[coll_name]
    doc = {"_id": 1}
    for i in range(3):
        doc[f"f{i}"] = 1
    coll.insert_one(doc)
    indexes = [{"key": {f"f{i}": 1}, "name": f"f{i}_1"} for i in range(3)]
    execute_command(coll, {"createIndexes": coll_name, "indexes": indexes})
    for i in range(3):
        coll.drop_index(f"f{i}_1")

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
    finally:
        coll.drop()


def test_listIndexes_special_characters_in_name(database_client):
    """Test listIndexes on collection with special characters in name."""
    coll_name = "test-coll_with.special"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})

    try:
        result = execute_command(coll, {"listIndexes": coll_name})
        assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
    finally:
        coll.drop()


def test_listIndexes_after_rename(database_client):
    """Test listIndexes after rename collection shows indexes preserved."""
    src_name = "test_rename_src"
    dst_name = "test_rename_dst"
    src = database_client[src_name]
    src.insert_one({"_id": 1, "a": 1})
    src.create_index("a", name="a_1")

    db_name = database_client.name
    database_client.client.admin.command(
        {"renameCollection": f"{db_name}.{src_name}", "to": f"{db_name}.{dst_name}"}
    )

    try:
        dst = database_client[dst_name]
        result = execute_command(dst, {"listIndexes": dst_name})
        assertSuccess(
            result,
            [{"v": 2, "key": {"_id": 1}, "name": "_id_"}, {"v": 2, "key": {"a": 1}, "name": "a_1"}],
        )
    finally:
        database_client.drop_collection(dst_name)
        database_client.drop_collection(src_name)


def test_listIndexes_system_profile(database_client):
    """Test listIndexes on system.profile collection returns empty firstBatch."""
    db = database_client
    db.command({"profile": 2})
    try:
        result = execute_command(db["system.profile"], {"listIndexes": "system.profile"})
        assertSuccess(result, [])
    finally:
        db.command({"profile": 0})
        db.drop_collection("system.profile")


def test_listIndexes_system_views(database_client):
    """Test listIndexes on system.views collection returns _id index."""
    src_name = "test_sys_views_src"
    database_client[src_name].insert_one({"_id": 1})
    database_client.create_collection("test_view_for_sys", viewOn=src_name, pipeline=[])

    try:
        result = execute_command(database_client["system.views"], {"listIndexes": "system.views"})
        assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
    finally:
        database_client.drop_collection("test_view_for_sys")
        database_client.drop_collection(src_name)


def test_listIndexes_comment_string_succeeds(collection):
    """Test listIndexes with comment: 'test' succeeds."""
    collection.insert_one({"_id": 1})

    result = execute_command(collection, {"listIndexes": collection.name, "comment": "test"})

    assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])


def test_listIndexes_comment_inherited_by_getMore(collection):
    """Test comment is inherited by subsequent getMore commands."""
    db = collection.database
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )

    db.command({"profile": 2})

    try:
        result = execute_command(
            collection,
            {
                "listIndexes": collection.name,
                "cursor": {"batchSize": 1},
                "comment": "getmore_inherit_test",
            },
        )
        cursor_id = result["cursor"]["id"]
        execute_command(collection, {"getMore": cursor_id, "collection": collection.name})

        result = execute_command(
            db["system.profile"],
            {
                "count": "system.profile",
                "query": {
                    "command.getMore": {"$exists": True},
                    "command.comment": "getmore_inherit_test",
                },
            },
        )
        assertSuccessPartial(
            result, {"n": 1}, msg="Comment should be inherited by getMore in profiler"
        )
    finally:
        db.command({"profile": 0})
        db.system.profile.drop()


def test_listIndexes_system_buckets_collection(database_client):
    """Test listIndexes on system.buckets prefix collection succeeds with empty result."""
    coll_name = "ts_test_coll"
    database_client.create_collection(coll_name, timeseries={"timeField": "ts"})
    buckets_coll_name = "system.buckets." + coll_name
    coll = database_client[buckets_coll_name]
    try:
        result = execute_command(coll, {"listIndexes": buckets_coll_name})
        assertSuccess(result, [])
    finally:
        database_client.drop_collection(coll_name)
