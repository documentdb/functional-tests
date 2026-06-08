"""Tests for planCacheClear command collation and collection type success cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
)

# Property [Collation Valid]: planCacheClear accepts valid collation with query.
PLANCACHECLEAR_COLLATION_VALID_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_valid_en",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept collation with locale 'en'",
    ),
    CommandTestCase(
        "collation_valid_fr_strength",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": {"locale": "fr", "strength": 2},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept collation with locale 'fr' and strength 2",
    ),
]

# Property [Collation Permissiveness]: collation accepts values that would
# normally be invalid because MongoDB silently accepts them.
PLANCACHECLEAR_COLLATION_PERMISSIVE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_empty",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": {},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept empty collation document",
    ),
    CommandTestCase(
        "collation_type_string",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": "en",
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept string as collation field",
    ),
    CommandTestCase(
        "collation_type_int",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": 123,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept int as collation field",
    ),
    CommandTestCase(
        "collation_type_bool",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": True,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept bool as collation field",
    ),
    CommandTestCase(
        "collation_type_array",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": [1],
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept array as collation field",
    ),
    CommandTestCase(
        "collation_type_null",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "query": {"a": 1},
            "collation": None,
        },
        expected={"ok": 1.0},
        msg="planCacheClear should treat null collation as omitted",
    ),
]

# Property [Capped Collection]: planCacheClear succeeds on capped collections.
PLANCACHECLEAR_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_success",
        target_collection=CappedCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed on a capped collection",
    ),
]

# Property [Clustered Collection]: planCacheClear succeeds on clustered collections.
PLANCACHECLEAR_CLUSTERED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clustered_success",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed on a clustered collection",
    ),
]

PLANCACHECLEAR_COLLATION_COLLECTION_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_COLLATION_VALID_TESTS
    + PLANCACHECLEAR_COLLATION_PERMISSIVE_TESTS
    + PLANCACHECLEAR_CAPPED_TESTS
    + PLANCACHECLEAR_CLUSTERED_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_COLLATION_COLLECTION_TESTS))
def test_planCacheClear_collation_collection(database_client, collection, test):
    """Test planCacheClear collation and collection type success cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
