"""
Tests for dropIndexes command — core error scenarios.

Covers index not found, _id protection, namespace errors, array atomicity,
spec mismatches, view rejection, unrecognized fields, and idempotent errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INDEX_NOT_FOUND_ERROR,
    INVALID_NAMESPACE_ERROR,
    INVALID_OPTIONS_ERROR,
    MISSING_FIELD_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DROP_ERROR_CASES: list[IndexTestCase] = [
    IndexTestCase(
        "nonexistent_index",
        indexes=("no_such_index",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should return IndexNotFound (code 27)",
    ),
    IndexTestCase(
        "drop_id_by_name",
        indexes=("_id_",),
        doc=({"_id": 1},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should return cannot drop _id (code 72)",
    ),
    IndexTestCase(
        "drop_nonexistent_collection",
        indexes=("*",),
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Should return NamespaceNotFound (code 26)",
    ),
    IndexTestCase(
        "array_nonexistent_is_atomic",
        indexes=(["idx_a", "nonexistent"],),
        doc=({"_id": 1, "a": 1, "b": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}, {"key": {"b": 1}, "name": "idx_b"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should return IndexNotFound (code 27), no partial drops",
    ),
    IndexTestCase(
        "drop_id_by_spec",
        indexes=({"_id": 1},),
        doc=({"_id": 1},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should fail with cannot drop _id index (code 72)",
    ),
    IndexTestCase(
        "drop_id_by_array",
        indexes=(["_id_"],),
        doc=({"_id": 1},),
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should fail with cannot drop _id index (code 72)",
    ),
    IndexTestCase(
        "name_empty_string",
        indexes=("",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should return error for empty string name",
    ),
    IndexTestCase(
        "name_substring_no_match",
        indexes=("my_index",),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "my_index_name"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should not match substring of index name",
    ),
    IndexTestCase(
        "spec_wrong_field_order",
        indexes=({"b": -1, "a": 1},),
        doc=({"_id": 1, "a": 1, "b": 1},),
        setup_indexes=[{"key": {"a": 1, "b": -1}, "name": "a_1_b_-1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail when field order differs from index definition",
    ),
    IndexTestCase(
        "spec_wrong_sort_order",
        indexes=({"a": -1},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail when sort order differs",
    ),
    IndexTestCase(
        "spec_extra_fields",
        indexes=({"a": 1, "b": 1},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail when spec has extra fields",
    ),
    IndexTestCase(
        "spec_subset_of_compound",
        indexes=({"a": 1},),
        doc=({"_id": 1, "a": 1, "b": 1},),
        setup_indexes=[{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail when spec is subset of compound index",
    ),
    IndexTestCase(
        "spec_empty_document",
        indexes=({},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail for empty spec document",
    ),
    IndexTestCase(
        "spec_no_match",
        indexes=({"z": 1},),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should return IndexNotFound for non-matching spec",
    ),
    IndexTestCase(
        "array_duplicate_names",
        indexes=(["idx_a", "idx_a"],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail with IndexNotFound on duplicate name",
    ),
    IndexTestCase(
        "array_with_id_mixed",
        indexes=(["idx_a", "_id_"],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        error_code=INVALID_OPTIONS_ERROR,
        msg="Should fail with cannot drop _id index (code 72)",
    ),
    IndexTestCase(
        "array_empty_string_element",
        indexes=(["idx_a", ""],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail with empty string element in array",
    ),
    IndexTestCase(
        "array_non_string_element",
        indexes=([1, "idx_a"],),
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "idx_a"}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="Should fail with TypeMismatch for non-string element in array",
    ),
    IndexTestCase(
        "text_index_by_spec",
        indexes=({"content": "text"},),
        doc=({"_id": 1, "content": "hello"},),
        setup_indexes=[{"key": {"content": "text"}, "name": "text_idx"}],
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Should fail when dropping text index by spec",
    ),
    IndexTestCase(
        "index_field_omitted",
        indexes=None,
        doc=({"_id": 1, "a": 1},),
        setup_indexes=[{"key": {"a": 1}, "name": "a_1"}],
        error_code=MISSING_FIELD_ERROR,
        msg="Should return missing required field error (code 40414)",
    ),
    IndexTestCase(
        "empty_collection_name",
        indexes=("*",),
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Should return InvalidNamespace (code 73) for empty name",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DROP_ERROR_CASES))
def test_dropIndexes_error(collection, test):
    """Test dropIndexes error scenarios."""
    if test.doc:
        collection.insert_many(test.doc)
    if test.setup_indexes:
        execute_command(
            collection, {"createIndexes": collection.name, "indexes": test.setup_indexes}
        )

    cmd = {"dropIndexes": collection.name}
    if test.id == "drop_nonexistent_collection":
        cmd["dropIndexes"] = "nonexistent_coll_err_test"
    elif test.id == "empty_collection_name":
        cmd["dropIndexes"] = ""

    if test.indexes is not None:
        cmd["index"] = test.indexes[0]

    result = execute_command(collection, cmd)
    assertResult(result, error_code=test.error_code, msg=test.msg)


def test_dropIndexes_on_view(database_client, collection):
    """Test dropIndexes on a view fails with error."""
    collection.insert_one({"_id": 1, "a": 1})
    view_name = f"{collection.name}_view"
    database_client.command("create", view_name, viewOn=collection.name, pipeline=[])

    result = execute_command(database_client[view_name], {"dropIndexes": view_name, "index": "*"})

    assertResult(
        result,
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Should fail on view with CommandNotSupportedOnView",
    )


def test_dropIndexes_writeConcern_non_object(collection):
    """Test dropIndexes rejects non-object writeConcern."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection,
        {
            "dropIndexes": collection.name,
            "index": "*",
            "writeConcern": "invalid",
        },
    )

    assertResult(
        result, error_code=TYPE_MISMATCH_ERROR, msg="Non-object writeConcern should fail with 14"
    )


def test_dropIndexes_unrecognized_field(collection):
    """Test dropIndexes rejects unrecognized fields."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a")

    result = execute_command(
        collection,
        {
            "dropIndexes": collection.name,
            "index": "*",
            "unknownField": 1,
        },
    )

    assertResult(
        result,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field should fail with 40415",
    )


def test_dropIndexes_same_index_twice(collection):
    """Test dropping same index twice: first succeeds, second IndexNotFound."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.create_index("a", name="idx_a")

    execute_command(collection, {"dropIndexes": collection.name, "index": "idx_a"})

    result = execute_command(collection, {"dropIndexes": collection.name, "index": "idx_a"})

    assertResult(
        result,
        error_code=INDEX_NOT_FOUND_ERROR,
        msg="Second drop should return IndexNotFound (code 27)",
    )
