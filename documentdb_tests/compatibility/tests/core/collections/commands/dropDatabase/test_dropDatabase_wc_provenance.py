from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Provenance Accepted Values]: the provenance
# field accepts only the defined provenance source identifiers.
WRITE_CONCERN_PROVENANCE_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"provenance": "clientSupplied"}},
        expected={"ok": 1.0},
        msg="provenance:clientSupplied should be accepted",
        id="provenance_client_supplied",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"provenance": "implicitDefault"}},
        expected={"ok": 1.0},
        msg="provenance:implicitDefault should be accepted",
        id="provenance_implicit_default",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"provenance": "customDefault"}},
        expected={"ok": 1.0},
        msg="provenance:customDefault should be accepted",
        id="provenance_custom_default",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"provenance": "getLastErrorDefaults"}},
        expected={"ok": 1.0},
        msg="provenance:getLastErrorDefaults should be accepted",
        id="provenance_get_last_error_defaults",
    ),
]

# Property [writeConcern Provenance Invalid Values]: invalid provenance
# values produce a bad value error.
WRITE_CONCERN_PROVENANCE_INVALID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"provenance": "invalid"}},
        error_code=BAD_VALUE_ERROR,
        msg="provenance:invalid should produce a bad value error",
        id="provenance_invalid",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"provenance": ""}},
        error_code=BAD_VALUE_ERROR,
        msg="provenance:empty string should produce a bad value error",
        id="provenance_empty_string",
    ),
]

WRITE_CONCERN_PROVENANCE_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_PROVENANCE_ACCEPTED_TESTS + WRITE_CONCERN_PROVENANCE_INVALID_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_PROVENANCE_TESTS))
def test_dropDatabase_wc_provenance(database_client, collection, register_db_cleanup, test):
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
