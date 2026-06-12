"""
Error case tests for $rename update operator.

Tests self-rename, _id immutability, array-path restrictions, sibling-operator
path conflicts, path-not-viable traversal, invalid field names (empty,
trailing/double dot, $-prefixed target), and null bytes in the target name.

A null byte in the source field name is rejected client-side by the BSON
encoder (InvalidDocument) before the command is sent, so it is covered by a
standalone test below rather than the server-error-code parametrization.
"""

from typing import cast

import pytest
from bson.errors import InvalidDocument

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertExceptionType, assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    EMPTY_FIELD_NAME_ERROR,
    IMMUTABLE_FIELD_ERROR,
    NULL_BYTE_PATH_ERROR,
    PATH_NOT_VIABLE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SELF_RENAME_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "self_rename",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "a"}},
        error_code=BAD_VALUE_ERROR,
        msg="$rename of a field to itself should error (source and target must differ)",
    ),
]

ID_RESTRICTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "rename_id_to_other",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"_id": "newId"}},
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$rename of _id field should error",
    ),
    UpdateTestCase(
        "rename_to_id",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "_id"}},
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="$rename to _id field should error",
    ),
]

ARRAY_RESTRICTION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "source_array_index",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$rename": {"arr.0": "x"}},
        error_code=BAD_VALUE_ERROR,
        msg="$rename from array index should error",
    ),
    UpdateTestCase(
        "source_embedded_in_array",
        setup_docs=[{"_id": 1, "arr": [{"b": 1}]}],
        query={"_id": 1},
        update={"$rename": {"arr.0.b": "x"}},
        error_code=BAD_VALUE_ERROR,
        msg="$rename from embedded doc in array should error",
    ),
    UpdateTestCase(
        "target_array_index",
        setup_docs=[{"_id": 1, "x": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$rename": {"x": "arr.0"}},
        error_code=BAD_VALUE_ERROR,
        msg="$rename to array index should error",
    ),
]

PATH_CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "rename_source_with_set",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}, "$set": {"a": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$rename source + $set same field should conflict",
    ),
    UpdateTestCase(
        "rename_target_with_set",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}, "$set": {"b": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$rename target + $set same field should conflict",
    ),
    UpdateTestCase(
        "rename_source_with_unset",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b"}, "$unset": {"a": ""}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$rename source + $unset same field should conflict",
    ),
    UpdateTestCase(
        "two_renames_to_same_target",
        setup_docs=[{"_id": 1, "a": 1, "c": 2}],
        query={"_id": 1},
        update={"$rename": {"a": "b", "c": "b"}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Two renames to same target should conflict",
    ),
    UpdateTestCase(
        "chain_rename_source_is_target",
        setup_docs=[{"_id": 1, "a": 1, "b": 2}],
        query={"_id": 1},
        update={"$rename": {"a": "b", "b": "c"}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Chain rename where source of one is target of another should conflict",
    ),
    UpdateTestCase(
        "rename_target_with_inc",
        setup_docs=[{"_id": 1, "a": 1, "d": 10}],
        query={"_id": 1},
        update={"$rename": {"a": "d"}, "$inc": {"d": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$rename target + $inc same field should conflict",
    ),
]

PATH_TRAVERSAL_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "source_traverses_scalar",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a.b": "c"}},
        error_code=PATH_NOT_VIABLE_ERROR,
        msg="$rename source path traversing a scalar should error",
    ),
    UpdateTestCase(
        "target_traverses_scalar",
        setup_docs=[{"_id": 1, "a": 1, "b": 2}],
        query={"_id": 1},
        update={"$rename": {"a": "b.x"}},
        error_code=PATH_NOT_VIABLE_ERROR,
        msg="$rename target path traversing a scalar should error",
    ),
]

INVALID_PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_source_name",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"": "b"}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="$rename with empty source name should error",
    ),
    UpdateTestCase(
        "trailing_dot_in_target",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b."}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="$rename with trailing dot in target should error",
    ),
    UpdateTestCase(
        "double_dot_in_target",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b..c"}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="$rename with double dot in target should error",
    ),
]

EMPTY_NAME_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "empty_target_name",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": ""}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="$rename to empty string should error",
    ),
    UpdateTestCase(
        "dollar_prefixed_target",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "$b"}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="$rename to $-prefixed field name should error",
    ),
]

NULL_BYTE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "null_byte_end",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b\x00"}},
        error_code=NULL_BYTE_PATH_ERROR,
        msg="$rename with null byte at end of target should error",
    ),
    UpdateTestCase(
        "null_byte_middle",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "b\x00c"}},
        error_code=NULL_BYTE_PATH_ERROR,
        msg="$rename with null byte in middle of target should error",
    ),
    UpdateTestCase(
        "null_byte_start",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$rename": {"a": "\x00b"}},
        error_code=NULL_BYTE_PATH_ERROR,
        msg="$rename with null byte at start of target should error",
    ),
]


ALL_TESTS = (
    SELF_RENAME_TESTS
    + ID_RESTRICTION_TESTS
    + ARRAY_RESTRICTION_TESTS
    + PATH_TRAVERSAL_TESTS
    + PATH_CONFLICT_TESTS
    + INVALID_PATH_TESTS
    + EMPTY_NAME_TESTS
    + NULL_BYTE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_rename_error(collection, test: UpdateTestCase):
    """Test $rename error handling."""
    collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertFailureCode(result, cast(int, test.error_code), msg=test.msg)


def test_rename_null_byte_in_source(collection):
    """A null byte in the source field name is rejected by the BSON encoder.

    Unlike a null byte in the target name (which the server rejects with a
    server error code), a null byte in the source key fails client-side
    during BSON encoding, before the command is sent. The driver raises
    InvalidDocument, which carries no server error code.
    """
    collection.insert_one({"_id": 1, "a": 1})

    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$rename": {"a\x00b": "c"}}}],
        },
    )
    assertExceptionType(
        result,
        InvalidDocument,
        msg="$rename with null byte in source should be rejected by the BSON encoder",
    )
