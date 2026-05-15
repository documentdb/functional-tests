"""Tests for cloneCollectionAsCapped source and destination collection types."""

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    ILLEGAL_OPERATION_ERROR,
    NAMESPACE_EXISTS_ERROR,
    NAMESPACE_NOT_FOUND_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    SystemBucketsCollection,
    TimeseriesCollection,
    ViewCollection,
)

# Property [Source Non-Existent]: a non-existent source collection
# produces NAMESPACE_NOT_FOUND_ERROR.
SOURCE_NON_EXISTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_existent_collection",
        docs=None,
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Non-existent source should fail with namespace not found",
    ),
    CommandTestCase(
        "namespace_exceeds_255_bytes",
        command=lambda ctx: {
            "cloneCollectionAsCapped": "x" * (255 - len(ctx.database) - 1 + 1),
            "toCollection": "dest",
            "size": 100_000,
        },
        error_code=NAMESPACE_NOT_FOUND_ERROR,
        msg="Source name exceeding 255-byte namespace limit should fail with namespace not found",
    ),
]

# Property [Destination Already Exists]: a destination collection that
# already exists produces NAMESPACE_EXISTS_ERROR.
DEST_ALREADY_EXISTS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "same_name_source_and_dest",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": ctx.collection,
            "size": 100_000,
        },
        error_code=NAMESPACE_EXISTS_ERROR,
        msg="Same name for source and destination should fail with namespace exists",
    ),
]

# Property [Source Collection Type Rejection]: views, timeseries, and
# timeseries backing collections are rejected as source.
SOURCE_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_as_source",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="A view as source should fail with command not supported on view",
    ),
    CommandTestCase(
        "timeseries_as_source",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="A timeseries collection as source should fail with command not supported on view",
    ),
    CommandTestCase(
        "system_buckets_source",
        target_collection=SystemBucketsCollection(),
        docs=[],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.buckets.* as source should be rejected as timeseries backing collection",
    ),
]

# Property [Destination is a View]: a view as destination produces
# COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR.
DEST_IS_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "dest_is_view",
        target_collection=ViewCollection(),
        docs=[],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection.removesuffix("_view"),
            "toCollection": ctx.collection,
            "size": 100_000,
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="A view as destination should produce view error, not namespace exists",
    ),
]

# Property [Source Collection Types - Success Cases]: the command
# succeeds for various source collection types.
SOURCE_COLLECTION_TYPES_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "empty_source",
        docs=[],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="Empty source should create an empty capped destination",
    ),
    CommandTestCase(
        "capped_source",
        target_collection=CappedCollection(size=100_000),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="Capped collection as source should succeed",
    ),
    CommandTestCase(
        "clustered_source",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": f"{ctx.collection}_dest",
            "size": 100_000,
        },
        expected={"ok": 1.0},
        msg="Clustered collection as source should succeed",
    ),
]

# Property [System Buckets Destination Without Timeseries]: creating a
# capped collection named system.buckets.X when no timeseries
# collection X exists is rejected with ILLEGAL_OPERATION_ERROR.
SYSTEM_BUCKETS_DEST_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "system_buckets_dest_no_timeseries",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "cloneCollectionAsCapped": ctx.collection,
            "toCollection": "system.buckets.nonexistent",
            "size": 100_000,
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="system.buckets.X as dest without timeseries X should fail",
    ),
]

COLLECTION_TYPES_TESTS: list[CommandTestCase] = (
    SOURCE_NON_EXISTENT_TESTS
    + DEST_ALREADY_EXISTS_TESTS
    + SOURCE_TYPE_REJECTION_TESTS
    + DEST_IS_VIEW_TESTS
    + SOURCE_COLLECTION_TYPES_SUCCESS_TESTS
    + SYSTEM_BUCKETS_DEST_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COLLECTION_TYPES_TESTS))
def test_clone_collection_as_capped_collection_types(database_client, collection, test):
    """Test cloneCollectionAsCapped source and destination collection types."""
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
