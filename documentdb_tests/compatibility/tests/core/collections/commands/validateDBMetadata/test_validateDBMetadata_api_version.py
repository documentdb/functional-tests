"""Tests for validateDBMetadata API version validation behavior."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import API_STRICT_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [API Version Validation Behavior]: only the exact string "1"
# as apiParameters.version triggers metadata validation.
VALIDATE_DB_METADATA_API_VERSION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "api_version_1_strict_false",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": False},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should report no errors when strict is false",
    ),
    CommandTestCase(
        "api_version_1_strict_false_sparse",
        indexes=[IndexModel([("field", 1)], sparse=True, name="field_sparse")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": False},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should report no errors for sparse index when strict is false",
    ),
    CommandTestCase(
        "api_version_1_deprecation_errors_true",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {
                "version": "1",
                "strict": True,
                "deprecationErrors": True,
            },
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_text is not allowed in API version 1.",
                }
            ],
        },
        msg="validateDBMetadata deprecationErrors should have no additional effect",
    ),
    CommandTestCase(
        "api_version_1_deprecation_errors_only",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {
                "version": "1",
                "strict": False,
                "deprecationErrors": True,
            },
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata deprecationErrors alone should produce no errors",
    ),
    CommandTestCase(
        "api_version_1_both_omitted",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1"},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should default both strict and deprecationErrors to false",
    ),
    CommandTestCase(
        "api_version_2",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "2", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for version 2",
    ),
    CommandTestCase(
        "api_version_empty_string",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for empty version string",
    ),
    CommandTestCase(
        "api_version_leading_space",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": " 1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for version with leading space",
    ),
    CommandTestCase(
        "api_version_trailing_space",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1 ", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for version with trailing space",
    ),
    CommandTestCase(
        "api_version_abc",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "abc", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for arbitrary version string",
    ),
    CommandTestCase(
        "api_version_1_dot_0",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1.0", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for version 1.0",
    ),
    CommandTestCase(
        "api_version_dollar_prefix",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "$1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for dollar-prefix version",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_API_VERSION_TESTS))
def test_validateDBMetadata_api_version(database_client, collection, test):
    """Test validateDBMetadata API version validation behavior."""
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
