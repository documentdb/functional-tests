"""Tests for dbStats command error conditions.

Covers value-level errors (BadValue for invalid scale values) and
command-level errors (unrecognized fields). Type-level rejections
(TypeMismatch for invalid scale types) are in test_dbStats_argument_handling.py.
"""

import pytest
from bson import SON

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, UNRECOGNIZED_COMMAND_FIELD_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.admin


INVALID_SCALE_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "zero",
        command={"dbStats": 1, "scale": 0},
        error_code=BAD_VALUE_ERROR,
        msg="scale=0 should error with BadValue",
    ),
    DiagnosticTestCase(
        "negative_int",
        command={"dbStats": 1, "scale": -1},
        error_code=BAD_VALUE_ERROR,
        msg="Negative int scale should error with BadValue",
    ),
    DiagnosticTestCase(
        "fractional_lt_1",
        command={"dbStats": 1, "scale": 0.5},
        error_code=BAD_VALUE_ERROR,
        msg="Fractional scale < 1 should error with BadValue",
    ),
    DiagnosticTestCase(
        "duplicate_keys_last_invalid",
        command=SON([("dbStats", 1), ("scale", 1024), ("scale", -1)]),
        error_code=BAD_VALUE_ERROR,
        msg="Invalid last duplicate scale value should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INVALID_SCALE_TESTS))
def test_dbStats_invalid_scale_errors(collection, test):
    """Test dbStats rejects invalid (non-positive/truncate-to-zero) scale values with BadValue."""
    result = execute_command(collection, test.command)
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_dbStats_unrecognized_field_errors(collection):
    """Test dbStats rejects an unrecognized command field."""
    collection.insert_one({"_id": 1})
    result = execute_command(collection, {"dbStats": 1, "bogusField": 1})
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized command field should error with code 40415",
    )
