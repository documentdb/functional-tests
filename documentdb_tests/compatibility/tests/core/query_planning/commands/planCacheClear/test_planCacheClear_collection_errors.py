"""Tests for planCacheClear command collection type error cases."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    TimeseriesCollection,
    ViewCollection,
)

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

PLANCACHECLEAR_COLLECTION_ERROR_TESTS: list[CommandTestCase] = (
    PLANCACHECLEAR_VIEW_TESTS + PLANCACHECLEAR_TIMESERIES_TESTS
)


@pytest.mark.parametrize("test", pytest_params(PLANCACHECLEAR_COLLECTION_ERROR_TESTS))
def test_planCacheClear_collection_errors(database_client, collection, test):
    """Test planCacheClear command collection type error cases."""
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
