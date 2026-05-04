"""Tests for createIndexes index options.

Validates unique, sparse, TTL (expireAfterSeconds), hidden, background,
partial (partialFilterExpression), and collation index options including
valid values and option interactions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
    index_created_response,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

OPTIONS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="unique_true_no_duplicates",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        indexes=({"key": {"a": 1}, "name": "a_unique", "unique": True},),
        msg="Unique with no dups should succeed",
    ),
    IndexTestCase(
        id="unique_false_with_duplicates",
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 1}),
        indexes=({"key": {"a": 1}, "name": "a_1", "unique": False},),
        msg="Non-unique with dups should succeed",
    ),
    IndexTestCase(
        id="unique_on_compound_index",
        doc=({"_id": 1, "a": 1, "b": 1}, {"_id": 2, "a": 1, "b": 2}),
        indexes=({"key": {"a": 1, "b": 1}, "name": "ab_unique", "unique": True},),
        msg="Unique compound should succeed with different combos",
    ),
    IndexTestCase(
        id="unique_on_empty_collection",
        indexes=({"key": {"a": 1}, "name": "a_unique", "unique": True},),
        msg="Unique on empty collection should succeed",
    ),
    IndexTestCase(
        id="sparse_true",
        indexes=({"key": {"a": 1}, "name": "a_sparse", "sparse": True},),
        msg="Sparse true should succeed",
    ),
    IndexTestCase(
        id="sparse_false",
        indexes=({"key": {"a": 1}, "name": "a_not_sparse", "sparse": False},),
        msg="Sparse false should succeed",
    ),
    IndexTestCase(
        id="sparse_unique",
        indexes=({"key": {"a": 1}, "name": "a_sparse_unique", "sparse": True, "unique": True},),
        msg="Sparse + unique should succeed",
    ),
    IndexTestCase(
        id="ttl_zero",
        indexes=({"key": {"a": 1}, "name": "a_ttl_0", "expireAfterSeconds": 0},),
        msg="TTL 0 should succeed",
    ),
    IndexTestCase(
        id="ttl_positive",
        indexes=({"key": {"a": 1}, "name": "a_ttl_3600", "expireAfterSeconds": 3600},),
        msg="TTL positive should succeed",
    ),
    IndexTestCase(
        id="ttl_max_value",
        indexes=({"key": {"a": 1}, "name": "a_ttl_max", "expireAfterSeconds": 2147483647},),
        msg="TTL max value should succeed",
    ),
    IndexTestCase(
        id="hidden_true",
        indexes=({"key": {"a": 1}, "name": "a_hidden", "hidden": True},),
        msg="Hidden true should succeed",
    ),
    IndexTestCase(
        id="hidden_false",
        indexes=({"key": {"a": 1}, "name": "a_not_hidden", "hidden": False},),
        msg="Hidden false should succeed",
    ),
    IndexTestCase(
        id="hidden_with_unique",
        indexes=({"key": {"a": 1}, "name": "a_hidden_unique", "hidden": True, "unique": True},),
        msg="Hidden + unique should succeed",
    ),
    IndexTestCase(
        id="hidden_with_sparse",
        indexes=({"key": {"a": 1}, "name": "a_hidden_sparse", "hidden": True, "sparse": True},),
        msg="Hidden + sparse should succeed",
    ),
    IndexTestCase(
        id="hidden_with_ttl",
        indexes=(
            {"key": {"a": 1}, "name": "a_hidden_ttl", "hidden": True, "expireAfterSeconds": 3600},
        ),
        msg="Hidden + TTL should succeed",
    ),
    IndexTestCase(
        id="background_true",
        indexes=({"key": {"a": 1}, "name": "a_bg_true", "background": True},),
        msg="background:true should succeed",
    ),
    IndexTestCase(
        id="background_false",
        indexes=({"key": {"a": 1}, "name": "a_bg_false", "background": False},),
        msg="background:false should succeed",
    ),
    IndexTestCase(
        id="background_integer_truthy",
        indexes=({"key": {"a": 1}, "name": "a_bg_1", "background": 1},),
        msg="background:1 should succeed",
    ),
    IndexTestCase(
        id="background_integer_falsy",
        indexes=({"key": {"a": 1}, "name": "a_bg_0", "background": 0},),
        msg="background:0 should succeed",
    ),
    IndexTestCase(
        id="partial_equality",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_eq",
                "partialFilterExpression": {"status": "active"},
            },
        ),
        msg="Partial with equality should succeed",
    ),
    IndexTestCase(
        id="partial_exists",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_exists",
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="Partial with $exists should succeed",
    ),
    IndexTestCase(
        id="partial_gt",
        indexes=(
            {"key": {"a": 1}, "name": "a_partial_gt", "partialFilterExpression": {"a": {"$gt": 5}}},
        ),
        msg="Partial with $gt should succeed",
    ),
    IndexTestCase(
        id="partial_and",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_and",
                "partialFilterExpression": {"$and": [{"a": {"$gt": 0}}, {"b": {"$exists": True}}]},
            },
        ),
        msg="Partial with $and should succeed",
    ),
    IndexTestCase(
        id="partial_or",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_or",
                "partialFilterExpression": {"$or": [{"a": {"$gt": 0}}, {"b": {"$exists": True}}]},
            },
        ),
        msg="Partial with $or should succeed",
    ),
    IndexTestCase(
        id="partial_type",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_type",
                "partialFilterExpression": {"a": {"$type": "string"}},
            },
        ),
        msg="Partial with $type should succeed",
    ),
    IndexTestCase(
        id="partial_nested_field",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_nested",
                "partialFilterExpression": {"a.b": {"$gt": 5}},
            },
        ),
        msg="Partial with nested field should succeed",
    ),
    IndexTestCase(
        id="partial_compound_index",
        indexes=(
            {
                "key": {"a": 1, "b": 1},
                "name": "ab_partial",
                "partialFilterExpression": {"a": {"$gt": 0}},
            },
        ),
        msg="Compound index with partial filter should succeed",
    ),
    IndexTestCase(
        id="partial_field_not_in_key",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_other",
                "partialFilterExpression": {"z": {"$exists": True}},
            },
        ),
        msg="Partial filter referencing field not in index key should succeed",
    ),
    IndexTestCase(
        id="partial_unique",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_partial_unique",
                "unique": True,
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="Partial + unique should succeed",
    ),
    IndexTestCase(
        id="collation_en",
        indexes=({"key": {"a": 1}, "name": "a_en", "collation": {"locale": "en"}},),
        msg="Collation en should succeed",
    ),
    IndexTestCase(
        id="collation_simple",
        indexes=({"key": {"a": 1}, "name": "a_simple", "collation": {"locale": "simple"}},),
        msg="Collation simple should succeed",
    ),
    IndexTestCase(
        id="collation_with_strength",
        indexes=(
            {"key": {"a": 1}, "name": "a_str2", "collation": {"locale": "en", "strength": 2}},
        ),
        msg="Collation with strength should succeed",
    ),
    IndexTestCase(
        id="collation_with_numeric_ordering",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_numord",
                "collation": {"locale": "en", "numericOrdering": True},
            },
        ),
        msg="Collation with numericOrdering should succeed",
    ),
    IndexTestCase(
        id="collation_fr_ca",
        indexes=({"key": {"a": 1}, "name": "a_fr_ca", "collation": {"locale": "fr_CA"}},),
        msg="Collation fr_CA should succeed",
    ),
    IndexTestCase(
        id="text_with_simple_collation",
        indexes=(
            {"key": {"a": "text"}, "name": "a_text_simple", "collation": {"locale": "simple"}},
        ),
        msg="Text with simple collation should succeed",
    ),
    IndexTestCase(
        id="text_language_override_default",
        indexes=({"key": {"a": "text"}, "name": "a_text_lo_def", "language_override": "language"},),
        msg="Text with default language_override should succeed",
    ),
    IndexTestCase(
        id="text_language_override_custom_field",
        indexes=({"key": {"a": "text"}, "name": "a_text_lo_lang", "language_override": "lang"},),
        msg="Text with custom language_override field should succeed",
    ),
    IndexTestCase(
        id="sparse_with_collation",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_sparse_coll",
                "sparse": True,
                "collation": {"locale": "en"},
            },
        ),
        msg="Sparse with collation should succeed",
    ),
    IndexTestCase(
        id="ttl_with_collation",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_ttl_coll",
                "expireAfterSeconds": 3600,
                "collation": {"locale": "en"},
            },
        ),
        msg="TTL with collation should succeed",
    ),
    IndexTestCase(
        id="unique_partial_with_collation",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_uniq_part_coll",
                "unique": True,
                "partialFilterExpression": {"a": {"$exists": True}},
                "collation": {"locale": "en"},
            },
        ),
        msg="Unique + partial + collation should succeed",
    ),
    IndexTestCase(
        id="2dsphere_with_collation",
        indexes=(
            {
                "key": {"loc": "2dsphere", "a": 1},
                "name": "loc_2ds_coll",
                "collation": {"locale": "en"},
            },
        ),
        msg="2dsphere with collation should succeed",
    ),
    IndexTestCase(
        id="ttl_sparse",
        indexes=({"key": {"a": 1}, "name": "a_ts", "expireAfterSeconds": 3600, "sparse": True},),
        msg="TTL + sparse should succeed",
    ),
    IndexTestCase(
        id="ttl_partial",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_tp",
                "expireAfterSeconds": 3600,
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="TTL + partial should succeed",
    ),
    IndexTestCase(
        id="hidden_partial",
        indexes=(
            {
                "key": {"a": 1},
                "name": "a_hp",
                "hidden": True,
                "partialFilterExpression": {"a": {"$exists": True}},
            },
        ),
        msg="Hidden + partial should succeed",
    ),
    IndexTestCase(
        id="collation_unique",
        indexes=({"key": {"a": 1}, "name": "a_cu", "unique": True, "collation": {"locale": "en"}},),
        msg="Collation + unique should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPTIONS_TESTS))
def test_createIndexes_options(collection, test):
    """Test createIndexes index options."""
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": list(test.indexes),
        },
    )
    assertSuccessPartial(result, index_created_response(), test.msg)


def test_createIndexes_sparse_unique_missing_field_no_dup(collection):
    """Test sparse + unique allows multiple docs missing the indexed field."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_sparse_unique", "sparse": True, "unique": True}
            ],
        },
    )
    collection.insert_one({"_id": 1, "b": 1})
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 2, "b": 2}],
        },
    )
    assertSuccessPartial(
        result, {"ok": 1.0}, "Sparse unique should allow multiple missing field docs"
    )


def test_createIndexes_same_key_different_collation_different_names(collection):
    """Test two indexes on same key with different collations and names succeeds."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_en", "collation": {"locale": "en"}}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_fr", "collation": {"locale": "fr"}}],
        },
    )
    assertSuccessPartial(
        result,
        index_created_response(num_indexes_before=2, num_indexes_after=3),
        "Same key different collation different names should succeed",
    )


def test_createIndexes_collation_on_nonexistent_collection(database_client):
    """Test creating index with collation on non-existing collection auto-creates collection."""
    coll = database_client["coll_nonexist_collation"]
    coll.drop()
    result = execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [{"key": {"a": 1}, "name": "a_coll", "collation": {"locale": "en"}}],
        },
    )
    assertSuccessPartial(
        result, index_created_response(), "Collation on non-existing collection should succeed"
    )
    coll.drop()


def test_createIndexes_same_key_name_as_existing_hidden_noop(collection):
    """Test creating an index matching an existing hidden one is a noop."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_hidden", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_hidden", "hidden": True}],
        },
    )
    assertSuccessPartial(
        result,
        index_created_response(num_indexes_before=2, num_indexes_after=2),
        "Recreating same hidden index should be a noop",
    )
