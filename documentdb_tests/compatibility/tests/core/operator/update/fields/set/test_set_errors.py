"""
Tests for $set update operator - error code validation.

Covers invalid field paths, conflicting paths, immutable _id, arrayFilters errors,
and path traversal errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    DOLLAR_PREFIXED_FIELD_NAME_ERROR,
    EMPTY_FIELD_NAME_ERROR,
    FAILED_TO_PARSE_ERROR,
    IMMUTABLE_FIELD_ERROR,
    PATH_NOT_VIABLE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SET_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="empty_field_name",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"": 1}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Empty field name should fail",
    ),
    UpdateTestCase(
        id="conflicting_paths",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a": 1, "a.b": 2}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="Conflicting paths should fail",
    ),
    UpdateTestCase(
        id="immutable_id",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"_id": 2}},
        error_code=IMMUTABLE_FIELD_ERROR,
        msg="Modifying _id should fail",
    ),
    UpdateTestCase(
        id="dollar_prefix_field",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"$invalid": 1}},
        error_code=DOLLAR_PREFIXED_FIELD_NAME_ERROR,
        msg="Dollar-prefix field should fail",
    ),
    UpdateTestCase(
        id="empty_field_name_trailing_dot",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a.": 1}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Trailing dot in path should fail (empty field name)",
    ),
    UpdateTestCase(
        id="empty_field_name_leading_dot",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {".a": 1}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Leading dot in path should fail (empty field name)",
    ),
    UpdateTestCase(
        id="empty_field_name_double_dot",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$set": {"a..b": 1}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Double dot in path should fail (empty field name)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_ERROR_TESTS))
def test_set_errors(collection, test):
    """Test $set error cases."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_set_undeclared_array_filter(collection):
    """Test $set with undeclared arrayFilter identifier returns error."""
    collection.insert_one({"_id": 1, "arr": [{"x": 1}, {"x": 2}]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"arr.$[undeclared].x": 99}},
                    "arrayFilters": [],
                }
            ],
        },
    )
    assertFailureCode(result, BAD_VALUE_ERROR, msg="Undeclared arrayFilter identifier should error")


def test_set_empty_operand_with_array_filters_error(collection):
    """Test $set with empty {} and arrayFilters specified returns parse error."""
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {}},
                    "arrayFilters": [{"elem": {"$gt": 1}}],
                }
            ],
        },
    )
    assertFailureCode(
        result, FAILED_TO_PARSE_ERROR, msg="Empty $set with arrayFilters should error"
    )


def test_set_cannot_traverse_non_object(collection):
    """Test $set 'a.b' on document where a is a string fails."""
    collection.insert_one({"_id": 1, "a": "string"})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a.b": 1}}}],
        },
    )
    assertFailureCode(
        result,
        PATH_NOT_VIABLE_ERROR,
        msg="Cannot traverse non-object with dot notation",
    )
