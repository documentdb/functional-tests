"""Tests for planCacheListFilters command error cases."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    TimeseriesCollection,
    ViewCollection,
)

# Property [View Rejection]: planCacheListFilters is not supported on views.
LIST_FILTERS_VIEW_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_rejection",
        target_collection=ViewCollection(),
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheListFilters should be rejected on a view",
    ),
]

# Property [Timeseries Rejection]: planCacheListFilters is not supported on
# timeseries collections.
LIST_FILTERS_TIMESERIES_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_rejection",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheListFilters should be rejected on a timeseries collection",
    ),
]

# Property [Field Type Rejection]: all non-string BSON types for the
# planCacheListFilters field produce an invalid namespace error.
LIST_FILTERS_NAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_type_int32",
        command={"planCacheListFilters": 123},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject int32 collection name",
    ),
    CommandTestCase(
        "name_type_int64",
        command={"planCacheListFilters": Int64(1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject Int64 collection name",
    ),
    CommandTestCase(
        "name_type_double",
        command={"planCacheListFilters": 1.5},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject double collection name",
    ),
    CommandTestCase(
        "name_type_decimal128",
        command={"planCacheListFilters": Decimal128("1")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject Decimal128 collection name",
    ),
    CommandTestCase(
        "name_type_bool_true",
        command={"planCacheListFilters": True},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject bool true collection name",
    ),
    CommandTestCase(
        "name_type_bool_false",
        command={"planCacheListFilters": False},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject bool false collection name",
    ),
    CommandTestCase(
        "name_type_null",
        command={"planCacheListFilters": None},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject null collection name",
    ),
    CommandTestCase(
        "name_type_array",
        command={"planCacheListFilters": []},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject array collection name",
    ),
    CommandTestCase(
        "name_type_object",
        command={"planCacheListFilters": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject object collection name",
    ),
    CommandTestCase(
        "name_type_objectid",
        command={"planCacheListFilters": ObjectId()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject ObjectId collection name",
    ),
    CommandTestCase(
        "name_type_binary",
        command={"planCacheListFilters": Binary(b"\x00")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject Binary collection name",
    ),
    CommandTestCase(
        "name_type_datetime",
        command={"planCacheListFilters": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject datetime collection name",
    ),
    CommandTestCase(
        "name_type_timestamp",
        command={"planCacheListFilters": Timestamp(0, 0)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject Timestamp collection name",
    ),
    CommandTestCase(
        "name_type_regex",
        command={"planCacheListFilters": Regex(".*")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject Regex collection name",
    ),
    CommandTestCase(
        "name_type_code",
        command={"planCacheListFilters": Code("function(){}")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject Code collection name",
    ),
    CommandTestCase(
        "name_type_minkey",
        command={"planCacheListFilters": MinKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject MinKey collection name",
    ),
    CommandTestCase(
        "name_type_maxkey",
        command={"planCacheListFilters": MaxKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject MaxKey collection name",
    ),
]

# Property [Namespace Edge Cases]: empty string and null byte collection
# names produce an invalid namespace error.
LIST_FILTERS_NAME_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_empty_string",
        command={"planCacheListFilters": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject empty string collection name",
    ),
    CommandTestCase(
        "name_null_byte_embedded",
        command={"planCacheListFilters": "test\x00coll"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheListFilters should reject null byte in collection name",
    ),
]

LIST_FILTERS_ERROR_TESTS: list[CommandTestCase] = (
    LIST_FILTERS_VIEW_REJECTION_TESTS
    + LIST_FILTERS_TIMESERIES_REJECTION_TESTS
    + LIST_FILTERS_NAME_TYPE_ERROR_TESTS
    + LIST_FILTERS_NAME_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_ERROR_TESTS))
def test_planCacheListFilters_errors(database_client, collection, test):
    """Test planCacheListFilters command error cases."""
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
