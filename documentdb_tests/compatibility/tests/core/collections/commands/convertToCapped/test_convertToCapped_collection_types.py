"""Tests for convertToCapped command - collection type handling."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Collection Type Success]: convertToCapped returns ok:1.0 on success for
# various collection states including empty, populated, and clustered.
COLLECTION_TYPE_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_collection",
        docs=[],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Empty collection should return ok:1.0",
    ),
    CommandTestCase(
        "populated_collection",
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Populated collection should return ok:1.0",
    ),
    CommandTestCase(
        "clustered_collection",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Clustered collection should return ok:1.0",
    ),
]

# Property [Data Truncation]: when the cap size is smaller than the existing
# data, the command still succeeds.
DATA_TRUNCATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "cap_smaller_than_data",
        docs=[{"_id": i, "x": "a" * 100} for i in range(10)],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 256},
        expected={"ok": 1.0},
        msg="Cap smaller than existing data should succeed",
    ),
]

# Property [Already Capped]: converting an already-capped collection succeeds
# regardless of whether the new size is smaller, equal, or larger.
ALREADY_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "smaller_size",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 2048},
        expected={"ok": 1.0},
        msg="Smaller size on already-capped collection should succeed",
    ),
    CommandTestCase(
        "same_size",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        expected={"ok": 1.0},
        msg="Same size on already-capped collection should succeed",
    ),
    CommandTestCase(
        "larger_size",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 8192},
        expected={"ok": 1.0},
        msg="Larger size on already-capped collection should succeed",
    ),
]

# Property [Collection Existence Errors]: attempting to convert a
# non-existent collection produces a namespace-not-found error.
EXISTENCE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "nonexistent_collection",
        docs=None,
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Non-existent collection should produce a namespace-not-found error",
    ),
]

# Property [Collection Type Errors]: views and timeseries collections
# produce a command-not-supported-on-view error.
COLLECTION_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view",
        target_collection=ViewCollection(),
        docs=None,
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="View should produce a command-not-supported-on-view error",
    ),
    CommandTestCase(
        "timeseries",
        target_collection=TimeseriesCollection(),
        docs=None,
        command=lambda ctx: {"convertToCapped": ctx.collection, "size": 4096},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="Timeseries collection should produce a command-not-supported-on-view error",
    ),
]

CONVERT_TO_CAPPED_COLLECTION_TYPE_TESTS: list[CommandTestCase] = (
    COLLECTION_TYPE_SUCCESS_TESTS
    + DATA_TRUNCATION_TESTS
    + ALREADY_CAPPED_TESTS
    + EXISTENCE_ERROR_TESTS
    + COLLECTION_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(CONVERT_TO_CAPPED_COLLECTION_TYPE_TESTS))
def test_convert_to_capped_collection_types(database_client, collection, test):
    """Test convertToCapped command behavior for various collection types."""
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
