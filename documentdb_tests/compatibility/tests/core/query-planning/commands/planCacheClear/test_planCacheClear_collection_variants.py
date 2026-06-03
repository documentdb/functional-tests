"""Tests for planCacheClear command on different collection types."""

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


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_COLLECTION_VARIANT_TESTS))
def test_planCacheClear_collection_variants(database_client, collection, test):
    """Test planCacheClear command on different collection types."""
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
