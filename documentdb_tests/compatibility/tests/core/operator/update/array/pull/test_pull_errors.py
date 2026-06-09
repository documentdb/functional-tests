"""Tests for $pull operator error cases.

Covers: operand-shape validation, invalid field paths.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    EMPTY_FIELD_NAME_ERROR,
    FAILED_TO_PARSE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PULL_ERROR_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "non_document_operand_integer",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": 1},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should error when $pull operand is not a document",
    ),
    UpdateTestCase(
        "non_document_operand_array",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": []},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="Should error when $pull operand is an array",
    ),
    UpdateTestCase(
        "invalid_dot_path",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"a..b": 1}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Should error when $pull field has invalid dot-path",
    ),
    UpdateTestCase(
        "empty_field_name",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pull": {"": 1}},
        error_code=EMPTY_FIELD_NAME_ERROR,
        msg="Should error when $pull field name is empty",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PULL_ERROR_TESTS))
def test_pull_errors(collection, test: UpdateTestCase):
    """Test $pull operator error cases."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]
