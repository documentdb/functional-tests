"""Tests for $out stage - write behavior."""

from __future__ import annotations

import threading
from typing import cast

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.out.utils.out_test_helpers import (
    OutTestCase,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    populate_collection,
)
from documentdb_tests.framework.assertions import (
    assertSuccess,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Database Name Acceptance]: any non-empty string of non-null
# bytes that does not contain a slash, backslash, dot, ASCII space, or dollar
# prefix is accepted as a database name.
OUT_DATABASE_NAME_ACCEPTANCE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "db_control_character",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\x01",
        msg="$out should accept a control character as a database name",
    ),
    OutTestCase(
        "db_unicode_no_break_space",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\u00a0",
        msg="$out should accept Unicode no-break space as a database name",
    ),
    OutTestCase(
        "db_zero_width_space",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\u200b",
        msg="$out should accept zero-width space as a database name",
    ),
    OutTestCase(
        "db_emoji",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\U0001f389",
        msg="$out should accept emoji as a database name",
    ),
    OutTestCase(
        "db_cjk_characters",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="\u4e2d\u6587",
        msg="$out should accept CJK characters as a database name",
    ),
    OutTestCase(
        "db_punctuation",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="a!@#b",
        msg="$out should accept punctuation in a database name",
    ),
    OutTestCase(
        "db_single_character",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="a",
        msg="$out should accept a single-character database name",
    ),
    OutTestCase(
        "db_digits_only",
        docs=[{"_id": 1}],
        target_coll="target",
        target_db="123",
        msg="$out should accept a digits-only database name",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_DATABASE_NAME_ACCEPTANCE_TESTS))
def test_out_database_name_acceptance(collection, test_case: OutTestCase):
    """Test $out accepts various character classes as database names."""
    populate_collection(collection, test_case)
    db_name = test_case.target_db  # type: ignore[arg-type]
    target_coll_name = test_case.resolve_target_coll(collection)
    client = collection.database.client
    client.drop_database(db_name)
    try:
        out_stage = test_case.build_out_stage(collection)
        execute_command(
            collection,
            {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
        )
        target_db = client[db_name]
        result = execute_command(
            target_db[target_coll_name],
            {"listCollections": 1, "filter": {"name": target_coll_name}},
        )
        raw_doc = cast(dict, result)["cursor"]["firstBatch"][0]
        assertSuccess(
            result,
            [
                {
                    "name": target_coll_name,
                    "type": "collection",
                    "options": {},
                    "info": raw_doc["info"],
                    "idIndex": raw_doc["idIndex"],
                }
            ],
            msg=test_case.msg,
        )
    finally:
        client.drop_database(db_name)


# Property [Collection Creation]: $out creates a new collection when the
# target does not exist, and an empty pipeline result creates an empty
# collection or empties an existing one.
#
# Property [Collection Replacement - Atomic Replace]: an existing collection
# is atomically replaced with the new pipeline results upon $out completion.
#
# Property [Collection Replacement - Failure Rollback]: if the aggregation
# fails during $out, the pre-existing collection and its documents are
# unchanged.
OUT_FIND_AFTER_OUT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "new_collection_created",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="creation_new_target",
        expected=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        msg="$out should create a new collection when the target does not exist",
    ),
    OutTestCase(
        "empty_pipeline_empties_existing_collection",
        docs=[],
        target_coll="creation_emptied_target",
        setup=lambda c: c.database[f"{c.name}_creation_emptied_target"].insert_one(
            {"_id": 99, "old": True}
        ),
        expected=[],
        msg="$out with no documents should empty an existing collection",
    ),
    OutTestCase(
        "replacement_atomic",
        docs=[{"_id": 10, "new": True}, {"_id": 20, "new": True}],
        target_coll="replacement_atomic_target",
        setup=lambda c: c.database[f"{c.name}_replacement_atomic_target"].insert_many(
            [{"_id": 1, "old": True}, {"_id": 2, "old": True}]
        ),
        expected=[{"_id": 10, "new": True}, {"_id": 20, "new": True}],
        msg="$out should replace existing documents with new pipeline results",
    ),
    OutTestCase(
        "failure_rollback_docs",
        docs=[{"_id": 10, "x": 1}, {"_id": 20, "x": 1}],
        target_coll="replacement_fail_target",
        setup=lambda c: (
            c.database[f"{c.name}_replacement_fail_target"].insert_many(
                [{"_id": 1, "x": 1}, {"_id": 2, "x": 2}]
            ),
            c.database[f"{c.name}_replacement_fail_target"].create_index("x", unique=True),
        ),
        expected=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        msg="$out failure should leave pre-existing documents unchanged",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_FIND_AFTER_OUT_TESTS))
def test_out_find_after_out(collection, test_case: OutTestCase):
    """Test $out write behavior verified via find on the target collection."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    target_coll_name = test_case.resolve_target_coll(collection)
    result = execute_command(
        collection,
        {"find": target_coll_name, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


@pytest.mark.aggregate
def test_out_empty_pipeline_creates_collection(collection):
    """Test $out with no documents creates an empty collection."""
    target_coll = f"{collection.name}_creation_empty_target"
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$out": target_coll}], "cursor": {}},
    )
    # Use listCollections because find on a non-existent collection also
    # returns empty, which would make this test pass even without creation.
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": target_coll}, "nameOnly": True},
    )
    assertSuccess(
        result,
        [{"name": target_coll, "type": "collection"}],
        msg="$out with no documents should create an empty collection",
    )


# Property [Database Creation]: $out creates a new database when the output
# database does not exist.


@pytest.mark.aggregate
def test_out_database_creation(collection):
    """Test $out creates a new database when the output database does not exist."""
    collection.insert_many([{"_id": 1, "value": 10}])
    db = collection.database
    client = db.client
    cross_db_name = db.name + "_cross"
    target_coll_name = f"{collection.name}_creation_cross_db_target"
    client.drop_database(cross_db_name)
    try:
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [{"$out": {"db": cross_db_name, "coll": target_coll_name}}],
                "cursor": {},
            },
        )
        target_coll = client[cross_db_name][target_coll_name]
        result = execute_command(
            target_coll,
            {"find": target_coll_name, "filter": {}},
        )
        assertSuccess(
            result,
            [{"_id": 1, "value": 10}],
            msg="$out should create a new database when the output database does not exist",
        )
    finally:
        client.drop_database(cross_db_name)


# Property [Collection Replacement - Self-Replacement]: writing to the same
# collection as the input succeeds and the collection contains the transformed
# results.
OUT_REPLACEMENT_SELF_TESTS: list[OutTestCase] = [
    OutTestCase(
        "replacement_self",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        expected=[
            {"_id": 1, "value": 10, "doubled": 20},
            {"_id": 2, "value": 20, "doubled": 40},
        ],
        msg="$out self-replacement should contain transformed results",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_REPLACEMENT_SELF_TESTS))
def test_out_replacement_self(collection, test_case: OutTestCase):
    """Test $out self-replacement writes transformed results back to the source."""
    populate_collection(collection, test_case)
    pipeline = [
        {"$addFields": {"doubled": {"$multiply": ["$value", 2]}}},
        {"$out": collection.name},
    ]
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": pipeline, "cursor": {}},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {}, "sort": {"_id": 1}}
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Collection Replacement - Index Preservation]: indexes from the
# previous collection are preserved after $out replaces its contents.
#
# Property [Collection Replacement - Failure Rollback]: if the aggregation
# fails during $out, the pre-existing collection and its indexes are unchanged.
OUT_INDEX_AFTER_OUT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "replacement_preserves_indexes",
        docs=[{"_id": 10, "x": 100}, {"_id": 20, "x": 200}],
        target_coll="replacement_idx_target",
        setup=lambda c: (
            c.database[f"{c.name}_replacement_idx_target"].insert_one({"_id": 1, "x": 1}),
            c.database[f"{c.name}_replacement_idx_target"].create_index(
                "x", name="x_idx", unique=True
            ),
        ),
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"x": 1}, "name": "x_idx", "unique": True},
        ],
        msg="$out should preserve indexes from the previous collection",
    ),
    OutTestCase(
        "failure_rollback_indexes",
        docs=[{"_id": 10, "x": 1}, {"_id": 20, "x": 1}],
        target_coll="replacement_fail_target",
        setup=lambda c: (
            c.database[f"{c.name}_replacement_fail_target"].insert_many(
                [{"_id": 1, "x": 1}, {"_id": 2, "x": 2}]
            ),
            c.database[f"{c.name}_replacement_fail_target"].create_index("x", unique=True),
        ),
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"x": 1}, "name": "x_1", "unique": True},
        ],
        msg="$out failure should leave pre-existing indexes unchanged",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_INDEX_AFTER_OUT_TESTS))
def test_out_index_after_out(collection, test_case: OutTestCase):
    """Test $out index behavior verified via listIndexes on the target collection."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    out_stage = test_case.build_out_stage(collection)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [out_stage], "cursor": {}},
    )
    target_coll_name = test_case.resolve_target_coll(collection)
    result = execute_command(
        collection,
        {"listIndexes": target_coll_name},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg, ignore_doc_order=True)


# Property [Temporary Collection]: $out uses a temporary collection during
# execution and cleans it up after completion.


@pytest.mark.aggregate
def test_out_temp_collection_observed(collection):
    """Test $out uses a temporary collection during execution."""
    collection.insert_many([{"_id": i, "value": i} for i in range(10_000)])
    db = collection.database
    target_coll = f"{collection.name}_creation_temp_target"

    found_tmp: list[str] = []
    stop = threading.Event()

    def poll_collections() -> None:
        while not stop.is_set():
            try:
                names = db.list_collection_names()
                for name in names:
                    if name.startswith("tmp.agg_out."):
                        found_tmp.append(name)
                        return
            except Exception:
                pass

    t = threading.Thread(target=poll_collections, daemon=True)
    t.start()

    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": target_coll}],
            "cursor": {},
        },
    )

    stop.set()
    t.join(timeout=5)

    assertSuccess(
        len(found_tmp) > 0,
        True,
        raw_res=True,
        msg="$out should use a temp collection during execution",
    )


@pytest.mark.aggregate
def test_out_temp_collection_cleaned_up(collection):
    """Test $out cleans up the temporary collection after completion."""
    collection.insert_many([{"_id": i, "value": i} for i in range(10_000)])
    db = collection.database
    target_coll = f"{collection.name}_creation_temp_target"

    found_tmp: list[str] = []
    stop = threading.Event()

    def poll_collections() -> None:
        while not stop.is_set():
            try:
                names = db.list_collection_names()
                for name in names:
                    if name.startswith("tmp.agg_out."):
                        found_tmp.append(name)
                        return
            except Exception:
                pass

    t = threading.Thread(target=poll_collections, daemon=True)
    t.start()

    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$out": target_coll}],
            "cursor": {},
        },
    )

    stop.set()
    t.join(timeout=5)

    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": {"$regex": "^tmp\\.agg_out\\."}}},
    )
    assertSuccess(
        result,
        [],
        msg="$out should clean up temp collection after completion",
    )
