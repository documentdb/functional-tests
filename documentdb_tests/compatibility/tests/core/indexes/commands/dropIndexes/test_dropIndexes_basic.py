"""
Tests for dropIndexes command — core success behavior.

Covers drop by name, by spec, by array, by '*', response structure
(nIndexesWas), idempotent operations, and long name edge cases.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertResult, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DROP_INDEXES_CASES: list[IndexTestCase] = [
    IndexTestCase(
        "by_name",
        indexes=("a_1",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should return nIndexesWas and ok:1",
    ),
    IndexTestCase(
        "by_auto_generated_compound_name",
        indexes=("a_1_b_-1",),
        doc=({"_id": 1, "a": 1, "b": 1},),
        setup_indexes=[{"key": {"a": 1, "b": -1}, "name": "a_1_b_-1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop by auto-generated compound name",
    ),
    IndexTestCase(
        "by_custom_name",
        indexes=("myCustomIndex",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "myCustomIndex"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop by custom name",
    ),
    IndexTestCase(
        "numeric_string_name",
        indexes=("123",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "123"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop index with numeric string name",
    ),
    IndexTestCase(
        "literal_star_name",
        indexes=("test*",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "test*"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should treat 'test*' as literal name, not wildcard",
    ),
    IndexTestCase(
        "unicode_name",
        indexes=("índex_ünïcödé",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "índex_ünïcödé"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop index with unicode name",
    ),
    IndexTestCase(
        "long_index_name",
        indexes=("idx_" + "x" * 120,),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_" + "x" * 120}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop index with long name",
    ),
    IndexTestCase(
        "name_with_dots",
        indexes=("my.index.name",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "my.index.name"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop index with dots in name",
    ),
    IndexTestCase(
        "name_with_dollar",
        indexes=("$myIndex",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "$myIndex"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop index with dollar sign in name",
    ),
    IndexTestCase(
        "name_with_spaces",
        indexes=("my index name",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "my index name"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop index with spaces in name",
    ),
    IndexTestCase(
        "spec_single_field",
        indexes=({"a": 1},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop by single field spec",
    ),
    IndexTestCase(
        "spec_compound",
        indexes=({"a": 1, "b": -1},),
        doc=({"_id": 1, "a": 1, "b": 1},),
        setup_indexes=[{"key": {"a": 1, "b": -1}, "name": "a_1_b_-1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop by compound spec",
    ),
    IndexTestCase(
        "spec_descending",
        indexes=({"a": -1},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": -1}, "name": "a_-1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop descending index by spec",
    ),
    IndexTestCase(
        "array_multiple_names",
        indexes=(["idx_a", "idx_b"],),
        doc=({"_id": 1, "a": 1, "b": 1, "c": 1},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "idx_a"},
            {"key": {"b": 1}, "name": "idx_b"},
            {"key": {"c": 1}, "name": "idx_c"},
        ],
        expected={"nIndexesWas": 4, "ok": 1.0},
        msg="Should drop both specified indexes",
    ),
    IndexTestCase(
        "array_single_element",
        indexes=(["idx_a"],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should drop single element array",
    ),
    IndexTestCase(
        "array_empty",
        indexes=([],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should succeed as no-op for empty array",
    ),
    IndexTestCase(
        "array_star_element",
        indexes=(["*"],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        expected={"nIndexesWas": 2, "ok": 1.0},
        msg="Should treat '*' in array same as string '*'",
    ),
    IndexTestCase(
        "star_removes_all_secondary",
        indexes=("*",),
        doc=({"_id": 1, "a": 1, "b": 1, "c": 1},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "a_1"},
            {"key": {"b": 1}, "name": "b_1"},
            {"key": {"c": 1}, "name": "c_1"},
        ],
        expected={"nIndexesWas": 4, "ok": 1.0},
        msg="Should drop all secondary indexes",
    ),
    IndexTestCase(
        "star_only_id_noop",
        indexes=("*",),
        doc=({"_id": 1},),
        expected={"nIndexesWas": 1, "ok": 1.0},
        msg="Should succeed with nIndexesWas=1",
    ),
    IndexTestCase(
        "star_many_secondary",
        indexes=("*",),
        doc=({"_id": 1, "a": 1, "b": 1, "c": 1, "d": 1, "e": 1},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "a_1"},
            {"key": {"b": 1}, "name": "b_1"},
            {"key": {"c": 1}, "name": "c_1"},
            {"key": {"d": 1}, "name": "d_1"},
            {"key": {"e": 1}, "name": "e_1"},
        ],
        expected={"nIndexesWas": 6, "ok": 1.0},
        msg="Should report nIndexesWas=6 for 5 secondary + _id",
    ),
    IndexTestCase(
        "nIndexesWas_drop_one_of_three",
        indexes=("idx_a",),
        doc=({"_id": 1, "a": 1, "b": 1, "c": 1},),
        setup_indexes=[
            {"key": {"a": 1}, "name": "idx_a"},
            {"key": {"b": 1}, "name": "idx_b"},
            {"key": {"c": 1}, "name": "idx_c"},
        ],
        expected={"nIndexesWas": 4, "ok": 1.0},
        msg="Should report nIndexesWas=4 before dropping idx_a",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DROP_INDEXES_CASES))
def test_dropIndexes(collection, test):
    """Test dropIndexes command success scenarios."""
    collection.insert_many(test.doc)
    if test.setup_indexes:
        execute_command(
            collection, {"createIndexes": collection.name, "indexes": test.setup_indexes}
        )

    result = execute_command(collection, {"dropIndexes": collection.name, "index": test.indexes[0]})

    assertSuccessPartial(result, expected=test.expected, msg=test.msg)


def test_dropIndexes_empty_collection_star(database_client, collection):
    """Test dropIndexes '*' on explicitly created empty collection succeeds."""
    database_client.create_collection(collection.name)

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "*"})

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 1, "ok": 1.0},
        msg="Should succeed on empty collection with only _id",
    )


def test_dropIndexes_empty_after_delete_star(collection):
    """Test dropIndexes '*' on collection emptied by deleting all docs."""
    collection.insert_one({"_id": 1})
    collection.delete_many({})

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "*"})

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 1, "ok": 1.0},
        msg="Should succeed on implicitly empty collection",
    )


def test_dropIndexes_star_preserves_id(collection):
    """Test '*' preserves _id index after dropping all secondary."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )

    execute_command(collection, {"dropIndexes": collection.name, "index": "*"})

    result = execute_command(collection, {"listIndexes": collection.name})

    assertResult(
        result,
        expected=[{"v": 2, "key": {"_id": 1}, "name": "_id_"}],
        msg="Should only have _id index remaining",
    )


def test_dropIndexes_star_after_partial_drop(collection):
    """Test drop '*' after already dropping one index reports correct count."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1, "c": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "idx_a"},
                {"key": {"b": 1}, "name": "idx_b"},
                {"key": {"c": 1}, "name": "idx_c"},
            ],
        },
    )
    execute_command(collection, {"dropIndexes": collection.name, "index": "idx_a"})

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "*"})

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 3, "ok": 1.0},
        msg="Should report nIndexesWas=3 after one was already dropped",
    )


def test_dropIndexes_star_twice(collection):
    """Test dropping '*' twice: first drops all, second is no-op."""
    collection.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )

    execute_command(collection, {"dropIndexes": collection.name, "index": "*"})

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "*"})

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 1, "ok": 1.0},
        msg="Second '*' should succeed with nIndexesWas=1",
    )


def test_dropIndexes_long_collection_name(database_client, collection):
    """Test creating and dropping indexes on collection with long name."""
    long_name = collection.name + "_" + "a" * 100
    database_client.create_collection(long_name)
    coll = database_client[long_name]
    coll.insert_one({"_id": 1, "a": 1, "b": 1})
    execute_command(
        coll,
        {
            "createIndexes": long_name,
            "indexes": [
                {"key": {"a": 1}, "name": "idx_a"},
                {"key": {"b": 1}, "name": "idx_b"},
            ],
        },
    )

    result = execute_command(coll, {"dropIndexes": long_name, "index": "idx_a"})

    assertSuccessPartial(
        result,
        expected={"nIndexesWas": 3, "ok": 1.0},
        msg="Should drop index on long-named collection",
    )
