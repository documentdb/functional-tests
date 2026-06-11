"""
Tests for dropIndexes command — dropping various index types.

Covers single field, text, 2d, 2dsphere, hashed, TTL, unique, sparse,
wildcard, wildcard projection, collated, partial filter expression, and
hidden indexes by name and by spec. Also covers disambiguation when
multiple indexes share the same key pattern with different options.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertResult,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import (
    AMBIGUOUS_INDEX_KEY_PATTERN_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DROP_INDEX_TYPE_CASES: list[IndexTestCase] = [
    IndexTestCase(
        "text_by_name",
        indexes=("text_idx",),
        doc=({"_id": 1, "content": "hello world"},),
        setup_indexes=[{"key": {"content": "text"}, "name": "text_idx"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop text index by name",
    ),
    IndexTestCase(
        "2dsphere_by_name",
        indexes=("geo_idx",),
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},),
        setup_indexes=[{"key": {"loc": "2dsphere"}, "name": "geo_idx"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop 2dsphere index by name",
    ),
    IndexTestCase(
        "2dsphere_by_spec",
        indexes=({"loc": "2dsphere"},),
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}},),
        setup_indexes=[{"key": {"loc": "2dsphere"}, "name": "loc_2dsphere"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop 2dsphere index by spec",
    ),
    IndexTestCase(
        "hashed_by_name",
        indexes=("hash_idx",),
        doc=({"_id": 1, "key": "value"},),
        setup_indexes=[{"key": {"key": "hashed"}, "name": "hash_idx"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop hashed index by name",
    ),
    IndexTestCase(
        "hashed_by_spec",
        indexes=({"key": "hashed"},),
        doc=({"_id": 1, "key": "value"},),
        setup_indexes=[{"key": {"key": "hashed"}, "name": "key_hashed"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop hashed index by spec",
    ),
    IndexTestCase(
        "ttl_by_name",
        indexes=("ttl_idx",),
        doc=({"_id": 1, "createdAt": None},),
        setup_indexes=[{"key": {"createdAt": 1}, "name": "ttl_idx", "expireAfterSeconds": 3600}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop TTL index by name",
    ),
    IndexTestCase(
        "ttl_by_spec",
        indexes=({"createdAt": 1},),
        doc=({"_id": 1, "createdAt": None},),
        setup_indexes=[
            {"key": {"createdAt": 1}, "name": "createdAt_1", "expireAfterSeconds": 3600}
        ],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop TTL index by spec",
    ),
    IndexTestCase(
        "unique_by_name",
        indexes=("unique_idx",),
        doc=({"_id": 1, "email": "test@test.com"},),
        setup_indexes=[{"key": {"email": 1}, "name": "unique_idx", "unique": True}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop unique index by name",
    ),
    IndexTestCase(
        "unique_by_spec",
        indexes=({"email": 1},),
        doc=({"_id": 1, "email": "test@test.com"},),
        setup_indexes=[{"key": {"email": 1}, "name": "email_1", "unique": True}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop unique index by spec",
    ),
    IndexTestCase(
        "sparse_by_name",
        indexes=("sparse_idx",),
        doc=({"_id": 1, "opt": "value"},),
        setup_indexes=[{"key": {"opt": 1}, "name": "sparse_idx", "sparse": True}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop sparse index by name",
    ),
    IndexTestCase(
        "sparse_by_spec",
        indexes=({"opt": 1},),
        doc=({"_id": 1, "opt": "value"},),
        setup_indexes=[{"key": {"opt": 1}, "name": "opt_1", "sparse": True}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop sparse index by spec",
    ),
    IndexTestCase(
        "wildcard_by_name",
        indexes=("wildcard_idx",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"$**": 1}, "name": "wildcard_idx"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop wildcard index by name",
    ),
    IndexTestCase(
        "wildcard_by_spec",
        indexes=({"$**": 1},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"$**": 1}, "name": "$**_1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop wildcard index by spec",
    ),
    IndexTestCase(
        "partial_filter_by_name",
        indexes=("partial_idx",),
        doc=({"_id": 1, "a": 1, "status": "active"},),
        setup_indexes=[
            {
                "key": {"a": 1},
                "name": "partial_idx",
                "partialFilterExpression": {"status": "active"},
            }
        ],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop partial filter index by name",
    ),
    IndexTestCase(
        "partial_filter_by_spec",
        indexes=({"a": 1},),
        doc=({"_id": 1, "a": 1, "status": "active"},),
        setup_indexes=[
            {
                "key": {"a": 1},
                "name": "a_1",
                "partialFilterExpression": {"status": "active"},
            }
        ],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop partial filter index by spec",
    ),
    IndexTestCase(
        "2d_by_name",
        indexes=("2d_idx",),
        doc=({"_id": 1, "loc": [40, 5]},),
        setup_indexes=[{"key": {"loc": "2d"}, "name": "2d_idx"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop 2d index by name",
    ),
    IndexTestCase(
        "2d_by_spec",
        indexes=({"loc": "2d"},),
        doc=({"_id": 1, "loc": [40, 5]},),
        setup_indexes=[{"key": {"loc": "2d"}, "name": "loc_2d"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop 2d index by spec",
    ),
    IndexTestCase(
        "wildcard_projection_by_name",
        indexes=("wp_idx",),
        doc=({"_id": 1, "a": 1, "b": 2},),
        setup_indexes=[{"key": {"$**": 1}, "name": "wp_idx", "wildcardProjection": {"a": 1}}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop wildcard projection index by name",
    ),
    IndexTestCase(
        "wildcard_projection_by_spec",
        indexes=({"$**": 1},),
        doc=({"_id": 1, "a": 1, "b": 2},),
        setup_indexes=[{"key": {"$**": 1}, "name": "$**_1", "wildcardProjection": {"a": 1}}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop wildcard projection index by spec",
    ),
    IndexTestCase(
        "collated_by_name",
        indexes=("collated_idx",),
        doc=({"_id": 1, "a": "hello"},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "collated_idx", "collation": {"locale": "en", "strength": 2}}
        ],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop collated index by name",
    ),
    IndexTestCase(
        "collated_by_spec",
        indexes=({"a": 1},),
        doc=({"_id": 1, "a": "hello"},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "a_1", "collation": {"locale": "en", "strength": 2}}
        ],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop collated index by spec",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DROP_INDEX_TYPE_CASES))
def test_dropIndexes_index_type(collection, test):
    """Test dropIndexes on various index types."""
    collection.insert_many(test.doc)
    execute_command(collection, {"createIndexes": collection.name, "indexes": test.setup_indexes})

    result = execute_command(collection, {"dropIndexes": collection.name, "index": test.indexes[0]})

    assertSuccessPartial(result, expected=test.expected, msg=test.msg)


def test_dropIndexes_same_key_with_partial_filter_by_name(collection):
    """Test dropping plain index by name when same key exists with partial filter."""
    collection.insert_one({"_id": 1, "a": 1, "status": "active"})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_plain"},
                {
                    "key": {"a": 1},
                    "name": "a_partial",
                    "partialFilterExpression": {"status": "active"},
                },
            ],
        },
    )

    execute_command(collection, {"dropIndexes": collection.name, "index": "a_plain"})

    result = execute_command(collection, {"listIndexes": collection.name})

    assertResult(
        result,
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"a": 1},
                "name": "a_partial",
                "partialFilterExpression": {"status": "active"},
            },
        ],
        ignore_doc_order=True,
        msg="Should drop only the plain index, leaving partial filter index intact",
    )


def test_dropIndexes_same_key_with_partial_filter_by_spec(collection):
    """Test dropping by spec when same key exists with and without partial filter."""
    collection.insert_one({"_id": 1, "a": 1, "status": "active"})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_plain"},
                {
                    "key": {"a": 1},
                    "name": "a_partial",
                    "partialFilterExpression": {"status": "active"},
                },
            ],
        },
    )

    result = execute_command(collection, {"dropIndexes": collection.name, "index": {"a": 1}})

    assertFailureCode(
        result,
        expected_code=AMBIGUOUS_INDEX_KEY_PATTERN_ERROR,
        msg="Dropping by spec with ambiguous key should fail",
    )


def test_dropIndexes_same_key_with_sparse_by_name(collection):
    """Test dropping plain index by name when same key exists with sparse option."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_plain"},
                {"key": {"a": 1}, "name": "a_sparse", "sparse": True},
            ],
        },
    )

    execute_command(collection, {"dropIndexes": collection.name, "index": "a_plain"})

    result = execute_command(collection, {"listIndexes": collection.name})

    assertResult(
        result,
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {"v": 2, "key": {"a": 1}, "name": "a_sparse", "sparse": True},
        ],
        ignore_doc_order=True,
        msg="Should drop only the plain index, leaving sparse index intact",
    )


def test_dropIndexes_same_key_with_sparse_by_spec(collection):
    """Test dropping by spec when same key exists with and without sparse fails."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_plain"},
                {"key": {"a": 1}, "name": "a_sparse", "sparse": True},
            ],
        },
    )

    result = execute_command(collection, {"dropIndexes": collection.name, "index": {"a": 1}})

    assertFailureCode(
        result,
        expected_code=AMBIGUOUS_INDEX_KEY_PATTERN_ERROR,
        msg="Dropping by spec with ambiguous key (sparse) should fail",
    )


def test_dropIndexes_same_key_with_collation_by_name(collection):
    """Test dropping plain index by name when same key exists with collation."""
    collection.insert_one({"_id": 1, "a": "hello"})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_plain"},
                {
                    "key": {"a": 1},
                    "name": "a_collated",
                    "collation": {"locale": "en", "strength": 2},
                },
            ],
        },
    )

    execute_command(collection, {"dropIndexes": collection.name, "index": "a_plain"})

    result = execute_command(collection, {"listIndexes": collection.name})

    assertResult(
        result,
        expected=[
            {"v": 2, "key": {"_id": 1}, "name": "_id_"},
            {
                "v": 2,
                "key": {"a": 1},
                "name": "a_collated",
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
        ignore_doc_order=True,
        msg="Should drop only the plain index, leaving collated index intact",
    )


def test_dropIndexes_same_key_with_collation_by_spec(collection):
    """Test dropping by spec when same key exists with and without collation fails."""
    collection.insert_one({"_id": 1, "a": "hello"})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_plain"},
                {
                    "key": {"a": 1},
                    "name": "a_collated",
                    "collation": {"locale": "en", "strength": 2},
                },
            ],
        },
    )

    result = execute_command(collection, {"dropIndexes": collection.name, "index": {"a": 1}})

    assertFailureCode(
        result,
        expected_code=AMBIGUOUS_INDEX_KEY_PATTERN_ERROR,
        msg="Dropping by spec with ambiguous key (collation) should fail",
    )


def test_dropIndexes_hidden_by_name(collection):
    """Test drop hidden index by name succeeds without unhiding."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "hidden_idx"}]},
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "hidden_idx", "hidden": True}}
    )

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "hidden_idx"})

    assertSuccessPartial(
        result, expected={"nIndexesWas": 2, "ok": 1.0}, msg="Should drop hidden index by name"
    )


def test_dropIndexes_hidden_by_spec(collection):
    """Test drop hidden index by spec succeeds."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "hidden_spec_idx"}],
        },
    )
    execute_command(
        collection,
        {"collMod": collection.name, "index": {"name": "hidden_spec_idx", "hidden": True}},
    )

    result = execute_command(collection, {"dropIndexes": collection.name, "index": {"a": 1}})

    assertSuccessPartial(
        result, expected={"nIndexesWas": 2, "ok": 1.0}, msg="Should drop hidden index by spec"
    )
