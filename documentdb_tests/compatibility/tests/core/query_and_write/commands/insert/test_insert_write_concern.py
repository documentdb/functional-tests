"""
Insert writeConcern tests.

Tests writeConcern parameter behavior including w values and invalid types.
"""

from dataclasses import dataclass
from typing import Any

import pytest

from documentdb_tests.framework.assertions import assertNotError, assertResult, assertSuccessPartial
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_case import BaseTestCase


@dataclass(frozen=True)
class WriteConcernTest(BaseTestCase):
    """Test case for writeConcern parameter behavior."""

    write_concern: Any = None


# Property [writeConcern Acceptance]: insert accepts document writeConcern values
# including w:1, w:'majority', j:true, j:false, null, and empty object.
# All produce a normal n=1 success response. null is treated as the server default.
# w:0 (unacknowledged) is tested separately as it returns no acknowledgment.
VALID_WRITE_CONCERN_TESTS: list[WriteConcernTest] = [
    WriteConcernTest(
        "w1",
        write_concern={"w": 1},
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed with writeConcern w:1.",
    ),
    WriteConcernTest(
        "w_majority",
        write_concern={"w": "majority"},
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed with writeConcern w:'majority'.",
    ),
    WriteConcernTest(
        "j_true",
        write_concern={"w": 1, "j": True},
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed with writeConcern j:true.",
    ),
    WriteConcernTest(
        "j_false",
        write_concern={"w": 1, "j": False},
        expected={"ok": 1.0, "n": 1},
        msg="insert should succeed with writeConcern j:false.",
    ),
    WriteConcernTest(
        "empty_object",
        write_concern={},
        expected={"ok": 1.0, "n": 1},
        msg="insert should accept an empty writeConcern object as the default.",
    ),
    WriteConcernTest(
        "null",
        write_concern=None,
        expected={"ok": 1.0, "n": 1},
        msg="insert should accept null writeConcern as the default.",
    ),
]

# Property [writeConcern Type Rejection]: non-document types are rejected.
# null is accepted (see above). string, int, bool, and array are rejected.
INVALID_WRITE_CONCERN_TESTS: list[WriteConcernTest] = [
    WriteConcernTest(
        "rejects_string",
        write_concern="majority",
        error_code=TYPE_MISMATCH_ERROR,
        msg="insert should reject string writeConcern.",
    ),
    WriteConcernTest(
        "rejects_int",
        write_concern=1,
        error_code=TYPE_MISMATCH_ERROR,
        msg="insert should reject integer writeConcern.",
    ),
    WriteConcernTest(
        "rejects_bool",
        write_concern=True,
        error_code=TYPE_MISMATCH_ERROR,
        msg="insert should reject boolean writeConcern.",
    ),
    WriteConcernTest(
        "rejects_array",
        write_concern=[{"w": 1}],
        error_code=TYPE_MISMATCH_ERROR,
        msg="insert should reject array writeConcern.",
    ),
]


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(VALID_WRITE_CONCERN_TESTS))
def test_insert_write_concern_valid(collection, test: WriteConcernTest):
    """Test insert succeeds with accepted writeConcern values."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1}],
            "writeConcern": test.write_concern,
        },
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.insert
@pytest.mark.parametrize("test", pytest_params(INVALID_WRITE_CONCERN_TESTS))
def test_insert_write_concern_invalid(collection, test: WriteConcernTest):
    """Test insert rejects non-document writeConcern types."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1}],
            "writeConcern": test.write_concern,
        },
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


@pytest.mark.insert
def test_insert_write_concern_w0(collection):
    """Test insert with writeConcern w:0 (unacknowledged) does not error."""
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1}],
            "writeConcern": {"w": 0},
        },
    )
    assertNotError(result, msg="insert should not error with writeConcern w:0.")
