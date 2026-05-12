from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import FAILED_TO_PARSE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern fsync and j Combination]: all combinations of
# fsync and j succeed except fsync:true with j:true.
WRITE_CONCERN_FSYNC_J_COMBINATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": False, "j": False}},
        expected={"ok": 1.0},
        msg="fsync:false with j:false should succeed",
        id="fsync_false_j_false",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": True, "j": False}},
        expected={"ok": 1.0},
        msg="fsync:true with j:false should succeed",
        id="fsync_true_j_false",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": False, "j": True}},
        expected={"ok": 1.0},
        msg="fsync:false with j:true should succeed",
        id="fsync_false_j_true",
    ),
]

# Property [writeConcern fsync and j Conflict]: fsync:true combined
# with j:true produces a parse error because they cannot be used together.
WRITE_CONCERN_FSYNC_J_CONFLICT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"fsync": True, "j": True}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="fsync:true with j:true should produce a parse error",
        id="fsync_true_j_true",
    ),
]

WRITE_CONCERN_FSYNC_J_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_FSYNC_J_COMBINATION_TESTS + WRITE_CONCERN_FSYNC_J_CONFLICT_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_FSYNC_J_TESTS))
def test_dropDatabase_wc_fsync_j(database_client, collection, register_db_cleanup, test):
    """Test dropDatabase command inputs and error handling."""
    coll = test.prepare(database_client, collection)
    result = execute_command(coll, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
