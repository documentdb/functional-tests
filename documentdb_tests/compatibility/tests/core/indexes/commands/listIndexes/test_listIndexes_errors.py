"""
Tests for listIndexes command — argument validation and semantic error cases.

Covers empty/invalid collection names, non-existent collections, negative batchSize,
unrecognized fields, mutually exclusive options, and views.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


def test_listIndexes_empty_string_collection_name(collection):
    """Test listIndexes with empty string collection name fails."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"listIndexes": ""})
    assertFailureCode(result, INVALID_NAMESPACE_ERROR)


def test_listIndexes_nonexistent_collection_name(collection):
    """Test listIndexes with non-existent collection name returns NamespaceNotFound."""
    result = execute_command(collection, {"listIndexes": "nonexistent_coll_xyz"})
    assertFailureCode(result, NAMESPACE_NOT_FOUND_ERROR)


def test_listIndexes_after_drop_collection(database_client):
    """Test listIndexes after drop collection returns NamespaceNotFound."""
    coll_name = "test_drop_then_list"
    coll = database_client[coll_name]
    coll.insert_one({"_id": 1})
    coll.drop()
    result = execute_command(coll, {"listIndexes": coll_name})
    assertFailureCode(result, NAMESPACE_NOT_FOUND_ERROR)


def test_listIndexes_batchSize_negative(collection):
    """Test listIndexes with negative batchSize fails with BadValue."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection, {"listIndexes": collection.name, "cursor": {"batchSize": -1}}
    )
    assertFailureCode(result, BAD_VALUE_ERROR)


def test_listIndexes_cursor_unrecognized_subfield(collection):
    """Test listIndexes with unrecognized cursor subfield fails."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"listIndexes": collection.name, "cursor": {"batchSize": 1, "unknownField": True}},
    )
    assertFailureCode(result, UNRECOGNIZED_COMMAND_FIELD_ERROR)


def test_listIndexes_includeBuildUUIDs_true_with_includeIndexBuildInfo_true(collection):
    """Test includeBuildUUIDs: true with includeIndexBuildInfo: true fails with InvalidOptions."""
    collection.insert_one({"_id": 1})
    result = execute_command(
        collection,
        {"listIndexes": collection.name, "includeBuildUUIDs": True, "includeIndexBuildInfo": True},
    )
    assertFailureCode(result, INVALID_OPTIONS_ERROR)


UNRECOGNIZED_FIELDS: list[IndexTestCase] = [
    IndexTestCase(
        "foo",
        command_options={"foo": 1},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field 'foo' should fail",
    ),
    IndexTestCase(
        "filter",
        command_options={"filter": {"a": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="filter field should be rejected",
    ),
    IndexTestCase(
        "projection",
        command_options={"projection": {"a": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="projection field should be rejected",
    ),
    IndexTestCase(
        "sort",
        command_options={"sort": {"a": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="sort field should be rejected",
    ),
    IndexTestCase(
        "limit",
        command_options={"limit": 10},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="limit field should be rejected",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNRECOGNIZED_FIELDS))
def test_listIndexes_unrecognized_field(collection, test):
    """Test listIndexes rejects unrecognized fields."""
    collection.insert_one({"_id": 1})
    cmd = {"listIndexes": collection.name}
    cmd.update(test.command_options)
    result = execute_command(collection, cmd)
    assertResult(result, error_code=test.error_code, msg=test.msg)


def test_listIndexes_on_view(database_client):
    """Test listIndexes on view returns error."""
    src_name = "test_view_source_err"
    view_name = "test_view_err"
    src = database_client[src_name]
    src.insert_one({"_id": 1})
    database_client.create_collection(view_name, viewOn=src_name, pipeline=[])
    try:
        result = execute_command(database_client[view_name], {"listIndexes": view_name})
        assertFailureCode(result, COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR)
    finally:
        database_client.drop_collection(view_name)
        src.drop()
