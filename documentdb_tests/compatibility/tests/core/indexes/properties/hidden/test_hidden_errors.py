"""Tests for hidden index error cases."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailure, assertFailureCode, assertSuccess
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CANNOT_CREATE_INDEX_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    DUPLICATE_KEY_ERROR,
    INDEX_NOT_FOUND_ERROR,
    INDEX_OPTIONS_CONFLICT_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    NO_QUERY_EXECUTION_PLANS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


HIDE_UNHIDE_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hide_nonmatching_key_pattern",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"keyPattern": {"nope": 1}, "hidden": True},
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Hiding a non-matching key pattern should fail with IndexNotFound",
    ),
    IndexTestCase(
        id="hide_nonexistent_name",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"name": "does_not_exist", "hidden": True},
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Hiding a non-existent index name should fail with IndexNotFound",
    ),
    IndexTestCase(
        id="hide_empty_name",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"name": "", "hidden": True},
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Hiding with an empty index name should fail with IndexNotFound",
    ),
    IndexTestCase(
        id="hide_partial_compound_key",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        input={"keyPattern": {"a": 1}, "hidden": True},
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="A partial key pattern should not match a compound index",
    ),
    IndexTestCase(
        id="unhide_nonmatching_key_pattern",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"keyPattern": {"nope": 1}, "hidden": False},
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Unhiding a non-matching key pattern should fail with IndexNotFound",
    ),
    IndexTestCase(
        id="unhide_nonexistent_name",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"name": "does_not_exist", "hidden": False},
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Unhiding a non-existent index name should fail with IndexNotFound",
    ),
    IndexTestCase(
        id="hide_id_by_key_pattern",
        indexes=(),
        input={"keyPattern": {"_id": 1}, "hidden": True},
        error_code=BAD_VALUE_ERROR,
        msg="Hiding the _id index should fail with BadValue",
    ),
    IndexTestCase(
        id="hide_id_by_name",
        indexes=(),
        input={"name": "_id_", "hidden": True},
        error_code=BAD_VALUE_ERROR,
        msg="Hiding the _id index by name should fail with BadValue",
    ),
    IndexTestCase(
        id="integer_index_arg",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input=5,
        error_code=TYPE_MISMATCH_ERROR,
        msg="An integer index argument should be rejected as a type error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HIDE_UNHIDE_ERROR_TESTS))
def test_collmod_hide_unhide_errors(collection, test):
    """Test collMod hide/unhide rejects invalid targets."""
    collection.insert_one({"x": 1})  # ensure collection exists
    if test.indexes:
        execute_command(
            collection,
            {"createIndexes": collection.name, "indexes": list(test.indexes)},
        )
    result = execute_command(collection, {"collMod": collection.name, "index": test.input})
    assertFailureCode(result, test.error_code, msg=test.msg)


HINT_HIDDEN_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="find_hint_by_name",
        input={"command": "find", "hint": "a_1"},
        error_code=BAD_VALUE_ERROR,
        msg="find hint on a hidden index name should fail with BadValue",
    ),
    IndexTestCase(
        id="find_hint_by_key_pattern",
        input={"command": "find", "hint": {"a": 1}},
        error_code=BAD_VALUE_ERROR,
        msg="find hint on a hidden index key pattern should fail with BadValue",
    ),
    IndexTestCase(
        id="aggregate_hint",
        input={"command": "aggregate", "hint": "a_1"},
        error_code=BAD_VALUE_ERROR,
        msg="aggregate hint on a hidden index should fail with BadValue",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HINT_HIDDEN_ERROR_TESTS))
def test_hint_hidden_index_errors(collection, test):
    """Test hinting a hidden index is rejected."""
    collection.insert_many([{"a": i} for i in range(5)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    if test.input["command"] == "find":
        result = execute_command(
            collection, {"find": collection.name, "filter": {"a": 1}, "hint": test.input["hint"]}
        )
    else:
        result = execute_command(
            collection,
            {
                "aggregate": collection.name,
                "pipeline": [{"$match": {"a": 1}}],
                "hint": test.input["hint"],
                "cursor": {},
            },
        )
    assertFailureCode(result, test.error_code, msg=test.msg)


CONFLICT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hidden_true_on_existing_non_hidden",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"key": {"a": 1}, "name": "a_1", "hidden": True},
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Re-creating an existing index with a different hidden value should conflict",
    ),
    IndexTestCase(
        id="hidden_false_on_existing_hidden",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"key": {"a": 1}, "name": "a_1", "hidden": False},
        error_code=INDEX_OPTIONS_CONFLICT_ERROR,
        msg="Re-creating a hidden index with hidden:false should conflict",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFLICT_TESTS))
def test_create_index_conflict_errors(collection, test):
    """Test conflicting hidden option on existing index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [test.input]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


VIEW_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="create_hidden_index_on_view",
        input={"command": "createIndexes"},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Creating a hidden index on a view should be rejected",
    ),
    IndexTestCase(
        id="hide_index_on_view",
        input={"command": "collMod", "hidden": True},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Hiding an index on a view should be rejected",
    ),
    IndexTestCase(
        id="unhide_index_on_view",
        input={"command": "collMod", "hidden": False},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Unhiding an index on a view should be rejected",
    ),
]


@pytest.mark.no_parallel
@pytest.mark.parametrize("test", pytest_params(VIEW_ERROR_TESTS))
def test_hidden_index_on_view_errors(collection, database_client, test):
    """Test hidden index operations on a view are rejected."""
    source_name = f"{collection.name}_source"
    view_name = f"{collection.name}_view"
    source = database_client[source_name]
    execute_command(source, {"insert": source_name, "documents": [{"a": 1}, {"a": 2}]})
    view = database_client[view_name]
    execute_command(view, {"create": view_name, "viewOn": source_name, "pipeline": []})

    if test.input["command"] == "createIndexes":
        result = execute_command(
            view,
            {
                "createIndexes": view_name,
                "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
            },
        )
    else:
        result = execute_command(
            view, {"collMod": view_name, "index": {"name": "a_1", "hidden": test.input["hidden"]}}
        )
    assertFailureCode(result, test.error_code, msg=test.msg)


UNIQUE_CONSTRAINT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="duplicate_insert_while_hidden",
        input={"operation": "insert"},
        indexes=({"key": {"a": 1}, "name": "a_1", "unique": True, "hidden": True},),
        error_code=DUPLICATE_KEY_ERROR,
        msg="A hidden unique index should still reject duplicate inserts",
    ),
    IndexTestCase(
        id="duplicate_update_while_hidden",
        input={"operation": "update"},
        indexes=({"key": {"a": 1}, "name": "a_1", "unique": True, "hidden": True},),
        error_code=DUPLICATE_KEY_ERROR,
        msg="A hidden unique index should still reject duplicate updates",
    ),
    IndexTestCase(
        id="duplicate_insert_after_hiding",
        input={"operation": "hide_then_insert"},
        indexes=({"key": {"a": 1}, "name": "a_1", "unique": True},),
        error_code=DUPLICATE_KEY_ERROR,
        msg="Unique constraint must remain active regardless of hidden state",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNIQUE_CONSTRAINT_TESTS))
def test_unique_constraint_enforced_while_hidden(collection, test):
    """Test hidden unique indexes still enforce uniqueness."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    execute_command(collection, {"insert": collection.name, "documents": [{"a": 1}]})

    if test.input["operation"] == "insert":
        result = execute_command(collection, {"insert": collection.name, "documents": [{"a": 1}]})
    elif test.input["operation"] == "update":
        execute_command(collection, {"insert": collection.name, "documents": [{"a": 2}]})
        result = execute_command(
            collection,
            {"update": collection.name, "updates": [{"q": {"a": 2}, "u": {"$set": {"a": 1}}}]},
        )
    else:  # hide_then_insert
        execute_command(
            collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
        )
        result = execute_command(collection, {"insert": collection.name, "documents": [{"a": 1}]})

    assertFailureCode(result, test.error_code, msg=test.msg)


def test_hidden_text_index_text_query_errors(collection):
    """Test $text fails when only text index is hidden."""
    collection.insert_many([{"txt": "hello world"}, {"txt": "goodbye"}])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"txt": "text"}, "name": "txt_text", "hidden": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"$text": {"$search": "hello"}}}
    )
    assertFailureCode(
        result,
        NO_QUERY_EXECUTION_PLANS_ERROR,
        msg="$text should fail when the only text index is hidden",
    )


def test_find_hint_after_unhide_succeeds(collection):
    """Test hint on unhidden index succeeds."""
    collection.insert_many([{"a": i} for i in range(5)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": 1}, "hint": "a_1"}
    )
    assertSuccess(
        result,
        [{"a": 1}],
        transform=lambda docs: [{"a": d["a"]} for d in docs],
        msg="Hint on an unhidden index should succeed and return matching documents",
    )


@pytest.mark.no_parallel
def test_create_hidden_index_on_system_collection_errors(database_client):
    """Test hidden:true on a system collection is rejected."""
    execute_command(database_client["system.views"], {"create": "system.views"})
    result = execute_command(
        database_client["system.views"],
        {
            "createIndexes": "system.views",
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    assertFailure(
        result,
        True,
        transform=lambda actual: actual["code"]
        in {BAD_VALUE_ERROR, CANNOT_CREATE_INDEX_ERROR, INVALID_NAMESPACE_ERROR},
        msg="Creating a hidden index on a system collection should be rejected",
    )
