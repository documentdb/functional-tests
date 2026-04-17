"""
Tests for $meta "indexKey" behavior.

Covers: single-field index, compound index, collection scan (no index), and $addFields.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def test_meta_indexkey_single_field_index(collection):
    """Test $meta indexKey in $project with single-field index returns object with index key."""
    collection.create_index([("a", 1)])
    collection.insert_many(
        [
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"a": {"$gt": 0}}},
                {"$project": {"_id": 1, "ik": {"$meta": "indexKey"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "ik": {"a": 10}},
            {"_id": 2, "ik": {"a": 30}},
        ],
        ignore_doc_order=True,
    )


def test_meta_indexkey_compound_index(collection):
    """Test $meta indexKey with compound index returns object with all index key fields."""
    collection.create_index([("a", 1), ("b", 1)])
    collection.insert_many(
        [
            {"_id": 1, "a": 10, "b": 20},
            {"_id": 2, "a": 30, "b": 40},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"a": {"$gt": 0}, "b": {"$gt": 0}}},
                {"$project": {"_id": 1, "ik": {"$meta": "indexKey"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "ik": {"a": 10, "b": 20}},
            {"_id": 2, "ik": {"a": 30, "b": 40}},
        ],
        ignore_doc_order=True,
    )


def test_meta_indexkey_no_index_field_absent(collection):
    """Test $meta indexKey when no index is used — field is absent from output."""
    collection.insert_many(
        [
            {"_id": 1, "a": 10},
            {"_id": 2, "a": 20},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 1, "ik": {"$meta": "indexKey"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1},
            {"_id": 2},
        ],
        ignore_doc_order=True,
    )


def test_meta_indexkey_text_index(collection):
    """Test $meta indexKey with a text index — field is absent since indexKey is for non-text indexes."""  # noqa: E501
    collection.create_index([("content", "text")])
    collection.insert_one({"_id": 1, "content": "apple banana"})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "apple"}}},
                {"$project": {"_id": 1, "ik": {"$meta": "indexKey"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1}])


def test_meta_indexkey_multikey_index(collection):
    """Test $meta indexKey with a multikey index (array field) returns the matched array element key."""  # noqa: E501
    collection.create_index([("tags", 1)])
    collection.insert_many(
        [
            {"_id": 1, "tags": ["apple", "banana"]},
            {"_id": 2, "tags": ["cherry"]},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"tags": "apple"}},
                {"$project": {"_id": 1, "ik": {"$meta": "indexKey"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "ik": {"tags": "apple"}}])


def test_meta_indexkey_sparse_index_matching_doc(collection):
    """Test $meta indexKey with sparse index returns key for documents that have the field."""
    collection.create_index([("a", 1)], sparse=True)
    collection.insert_many(
        [
            {"_id": 1, "a": 10},
            {"_id": 2},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"a": {"$gt": 0}}},
                {"$project": {"_id": 1, "ik": {"$meta": "indexKey"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "ik": {"a": 10}}])


def test_meta_indexkey_hashed_index(collection):
    """Test $meta indexKey with hashed index returns a long (int64) hash value.

    Not the original value.
    """
    collection.create_index([("a", "hashed")])
    collection.insert_one({"_id": 1, "a": 10})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"a": 10}},
                # $addFields is needed to access the type of indexKey
                {"$addFields": {"ik": {"$meta": "indexKey"}}},
                {"$project": {"_id": 1, "ik_a_type": {"$type": "$ik.a"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 1, "ik_a_type": "long"}])
