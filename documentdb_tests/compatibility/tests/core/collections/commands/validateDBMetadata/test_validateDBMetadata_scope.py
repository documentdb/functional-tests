"""Tests for validateDBMetadata scope and filtering behavior."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Contains, Eq
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Scope and Filtering]: the db and collection filters use exact
# case-sensitive string matching with no existence check, and views produce
# 0 apiVersionErrors.
VALIDATE_DB_METADATA_SCOPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "scope_nonexistent_db",
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "nonexistent_db_xyz_99",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed with 0 errors for non-existent db",
    ),
    CommandTestCase(
        "scope_nonexistent_db_with_violation",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": "nonexistent_db_xyz_99",
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata db filter should exclude violations from other databases",
    ),
    CommandTestCase(
        "scope_nonexistent_collection",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": "nonexistent_coll_xyz_99",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should succeed with 0 errors for non-existent collection",
    ),
    CommandTestCase(
        "scope_case_sensitive",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection.upper(),
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not match collection name with different case",
    ),
    CommandTestCase(
        "scope_no_partial_match",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection[:5],
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not match partial collection name",
    ),
    CommandTestCase(
        "scope_no_prefix_match",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection + "_extra",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not match collection name with extra suffix",
    ),
    CommandTestCase(
        "scope_no_wildcard_expansion",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": "*",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should treat wildcard characters literally in collection filter",
    ),
    CommandTestCase(
        "scope_no_whitespace_trim",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection + " ",
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not trim whitespace from collection filter",
    ),
    CommandTestCase(
        "scope_view_no_errors",
        target_collection=ViewCollection(),
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should produce 0 errors for views",
    ),
    CommandTestCase(
        "scope_omit_collection",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "apiVersionErrors": Contains("ns", ctx.namespace),
        },
        msg="validateDBMetadata should validate all collections when collection is omitted",
    ),
    CommandTestCase(
        "scope_omit_db",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "apiVersionErrors": Contains("ns", ctx.namespace),
        },
        msg="validateDBMetadata should search all databases when db is omitted",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_SCOPE_TESTS))
def test_validateDBMetadata_scope(database_client, collection, test):
    """Test validateDBMetadata scope and filtering behavior."""
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
