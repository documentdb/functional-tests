"""Tests for validateDBMetadata response structure."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import API_STRICT_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, IsType, NotExists

# Property [Response Structure]: the success response has a fixed shape
# with ok, apiVersionErrors array, and no hasMoreErrors field.
VALIDATE_DB_METADATA_RESPONSE_STRUCTURE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "structure_empty_errors",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "nonexistent_db_structure_test",
        },
        expected={
            "ok": Eq(1.0),
            "apiVersionErrors": IsType("array"),
            "hasMoreErrors": NotExists(),
        },
        msg="validateDBMetadata response should have correct structure with empty errors",
    ),
    CommandTestCase(
        "structure_with_errors",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "apiVersionErrors": IsType("array"),
            "hasMoreErrors": NotExists(),
            "apiVersionErrors.0": Eq(
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_text is not allowed in API version 1.",
                }
            ),
        },
        msg="validateDBMetadata response should have correct structure with error entries",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_RESPONSE_STRUCTURE_TESTS))
def test_validateDBMetadata_response_structure(database_client, collection, test):
    """Test validateDBMetadata response structure."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
