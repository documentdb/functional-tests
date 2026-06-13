"""Tests for timeseries collection view-like operation restrictions."""

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
from documentdb_tests.framework.target_collection import TimeseriesCollection

# Property [View-Like Command Rejections]: dataSize is not supported on
# timeseries collections.
VIEW_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "datasize_rejected",
        target_collection=TimeseriesCollection(
            timeseries_options={"timeField": "time", "metaField": "meta"}
        ),
        command=lambda ctx: {"dataSize": f"{ctx.database}.{ctx.collection}"},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Should reject dataSize on timeseries",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VIEW_REJECTION_TESTS))
def test_timeseries_view_restriction_cases(database_client, collection, test):
    """Test timeseries view-like restriction cases."""
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
