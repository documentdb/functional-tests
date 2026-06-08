"""Tests for planCacheClear command collation and collection type support."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    ViewCollection,
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
        "collation_without_query",
        command=lambda ctx: {
            "planCacheClear": ctx.collection,
            "collation": {"locale": "en"},
        },
        expected={"ok": 1.0},
        msg="planCacheClear should accept collation without query",
    ),
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

PLANCACHECLEAR_COLLATION_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_COLLATION_VALID_TESTS + PLANCACHECLEAR_COLLATION_PERMISSIVE_TESTS
)

# Property [Regular Collection]: planCacheClear succeeds on a regular collection.
PLANCACHECLEAR_REGULAR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "regular_with_docs",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheClear": ctx.collection},
        expected={"ok": 1.0},
        msg="planCacheClear should succeed on a regular collection with documents",
    ),
]

# Property [View Rejection]: planCacheClear is not supported on views and
# returns COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR.
PLANCACHECLEAR_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_rejected",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheClear": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheClear should reject views with CommandNotSupportedOnView error",
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

# Property [Timeseries Collection]: planCacheClear is not supported on
# timeseries collections and returns COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR.
PLANCACHECLEAR_TIMESERIES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_rejected",
        target_collection=TimeseriesCollection(),
        command=lambda ctx: {"planCacheClear": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheClear should reject timeseries collection (backed by view)",
    ),
]

PLANCACHECLEAR_COLLECTION_VARIANT_SUCCESS_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_REGULAR_TESTS + PLANCACHECLEAR_CAPPED_TESTS + PLANCACHECLEAR_CLUSTERED_TESTS
)

PLANCACHECLEAR_COLLECTION_VARIANT_ERROR_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_VIEW_TESTS + PLANCACHECLEAR_TIMESERIES_TESTS
)

PLANCACHECLEAR_COLLECTION_VARIANT_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_COLLECTION_VARIANT_SUCCESS_TESTS + PLANCACHECLEAR_COLLECTION_VARIANT_ERROR_TESTS
)

PLANCACHECLEAR_COLLATION_COLLECTION_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_COLLATION_TESTS + PLANCACHECLEAR_COLLECTION_VARIANT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_COLLATION_COLLECTION_TESTS))
def test_planCacheClear_collation_collection(database_client, collection, test):
    """Test planCacheClear collation and collection type support."""
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
