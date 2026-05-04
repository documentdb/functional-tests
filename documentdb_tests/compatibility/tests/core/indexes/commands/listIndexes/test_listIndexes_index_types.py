"""
Tests for listIndexes command — index types, options, hidden indexes, and post-modification.

Covers various index types in output, index options, hidden index visibility,
and listIndexes behavior after index lifecycle operations.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

INDEX_TYPE_CASES: list[IndexTestCase] = [
    IndexTestCase(
        "ascending",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1"},
        ],
        msg="Ascending index should appear in listIndexes output",
    ),
    IndexTestCase(
        "descending",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": -1}, "name": "a_-1"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": -1}, "name": "a_-1"},
        ],
        msg="Descending index should appear in listIndexes output",
    ),
    IndexTestCase(
        "compound",
        doc=({"_id": 1, "a": 1, "b": 1},),
        setup_indexes=[{"key": {"a": 1, "b": -1}, "name": "a_1_b_-1"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1, "b": -1}, "name": "a_1_b_-1"},
        ],
        msg="Compound index should appear in listIndexes output",
    ),
    IndexTestCase(
        "unique",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1", "unique": True}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1", "unique": True},
        ],
        msg="Unique index should show unique: true",
    ),
    IndexTestCase(
        "sparse",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1", "sparse": True}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1", "sparse": True},
        ],
        msg="Sparse index should show sparse: true",
    ),
    IndexTestCase(
        "ttl",
        doc=({"_id": 1, "ts": None},),
        setup_indexes=[{"key": {"ts": 1}, "name": "ts_1", "expireAfterSeconds": 3600}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"ts": 1}, "name": "ts_1", "expireAfterSeconds": 3600},
        ],
        msg="TTL index should show expireAfterSeconds",
    ),
    IndexTestCase(
        "partial_filter",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "a_partial", "partialFilterExpression": {"a": {"$gt": 0}}}
        ],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"a": 1},
                "name": "a_partial",
                "partialFilterExpression": {"a": {"$gt": 0}},
            },
        ],
        msg="Partial filter index should show partialFilterExpression",
    ),
    IndexTestCase(
        "hashed",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": "hashed"}, "name": "a_hashed"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": "hashed"}, "name": "a_hashed"},
        ],
        msg="Hashed index should appear in listIndexes output",
    ),
    IndexTestCase(
        "2dsphere",
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},),
        setup_indexes=[{"key": {"loc": "2dsphere"}, "name": "loc_2dsphere"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"loc": "2dsphere"}, "name": "loc_2dsphere", "2dsphereIndexVersion": 3},
        ],
        msg="2dsphere index should appear in listIndexes output",
    ),
    IndexTestCase(
        "2d",
        doc=({"_id": 1, "loc": [0, 0]},),
        setup_indexes=[{"key": {"loc": "2d"}, "name": "loc_2d"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"loc": "2d"}, "name": "loc_2d"},
        ],
        msg="2d index should appear in listIndexes output",
    ),
    IndexTestCase(
        "wildcard",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"$**": 1}, "name": "wildcard"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"$**": 1}, "name": "wildcard"},
        ],
        msg="Wildcard index should appear in listIndexes output",
    ),
    IndexTestCase(
        "wildcard_with_projection",
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"$**": 1}, "name": "$**_1", "wildcardProjection": {"a": 1}}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"$**": 1}, "name": "$**_1", "wildcardProjection": {"a": 1}},
        ],
        msg="Wildcard index with wildcardProjection should appear in listIndexes output",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INDEX_TYPE_CASES))
def test_listIndexes_index_type(collection, test):
    """Test listIndexes shows correct output for various index types and options."""
    collection.insert_many(test.doc)
    execute_command(collection, {"createIndexes": collection.name, "indexes": test.setup_indexes})

    result = execute_command(collection, {"listIndexes": collection.name})

    assertSuccess(result, test.expected, msg=test.msg)


INDEX_FIRSTBATCH_CASES: list[IndexTestCase] = [
    IndexTestCase(
        "text",
        doc=({"_id": 1, "content": "hello world"},),
        setup_indexes=[{"key": {"content": "text"}, "name": "content_text"}],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"_fts": "text", "_ftsx": 1},
                "name": "content_text",
                "weights": {"content": 1},
                "default_language": "english",
                "language_override": "language",
                "textIndexVersion": 3,
            },
        ],
        msg="Text index should appear in listIndexes output",
    ),
    IndexTestCase(
        "collation",
        doc=({"_id": 1, "a": "hello"},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "a_collation", "collation": {"locale": "en", "strength": 2}}
        ],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"a": 1},
                "name": "a_collation",
                "collation": {
                    "locale": "en",
                    "caseLevel": False,
                    "caseFirst": "off",
                    "strength": 2,
                    "numericOrdering": False,
                    "alternate": "non-ignorable",
                    "maxVariable": "punct",
                    "normalization": False,
                    "backwards": False,
                    "version": "57.1",
                },
            },
        ],
        msg="Collation index should appear in output",
    ),
    IndexTestCase(
        "text_with_weights",
        doc=({"_id": 1, "title": "hello", "body": "world"},),
        setup_indexes=[
            {
                "key": {"title": "text", "body": "text"},
                "name": "text_weighted",
                "weights": {"title": 10, "body": 1},
            }
        ],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"_fts": "text", "_ftsx": 1},
                "name": "text_weighted",
                "weights": {"body": 1, "title": 10},
                "default_language": "english",
                "language_override": "language",
                "textIndexVersion": 3,
            },
        ],
        msg="Text index with weights should appear in output",
    ),
    IndexTestCase(
        "text_with_language",
        doc=({"_id": 1, "content": "hello", "lang": "en"},),
        setup_indexes=[
            {
                "key": {"content": "text"},
                "name": "text_lang",
                "default_language": "spanish",
                "language_override": "lang",
            }
        ],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"_fts": "text", "_ftsx": 1},
                "name": "text_lang",
                "weights": {"content": 1},
                "default_language": "spanish",
                "language_override": "lang",
                "textIndexVersion": 3,
            },
        ],
        msg="Text index with language options should appear in output",
    ),
    IndexTestCase(
        "2d_with_options",
        doc=({"_id": 1, "loc": [0, 0]},),
        setup_indexes=[
            {"key": {"loc": "2d"}, "name": "loc_2d_opts", "min": -100, "max": 100, "bits": 20}
        ],
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"loc": "2d"},
                "name": "loc_2d_opts",
                "bits": 20,
                "min": -100.0,
                "max": 100.0,
            },
        ],
        msg="2d index with options should appear in output",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INDEX_FIRSTBATCH_CASES))
def test_listIndexes_index_firstbatch(collection, test):
    """Test listIndexes includes indexes with server-generated fields in output."""
    collection.insert_many(test.doc)
    execute_command(collection, {"createIndexes": collection.name, "indexes": test.setup_indexes})

    result = execute_command(collection, {"listIndexes": collection.name})

    assertSuccess(result, test.expected, msg=test.msg)


def test_listIndexes_hidden_index_shows_hidden_true(collection):
    """Test listIndexes shows hidden: true for hidden index."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )

    result = execute_command(collection, {"listIndexes": collection.name})

    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1", "hidden": True},
        ],
    )


def test_listIndexes_unhidden_index(collection):
    """Test listIndexes after unhiding index does not show hidden field."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )

    result = execute_command(collection, {"listIndexes": collection.name})

    assertSuccess(
        result,
        [{"v": 2, "key": {"_id": 1}, "name": "_id_"}, {"v": 2, "key": {"a": 1}, "name": "a_1"}],
    )


def test_listIndexes_hidden_index_not_omitted(collection):
    """Test listIndexes returns hidden indexes (not omitted from results)."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )

    result = execute_command(collection, {"listIndexes": collection.name})

    assertSuccess(
        result,
        [
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_1", "hidden": True},
            {"v": 2, "key": {"b": 1}, "name": "b_1"},
        ],
    )


def test_listIndexes_after_create_drop(collection):
    """Test listIndexes after create then drop index shows dropped index gone."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="a_1")
    collection.drop_index("a_1")

    result = execute_command(collection, {"listIndexes": collection.name})

    assertSuccess(result, [{"v": 2, "key": {"_id": 1}, "name": "_id_"}])
