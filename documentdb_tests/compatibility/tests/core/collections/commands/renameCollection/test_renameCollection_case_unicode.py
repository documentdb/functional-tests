"""Tests for renameCollection case sensitivity and Unicode normalization."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.renameCollection.utils.renameCollection_common import (  # noqa: E501
    cross_db_cleanup_ns,
)
from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import (
    assertResult,
)
from documentdb_tests.framework.error_codes import (
    DATABASE_DIFFER_CASE_ERROR,
    NAMESPACE_EXISTS_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    NamedCollection,
    SiblingCollection,
)

# Property [Case Sensitivity - Names]: database and collection names
# are fully case-sensitive; no case folding is applied.
RENAME_CASE_SENSITIVITY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "case_rename_differs_only_in_case",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection.upper()}",
        },
        expected={"ok": 1.0},
        msg="Rename to name differing only in case should succeed (no case folding)",
    ),
]

# Property [Case Sensitivity - Unicode Normalization]: no Unicode
# normalization is applied; precomposed and decomposed forms are
# treated as distinct names and can coexist.
RENAME_UNICODE_NORMALIZATION_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unicode_no_normalization",
        # Source is the fixture collection. Target U+0065 U+0301 (decomposed)
        # already exists as a sibling, so rename fails with NAMESPACE_EXISTS.
        # If normalization were applied, the server might treat the names as
        # equivalent and produce a different error.
        docs=[{"_id": 1}],
        siblings=[SiblingCollection(suffix="_e\u0301", docs=[{"_id": 2}])],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection}_e\u0301",
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Decomposed Unicode target exists; rename should fail with target exists",
    ),
]

# Property [Case Sensitivity - Unicode Rename]: precomposed and
# decomposed forms are distinct names; renaming between them succeeds.
RENAME_UNICODE_NORMALIZATION_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unicode_precomposed_to_decomposed",
        # U+00E9 precomposed source renamed to U+0065 U+0301 decomposed target.
        target_collection=NamedCollection(suffix="_\u00e9"),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database}.{ctx.collection[:-1]}e\u0301",
        },
        expected={"ok": 1.0},
        msg="Renaming from precomposed to decomposed should succeed (distinct names)",
    ),
]

# Property [Case Sensitivity - Database Case Conflict]: renaming to a
# target in a database that exists with different case produces a
# database-differ-case error.
RENAME_DATABASE_CASE_CONFLICT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "case_conflict_db_lower_to_upper",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "renameCollection": ctx.namespace,
            "to": f"{ctx.database.upper()}.{ctx.collection}_dest",
        },
        error_code=DATABASE_DIFFER_CASE_ERROR,
        msg="Renaming to a database with different case should be rejected",
    ),
]

RENAME_CASE_UNICODE_TESTS: list[CommandTestCase] = (
    RENAME_CASE_SENSITIVITY_TESTS
    + RENAME_UNICODE_NORMALIZATION_ERROR_TESTS
    + RENAME_UNICODE_NORMALIZATION_SUCCESS_TESTS
    + RENAME_DATABASE_CASE_CONFLICT_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(RENAME_CASE_UNICODE_TESTS))
def test_renameCollection_case_unicode(database_client, collection, register_db_cleanup, test):
    """Test renameCollection case sensitivity and Unicode normalization."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    cmd = test.build_command(ctx)
    cross_db_cleanup_ns(cmd, ctx, register_db_cleanup)
    result = execute_admin_command(collection, cmd)
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
