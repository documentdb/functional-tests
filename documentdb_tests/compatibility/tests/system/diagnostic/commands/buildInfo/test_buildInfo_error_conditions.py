"""Tests for buildInfo command error conditions.

Validates that invalid usages of buildInfo produce appropriate errors.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.executor import execute_admin_command, execute_command

pytestmark = pytest.mark.admin


def test_buildInfo_as_aggregation_stage_fails(collection):
    """Test running buildInfo as an aggregation stage fails with unrecognized stage error."""
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [{"$buildInfo": {}}], "cursor": {}},
    )
    assertFailureCode(result, 40324, msg="$buildInfo is not a valid aggregation stage")


def test_buildInfo_case_sensitive(collection):
    """Test buildInfo command name is case-sensitive — 'BuildInfo' should fail."""
    result = execute_admin_command(collection, {"BuildInfo": 1})
    assertFailureCode(result, 59, msg="Case-mismatched command name should fail")
