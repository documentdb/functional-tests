"""
Tests for $setOnInsert update operator - upsert behavior.

Covers insert path, update path, combination with other operators, query field
extraction, and $and query conditions.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SETONINSERT_INSERT_PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="combined_with_set_no_match",
        query={"_id": 1},
        update={"$set": {"a": 1}, "$setOnInsert": {"b": 2}},
        upsert=True,
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Both $set and $setOnInsert should apply on insert",
    ),
    UpdateTestCase(
        id="array_value",
        query={"_id": 1},
        update={"$setOnInsert": {"arr": [1, 2, 3]}},
        upsert=True,
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="Should set array value on insert",
    ),
    UpdateTestCase(
        id="empty_object_value_on_insert",
        query={"_id": 1},
        update={"$setOnInsert": {"x": {}}},
        upsert=True,
        expected=[{"_id": 1, "x": {}}],
        msg="Should create doc with empty object value on insert path",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_INSERT_PATH_TESTS))
def test_setOnInsert_insert_path(collection, test):
    """Test $setOnInsert on insert path (no match, upsert:true)."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, test.expected, msg=test.msg)


SETONINSERT_UPDATE_PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="match_does_nothing",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$setOnInsert": {"x": 100}},
        upsert=True,
        expected=[{"_id": 1, "a": 1}],
        msg="$setOnInsert should be ignored on update path",
    ),
    UpdateTestCase(
        id="combined_with_set_match",
        setup_docs=[{"_id": 1, "a": 0}],
        query={"_id": 1},
        update={"$set": {"a": 1}, "$setOnInsert": {"b": 2}},
        upsert=True,
        expected=[{"_id": 1, "a": 1}],
        msg="Only $set should apply on update path",
    ),
    UpdateTestCase(
        id="nested_subdoc_noop_on_match",
        setup_docs=[{"_id": 1, "a": {"b": 1}}],
        query={"_id": 1},
        update={"$setOnInsert": {"a.c": 99}},
        upsert=True,
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="$setOnInsert on nested path should be no-op when doc matches",
    ),
    UpdateTestCase(
        id="multi_dot_paths_noop_on_match",
        setup_docs=[{"_id": 1, "a": {"b": 0}}],
        query={"_id": 1},
        update={"$setOnInsert": {"a.b": 1, "a.c": 2}},
        upsert=True,
        expected=[{"_id": 1, "a": {"b": 0}}],
        msg="$setOnInsert with multiple dot paths should be no-op when doc matches",
    ),
    UpdateTestCase(
        id="field_conflict_with_query_noop_on_match",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1, "a": 1},
        update={"$setOnInsert": {"a": 99}},
        upsert=True,
        expected=[{"_id": 1, "a": 1}],
        msg="$setOnInsert should not overwrite query-matched field on update path",
    ),
    UpdateTestCase(
        id="empty_object_value_noop_on_match",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$setOnInsert": {"x": {}}},
        upsert=True,
        expected=[{"_id": 1, "a": 1}],
        msg="$setOnInsert with empty object value should be no-op when doc matches",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_UPDATE_PATH_TESTS))
def test_setOnInsert_update_path(collection, test):
    """Test $setOnInsert on update path (match exists)."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, test.expected, msg=test.msg)


SETONINSERT_QUERY_EXTRACTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="equality_fields_extracted",
        query={"_id": 1, "status": "active"},
        update={"$setOnInsert": {"x": 1}},
        upsert=True,
        expected=[{"_id": 1, "status": "active", "x": 1}],
        msg="Equality fields from query should be in upserted doc",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_QUERY_EXTRACTION_TESTS))
def test_setOnInsert_query_extraction(collection, test):
    """Test upsert extracts equality fields from query into inserted doc."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, test.expected, msg=test.msg)


SETONINSERT_WITHOUT_UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="no_match_no_upsert",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 99},
        update={"$setOnInsert": {"x": 100}},
        expected={"n": 0, "nModified": 0, "ok": 1.0},
        msg="Without upsert, no insert should occur",
    ),
    UpdateTestCase(
        id="match_no_upsert_noop",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$setOnInsert": {"x": 100}},
        expected={"n": 1, "nModified": 0, "ok": 1.0},
        msg="With match but no upsert, $setOnInsert should be no-op",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_WITHOUT_UPSERT_TESTS))
def test_setOnInsert_without_upsert(collection, test):
    """Test $setOnInsert without upsert has no effect."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


# expected uses partial match since _id is auto-generated
SETONINSERT_AND_QUERY_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="and_equality_extracted",
        query={"$and": [{"a": 1}, {"b": 2}]},
        update={"$setOnInsert": {"x": 10}},
        upsert=True,
        expected={"a": 1, "b": 2, "x": 10},
        msg="Equality fields from $and should be in upserted doc",
    ),
    UpdateTestCase(
        id="and_or_single_clause_extracted",
        query={"$and": [{"a": 1}, {"$or": [{"b": 2}]}]},
        update={"$setOnInsert": {"x": 10}},
        upsert=True,
        expected={"a": 1, "b": 2, "x": 10},
        msg="$or single clause values should be extracted",
    ),
    UpdateTestCase(
        id="and_or_multiple_clauses_not_extracted",
        query={"$and": [{"a": 1}], "$or": [{"b": 2}, {"b": 3}]},
        update={"$setOnInsert": {"x": 10}},
        upsert=True,
        expected={"a": 1, "x": 10},
        msg="$or multi-clause values should NOT be extracted",
    ),
    UpdateTestCase(
        id="and_range_predicate_not_extracted",
        query={"$and": [{"a": 1}, {"b": {"$gt": 5}}]},
        update={"$setOnInsert": {"x": 10}},
        upsert=True,
        expected={"a": 1, "x": 10},
        msg="Range predicate values should NOT be extracted",
    ),
    UpdateTestCase(
        id="and_regex_not_extracted",
        query={"$and": [{"a": 1}, {"b": {"$regex": "^abc"}}]},
        update={"$setOnInsert": {"x": 10}},
        upsert=True,
        expected={"a": 1, "x": 10},
        msg="Regex predicate values should NOT be extracted",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SETONINSERT_AND_QUERY_TESTS))
def test_setOnInsert_and_query_extraction(collection, test):
    """Test $setOnInsert with $and query conditions and field extraction."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"x": 10}})
    assertSuccessPartial(result, {"cursor": {"firstBatch": [test.expected]}}, msg=test.msg)


def test_setOnInsert_empty_query_auto_generates_id(collection):
    """Test $setOnInsert with empty query {} and upsert → _id auto-generated."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {}, "u": {"$setOnInsert": {"x": 42}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"x": 42}})
    assertSuccessPartial(
        result,
        {"cursor": {"firstBatch": [{"x": 42}]}},
        msg="Empty query upsert should auto-generate _id and set field",
    )


def test_setOnInsert_query_field_vs_operator_on_insert(collection):
    """Test $setOnInsert overrides query-extracted field value on insert path."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1, "a": 1}, "u": {"$setOnInsert": {"a": 99}}, "upsert": True}
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "a": 99}],
        msg="$setOnInsert should override query-extracted field value on insert",
    )


def test_setOnInsert_id_null_upsert(collection):
    """Test $setOnInsert with null _id matching query succeeds and creates doc."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": None}, "u": {"$setOnInsert": {"_id": None, "x": 1}}, "upsert": True}
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": None}})
    assertSuccess(result, [{"_id": None, "x": 1}], msg="Inserted doc should have _id: null")


def test_setOnInsert_id_subfield_ignored_on_match(collection):
    """Test $setOnInsert on _id subfield is ignored when match exists (no-op)."""
    collection.insert_one({"_id": {"a": 1}, "x": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": {"a": 1}},
                    "u": {"$setOnInsert": {"_id.b": 2}},
                    "upsert": True,
                }
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"n": 1, "nModified": 0, "ok": 1.0},
        msg="$setOnInsert should be no-op on match",
    )
