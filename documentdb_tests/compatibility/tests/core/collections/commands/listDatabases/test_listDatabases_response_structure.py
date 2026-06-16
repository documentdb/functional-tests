"""Tests for listDatabases response structure."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    full_structure_success,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.test_constants import INT64_ZERO

# Property [Full Response Structure]: when nameOnly is false or
# omitted, the response contains databases (array), totalSize (Int64),
# totalSizeMb (Int64), and ok (double 1.0), and each database entry
# contains name (string), sizeOnDisk (Int64), and empty (bool).
FULL_RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1},
        expected=full_structure_success,
        msg="Full response should have databases, totalSize, totalSizeMb, ok",
        id="full_response_top_level_keys",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "nameOnly": False},
        expected=full_structure_success,
        msg="Explicit nameOnly=false should produce full response structure",
        id="full_response_name_only_false",
    ),
]

# Property [Empty Result Structure]: when the filter matches no
# databases, the response contains an empty databases array with
# appropriate fields depending on nameOnly.
EMPTY_RESULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": "nonexistent_db_xyz_99999"},
        },
        expected={
            "ok": Eq(1.0),
            "databases": Eq([]),
            "totalSize": Eq(INT64_ZERO),
            "totalSizeMb": Eq(INT64_ZERO),
        },
        msg="Empty result with nameOnly=false should have totalSize=0 and totalSizeMb=0",
        id="empty_result_full",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": {"name": "nonexistent_db_xyz_99999"},
            "nameOnly": True,
        },
        expected={"ok": Eq(1.0), "databases": Eq([])},
        msg="Empty result with nameOnly=true should have only databases and ok",
        id="empty_result_name_only",
    ),
]

RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = FULL_RESPONSE_STRUCTURE_TESTS + EMPTY_RESULT_TESTS


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RESPONSE_STRUCTURE_TESTS))
def test_listDatabases_response_structure(collection, test):
    """Test listDatabases response structure."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
