"""Tests for update command error handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class UpdateErrorTest(BaseTestCase):
    """Test case for update command error scenarios."""

    updates: Any = None


# Property [Invalid Operations]: update command rejects invalid operators, mixed
# operator/replacement fields, and deprecated query operators with correct error codes.
TESTS: list[UpdateErrorTest] = [
    UpdateErrorTest(
        "invalid_update_operator",
        updates=[{"q": {"_id": 1}, "u": {"$badop": {"x": 1}}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update should reject non-existent update operator.",
    ),
    UpdateErrorTest(
        "mixed_operators_and_fields",
        updates=[{"q": {"_id": 1}, "u": {"$set": {"x": 2}, "y": 3}}],
        error_code=FAILED_TO_PARSE_ERROR,
        msg="update should reject mixing operator keys with plain fields.",
    ),
    UpdateErrorTest(
        "deprecated_isolated_in_query",
        updates=[{"q": {"$isolated": 1}, "u": {"$set": {"x": 2}}}],
        error_code=BAD_VALUE_ERROR,
        msg="update should reject deprecated $isolated in query.",
    ),
    UpdateErrorTest(
        "deprecated_atomic_in_query",
        updates=[{"q": {"$atomic": 1}, "u": {"$set": {"x": 2}}}],
        error_code=BAD_VALUE_ERROR,
        msg="update should reject deprecated $atomic in query.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_update_errors(collection, test: UpdateErrorTest):
    """Test update command error cases."""
    collection.insert_one({"_id": 1, "x": 1})
    result = execute_command(collection, {"update": collection.name, "updates": test.updates})
    assertResult(result, error_code=test.error_code, msg=test.msg)
