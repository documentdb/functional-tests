"""Tests for $out stage - individual write properties."""

from __future__ import annotations

from datetime import datetime
from typing import cast

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

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

# Property [Write Behavior - Auto-Generated _id]: documents with _id removed
# via a pipeline stage receive auto-generated ObjectId _id values in the
# output collection.
OUT_AUTO_GENERATED_ID_TESTS: list[OutTestCase] = [
    OutTestCase(
        "auto_id",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="write_auto_id_target",
        pipeline=[{"$unset": "_id"}, {"$out": "write_auto_id_target"}],
        expected=2,
        msg="$out should auto-generate ObjectId _id when _id is removed",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_AUTO_GENERATED_ID_TESTS))
def test_out_auto_generated_id(collection, test_case: OutTestCase):
    """Test $out auto-generates ObjectId _id when _id is removed."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    # Filter by _id type to confirm auto-generated ObjectIds.
    result = execute_command(
        collection,
        {
            "aggregate": test_case.target_coll,
            "pipeline": [
                {"$match": {"_id": {"$type": "objectId"}}},
                {"$count": "n"},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"n": test_case.expected}], msg=test_case.msg)


# Property [Write Behavior - Empty Cursor]: the aggregation cursor returned
# by a pipeline ending with $out contains an empty result list.
OUT_EMPTY_CURSOR_TESTS: list[OutTestCase] = [
    OutTestCase(
        "empty_cursor",
        docs=[{"_id": 1, "value": 10}],
        target_coll="write_cursor_target",
        pipeline=[{"$out": "write_cursor_target"}],
        expected=[],
        msg="$out aggregation cursor should return an empty result list",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_EMPTY_CURSOR_TESTS))
def test_out_empty_cursor(collection, test_case: OutTestCase):
    """Test $out returns an empty cursor result."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Write Behavior - Explain No Write]: explain does not perform the
# write - the target collection is not created or modified.
OUT_EXPLAIN_NO_WRITE_TESTS: list[OutTestCase] = [
    OutTestCase(
        "explain_no_write",
        docs=[{"_id": 1, "value": 10}],
        target_coll="write_explain_target",
        pipeline=[{"$out": "write_explain_target"}],
        expected=[],
        msg="explain with $out should not create the target collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_EXPLAIN_NO_WRITE_TESTS))
def test_out_explain_no_write(collection, test_case: OutTestCase):
    """Test explain with $out does not create or modify the target collection."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
            "explain": True,
        },
    )
    result = execute_command(
        collection,
        {"listCollections": 1, "filter": {"name": test_case.target_coll}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


OUT_EXPLAIN_NO_MODIFY_TESTS: list[OutTestCase] = [
    OutTestCase(
        "explain_no_modify",
        docs=[{"_id": 10, "new": True}],
        target_coll="write_explain_existing_target",
        pipeline=[{"$out": "write_explain_existing_target"}],
        setup=lambda c: c.database["write_explain_existing_target"].insert_many(
            [{"_id": 1, "old": True}, {"_id": 2, "old": True}]
        ),
        expected=[{"_id": 1, "old": True}, {"_id": 2, "old": True}],
        msg="explain with $out should not modify existing target collection",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_EXPLAIN_NO_MODIFY_TESTS))
def test_out_explain_no_modify(collection, test_case: OutTestCase):
    """Test explain with $out does not modify an existing target collection."""
    populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(collection)
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
            "explain": True,
        },
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Write Behavior - Idempotent]: running the same $out pipeline to
# the same target twice produces the same result in the target collection.
OUT_IDEMPOTENT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "idempotent",
        docs=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        target_coll="write_idempotent_target",
        pipeline=[{"$out": "write_idempotent_target"}],
        expected=[{"_id": 1, "value": 10}, {"_id": 2, "value": 20}],
        msg="$out should produce the same result when run twice to the same target",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_IDEMPOTENT_TESTS))
def test_out_idempotent(collection, test_case: OutTestCase):
    """Test $out is idempotent when run twice to the same target."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "sort": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Write Behavior - BSON Round-Trip]: all BSON types representable
# by pymongo round-trip through $out without modification.
OUT_BSON_ROUND_TRIP_TESTS: list[OutTestCase] = [
    OutTestCase(
        "bson_round_trip",
        docs=[
            {
                "_id": 1,
                "double_val": 3.14,
                "string_val": "hello",
                "object_val": {"nested": True},
                "array_val": [1, 2, 3],
                "binary_val": Binary(b"\x01\x02\x03"),
                "objectid_val": ObjectId("507f1f77bcf86cd799439011"),
                "bool_val": True,
                "date_val": datetime(2024, 1, 1),
                "null_val": None,
                "regex_val": Regex("abc", "i"),
                "int32_val": 42,
                "timestamp_val": Timestamp(1_234_567_890, 1),
                "int64_val": Int64(9_876_543_210),
                "decimal128_val": Decimal128("123.456"),
                "minkey_val": MinKey(),
                "maxkey_val": MaxKey(),
                "code_val": Code("function() {}"),
            }
        ],
        target_coll="write_bson_target",
        pipeline=[{"$out": "write_bson_target"}],
        msg="all BSON types should round-trip through $out without modification",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_BSON_ROUND_TRIP_TESTS))
def test_out_bson_round_trip(collection, test_case: OutTestCase):
    """Test all BSON types round-trip through $out without modification."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    source_result = execute_command(
        collection,
        {"find": collection.name, "filter": {}},
    )
    target_result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}},
    )
    assertSuccess(
        target_result,
        cast(dict, source_result)["cursor"]["firstBatch"],
        msg=test_case.msg,
    )


# Property [Write Behavior - Large Documents]: documents up to 15 MB are
# written successfully through $out.
OUT_LARGE_DOCUMENT_TESTS: list[OutTestCase] = [
    OutTestCase(
        "large_doc",
        docs=[{"_id": 1, "data": "x" * (15 * 1_024 * 1_024)}],
        target_coll="write_large_target",
        pipeline=[{"$out": "write_large_target"}],
        expected=[{"_id": 1}],
        msg="$out should successfully write a 15 MB document",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OUT_LARGE_DOCUMENT_TESTS))
def test_out_large_document(collection, test_case: OutTestCase):
    """Test $out writes documents up to 15 MB successfully."""
    populate_collection(collection, test_case)
    execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    result = execute_command(
        collection,
        {"find": test_case.target_coll, "filter": {}, "projection": {"_id": 1}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [No Unicode Normalization - Collections]: precomposed and combining
# forms of the same character create separate, distinct collections - no
# Unicode normalization is applied to collection names.


@pytest.mark.aggregate
def test_out_no_unicode_normalization_precomposed(collection):
    """Test $out writes to precomposed Unicode collection name correctly."""
    collection.insert_many([{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}])
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 1}}, {"$out": "\u00e9"}],  # precomposed e-acute
            "cursor": {},
        },
    )
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 2}}, {"$out": "\u0065\u0301"}],  # combining e-acute
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {"find": "\u00e9", "filter": {}},
    )
    assertSuccess(
        result,
        [{"_id": 1, "form": "precomposed"}],
        msg="$out should write to precomposed Unicode collection name",
    )


@pytest.mark.aggregate
def test_out_no_unicode_normalization_combining(collection):
    """Test $out writes to combining Unicode collection name correctly."""
    collection.insert_many([{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}])
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 1}}, {"$out": "\u00e9"}],  # precomposed e-acute
            "cursor": {},
        },
    )
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 2}}, {"$out": "\u0065\u0301"}],  # combining e-acute
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {"find": "\u0065\u0301", "filter": {}},
    )
    assertSuccess(
        result,
        [{"_id": 2, "form": "combining"}],
        msg="$out should write to combining Unicode collection name",
    )


@pytest.mark.aggregate
def test_out_no_unicode_normalization_distinct_colls(collection):
    """Test $out creates separate collections for precomposed and combining Unicode forms."""
    collection.insert_many([{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}])
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 1}}, {"$out": "\u00e9"}],  # precomposed e-acute
            "cursor": {},
        },
    )
    execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$match": {"_id": 2}}, {"$out": "\u0065\u0301"}],  # combining e-acute
            "cursor": {},
        },
    )
    result = execute_command(
        collection,
        {
            "listCollections": 1,
            "filter": {"name": {"$in": ["\u00e9", "\u0065\u0301"]}},
            "nameOnly": True,
        },
    )
    assertSuccess(
        result,
        [
            {"name": "\u00e9", "type": "collection"},
            {"name": "\u0065\u0301", "type": "collection"},
        ],
        msg="$out should create separate collections for precomposed and combining forms",
        ignore_doc_order=True,
    )


# Property [No Unicode Normalization - Databases]: precomposed and combining
# forms of the same character create separate, distinct databases - no Unicode
# normalization is applied to database names.


@pytest.mark.aggregate
def test_out_no_unicode_normalization_db_precomposed(collection):
    """Test $out writes to precomposed Unicode database name correctly."""
    collection.insert_many([{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}])
    client = collection.database.client
    client.drop_database("\u00e9")
    client.drop_database("\u0065\u0301")
    try:
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 1}},
                    {"$out": {"db": "\u00e9", "coll": "target"}},  # precomposed e-acute
                ],
                "cursor": {},
            },
        )
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 2}},
                    {"$out": {"db": "\u0065\u0301", "coll": "target"}},  # combining e-acute
                ],
                "cursor": {},
            },
        )
        result = execute_command(
            client["\u00e9"]["target"],
            {"find": "target", "filter": {}},
        )
        assertSuccess(
            result,
            [{"_id": 1, "form": "precomposed"}],
            msg="$out should write to precomposed Unicode database name",
        )
    finally:
        client.drop_database("\u00e9")
        client.drop_database("\u0065\u0301")


@pytest.mark.aggregate
def test_out_no_unicode_normalization_db_combining(collection):
    """Test $out writes to combining Unicode database name correctly."""
    collection.insert_many([{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}])
    client = collection.database.client
    client.drop_database("\u00e9")
    client.drop_database("\u0065\u0301")
    try:
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 1}},
                    {"$out": {"db": "\u00e9", "coll": "target"}},  # precomposed e-acute
                ],
                "cursor": {},
            },
        )
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 2}},
                    {"$out": {"db": "\u0065\u0301", "coll": "target"}},  # combining e-acute
                ],
                "cursor": {},
            },
        )
        result = execute_command(
            client["\u0065\u0301"]["target"],
            {"find": "target", "filter": {}},
        )
        assertSuccess(
            result,
            [{"_id": 2, "form": "combining"}],
            msg="$out should write to combining Unicode database name",
        )
    finally:
        client.drop_database("\u00e9")
        client.drop_database("\u0065\u0301")


@pytest.mark.aggregate
def test_out_no_unicode_normalization_db_distinct(collection):
    """Test $out creates separate databases for precomposed and combining Unicode forms."""
    collection.insert_many([{"_id": 1, "form": "precomposed"}, {"_id": 2, "form": "combining"}])
    client = collection.database.client
    client.drop_database("\u00e9")
    client.drop_database("\u0065\u0301")
    try:
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 1}},
                    {"$out": {"db": "\u00e9", "coll": "target"}},  # precomposed e-acute
                ],
                "cursor": {},
            },
        )
        execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [
                    {"$match": {"_id": 2}},
                    {"$out": {"db": "\u0065\u0301", "coll": "target"}},  # combining e-acute
                ],
                "cursor": {},
            },
        )
        # Verify precomposed database has exactly 1 document (not 2, which
        # would mean both forms mapped to the same database).
        result = execute_command(
            client["\u00e9"]["target"],
            {
                "aggregate": "target",
                "pipeline": [{"$count": "n"}],
                "cursor": {},
            },
        )
        assertSuccess(
            result,
            [{"n": 1}],
            msg="$out should create separate databases for precomposed and combining forms",
        )
    finally:
        client.drop_database("\u00e9")
        client.drop_database("\u0065\u0301")
