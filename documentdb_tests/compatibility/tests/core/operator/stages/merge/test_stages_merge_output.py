"""Tests for $merge output target creation and output behavior."""

from __future__ import annotations

import uuid

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.merge.utils.merge_common import (
    TARGET,
    MergeTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
    assertSuccess,
)
from documentdb_tests.framework.executor import (
    execute_command,
)
from documentdb_tests.framework.parametrize import (
    pytest_params,
)
from documentdb_tests.framework.property_checks import (
    IsType,
)

# Property [Collection Creation]: when the output collection does not exist,
# $merge creates it upon writing the first document; when no documents are
# written (empty source, discard, or fail with no unmatched), the collection
# is not created.
MERGE_COLLECTION_CREATION_TESTS: list[MergeTestCase] = [
    MergeTestCase(
        "creation_target_created",
        docs=[{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        pipeline=[{"$merge": TARGET}],
        expected=[{"name": TARGET, "type": "collection"}],
        msg="$merge should create the target collection when it does not exist",
    ),
    MergeTestCase(
        "creation_empty_source_no_create",
        docs=[],
        pipeline=[{"$merge": TARGET}],
        expected=[],
        msg="$merge should not create the target collection when the source is empty",
    ),
    MergeTestCase(
        "creation_discard_no_create",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "discard"}}],
        expected=[],
        msg="$merge should not create the target collection when whenNotMatched is discard",
    ),
    MergeTestCase(
        "creation_fail_no_unmatched_no_create",
        docs=[],
        pipeline=[{"$merge": {"into": TARGET, "whenNotMatched": "fail"}}],
        expected=[],
        msg="$merge should not create the target when source is empty and whenNotMatched is fail",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(MERGE_COLLECTION_CREATION_TESTS))
def test_stages_merge_collection_creation(collection, test_case: MergeTestCase):
    """Test $merge collection creation behavior."""
    target = test_case.prepare(collection)

    execute_command(collection, test_case.build_command(collection, target))

    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": target}, "nameOnly": True},
    )
    expected_list = [
        {k: target if v is TARGET else v for k, v in doc.items()} for doc in test_case.expected
    ]
    assertSuccess(result, expected_list, msg=test_case.msg)


# Property [Database Creation]: when the output database does not exist,
# $merge creates it.
@pytest.mark.aggregate
def test_stages_merge_database_creation(collection):
    """Test $merge creates a new database when the output database does not exist."""
    collection.insert_many([{"_id": 1, "a": 10}])
    db = collection.database
    client = db.client
    cross_db_name = f"{db.name}_merge_cross_{uuid.uuid4().hex[:8]}"
    target_coll_name = f"{collection.name}_cross_db_target"
    client.drop_database(cross_db_name)
    try:
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [{"$merge": {"into": {"db": cross_db_name, "coll": target_coll_name}}}],
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
            [{"_id": 1, "a": 10}],
            msg="$merge should create a new database when the output database does not exist",
        )
    finally:
        client.drop_database(cross_db_name)


# Property [Cross-Database Output]: $merge can write to a collection in a
# different database using the document form {db: <db>, coll: <collection>}.
@pytest.mark.aggregate
def test_stages_merge_cross_database_output(collection):
    """Test $merge writes to a collection in a different database."""
    collection.insert_many([{"_id": 1, "a": 10}, {"_id": 2, "a": 20}])
    db = collection.database
    client = db.client
    cross_db_name = f"{db.name}_merge_xdb_{uuid.uuid4().hex[:8]}"
    target_coll_name = f"{collection.name}_xdb_target"
    client.drop_database(cross_db_name)
    try:
        client[cross_db_name].create_collection(target_coll_name)
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [{"$merge": {"into": {"db": cross_db_name, "coll": target_coll_name}}}],
                "cursor": {},
            },
        )
        target_coll = client[cross_db_name][target_coll_name]
        result = execute_command(
            target_coll,
            {"find": target_coll_name, "filter": {}, "sort": {"_id": 1}},
        )
        assertSuccess(
            result,
            [{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
            msg="$merge should write documents to a collection in a different database",
        )
    finally:
        client.drop_database(cross_db_name)


# Property [_id Field Generation]: when _id is not present in a document
# from the aggregation results, $merge generates it automatically as an
# ObjectId.
@pytest.mark.aggregate
def test_stages_merge_id_field_generation(collection):
    """Test $merge generates _id as ObjectId when not present in results."""
    collection.insert_many([{"_id": 1, "a": 10}, {"_id": 2, "b": 20}])
    db = collection.database
    target = f"{collection.name}_id_gen"
    db.drop_collection(target)

    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "a": 1, "b": 1}},
                {"$merge": {"into": target}},
            ],
            "cursor": {},
        },
    )

    result = execute_command(
        collection,
        {"find": target, "filter": {}},
    )
    assertResult(
        result,
        expected={"_id": IsType("objectId")},
        msg="$merge should generate _id as ObjectId when not present in aggregation results",
    )


# Property [Self-Merge]: $merge can output to the same collection that is
# being aggregated.
@pytest.mark.aggregate
def test_stages_merge_self_merge(collection):
    """Test $merge can output to the same collection being aggregated."""
    collection.insert_many([{"_id": 1, "a": 10}, {"_id": 2, "a": 20}])

    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$addFields": {"merged": True}},
                {"$merge": {"into": collection.name, "whenMatched": "replace"}},
            ],
            "cursor": {},
        },
    )

    result = execute_command(
        collection,
        {"find": collection.name, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": 10, "merged": True}, {"_id": 2, "a": 20, "merged": True}],
        msg="$merge should be able to output to the same collection being aggregated",
    )


# Property [Capped Collection Target]: $merge can write to a capped
# collection (unlike $out which rejects capped collections).
@pytest.mark.aggregate
def test_stages_merge_capped_collection_target(collection):
    """Test $merge can write to a capped collection."""
    collection.insert_many([{"_id": 1, "a": 10}, {"_id": 2, "a": 20}])
    db = collection.database
    target = f"{collection.name}_capped_target"
    db.drop_collection(target)
    db.create_collection(target, capped=True, size=1_048_576)

    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": target}}],
            "cursor": {},
        },
    )

    result = execute_command(
        collection,
        {"find": target, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": 10}, {"_id": 2, "a": 20}],
        msg="$merge should write documents to a capped collection",
    )


# Property [Output Behavior]: $merge is a terminal stage that writes to the
# target collection but returns an empty cursor to the client; no documents
# from the pipeline appear in the aggregation result.
@pytest.mark.aggregate
def test_stages_merge_output_behavior(collection):
    """Test $merge returns an empty cursor even when documents are written."""
    db = collection.database
    target = f"{collection.name}_output_behavior"

    collection.insert_many([{"_id": 1, "a": 10}, {"_id": 2, "a": 20}])
    db.drop_collection(target)

    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$merge": {"into": target}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [],
        msg="$merge should return an empty cursor with no output documents",
    )
