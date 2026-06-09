"""Tests for update command field type validation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class FieldValidationTest(BaseTestCase):
    """Test case for update command field validation errors."""

    command: Any = None


# Property [Command Field Rejection]: update command rejects invalid BSON types for
# the collection name field, query field, update field, let field, and unknown fields.
TESTS: list[FieldValidationTest] = [
    FieldValidationTest(
        "update_field_rejects_int",
        command={"update": 123, "updates": [{"q": {}, "u": {"$set": {"x": 1}}}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="update should reject integer type for collection name field.",
    ),
    FieldValidationTest(
        "update_field_rejects_bool",
        command={"update": True, "updates": [{"q": {}, "u": {"$set": {"x": 1}}}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="update should reject boolean type for collection name field.",
    ),
    FieldValidationTest(
        "update_field_rejects_array",
        command={"update": ["coll"], "updates": [{"q": {}, "u": {"$set": {"x": 1}}}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="update should reject array type for collection name field.",
    ),
    FieldValidationTest(
        "q_field_rejects_string",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="update should reject string type for q field.",
    ),
    FieldValidationTest(
        "q_field_rejects_array",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="update should reject array type for q field.",
    ),
    FieldValidationTest(
        "u_field_rejects_string",
        command=None,
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update should reject string type for u field.",
    ),
    FieldValidationTest(
        "missing_q_field",
        command=None,
        error_code=MISSING_FIELD_ERROR,
        msg="update should reject update statement missing q field.",
    ),
    FieldValidationTest(
        "unrecognized_field",
        command=None,
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="update should reject unrecognized fields in command document.",
    ),
    FieldValidationTest(
        "let_field_rejects_array",
        command=None,
        error_code=TYPE_MISMATCH_ERROR,
        msg="update should reject array type for let field.",
    ),
    FieldValidationTest(
        "empty_updates_array",
        command=None,
        error_code=16,
        msg="update should reject empty updates array.",
    ),
]

# Commands that need collection.name substituted at runtime.
_DYNAMIC_COMMANDS = {
    "q_field_rejects_string": lambda n: {
        "update": n,
        "updates": [{"q": "invalid", "u": {"$set": {"x": 1}}}],
    },
    "q_field_rejects_array": lambda n: {
        "update": n,
        "updates": [{"q": [1, 2], "u": {"$set": {"x": 1}}}],
    },
    "u_field_rejects_string": lambda n: {
        "update": n,
        "updates": [{"q": {"_id": 1}, "u": "invalid"}],
    },
    "missing_q_field": lambda n: {"update": n, "updates": [{"u": {"$set": {"x": 1}}}]},
    "unrecognized_field": lambda n: {
        "update": n,
        "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 1}}}],
        "unknownField": 1,
    },
    "let_field_rejects_array": lambda n: {
        "update": n,
        "updates": [{"q": {"_id": 1}, "u": {"$set": {"x": 1}}}],
        "let": [1, 2, 3],
    },
    "empty_updates_array": lambda n: {"update": n, "updates": []},
}


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_update_field_validation(collection, test: FieldValidationTest):
    """Test update command rejects invalid field types."""
    if test.command is not None:
        cmd = test.command
    else:
        cmd = _DYNAMIC_COMMANDS[test.id](collection.name)
    result = execute_command(collection, cmd)
    assertResult(result, error_code=test.error_code, msg=test.msg)
