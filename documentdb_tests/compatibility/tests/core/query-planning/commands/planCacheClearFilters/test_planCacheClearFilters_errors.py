"""Tests for planCacheClearFilters command error cases."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
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

# Property [View Rejection]: planCacheClearFilters is not supported on views.
CLEAR_FILTERS_VIEW_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_rejection",
        target_collection=ViewCollection(),
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheClearFilters should be rejected on a view",
    ),
]

# Property [Timeseries Rejection]: planCacheClearFilters is not supported on
# timeseries collections.
CLEAR_FILTERS_TIMESERIES_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "timeseries_rejection",
        target_collection=TimeseriesCollection(),
        docs=[],
        command=lambda ctx: {"planCacheClearFilters": ctx.collection},
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheClearFilters should be rejected on a timeseries collection",
    ),
]

# Property [Field Type Rejection]: all non-string BSON types for the
# planCacheClearFilters field produce an invalid namespace error.
CLEAR_FILTERS_NAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_type_int32",
        command={"planCacheClearFilters": 123},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="int32 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_int64",
        command={"planCacheClearFilters": Int64(1)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Int64 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_double",
        command={"planCacheClearFilters": 1.5},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="double collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_decimal128",
        command={"planCacheClearFilters": Decimal128("1")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Decimal128 collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_bool_true",
        command={"planCacheClearFilters": True},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="bool true collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_bool_false",
        command={"planCacheClearFilters": False},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="bool false collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_null",
        command={"planCacheClearFilters": None},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="null collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_array",
        command={"planCacheClearFilters": []},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="array collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_object",
        command={"planCacheClearFilters": {}},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="object collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_objectid",
        command={"planCacheClearFilters": ObjectId()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="ObjectId collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_binary",
        command={"planCacheClearFilters": Binary(b"\x00")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Binary collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_datetime",
        command={"planCacheClearFilters": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="datetime collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_timestamp",
        command={"planCacheClearFilters": Timestamp(0, 0)},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Timestamp collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_regex",
        command={"planCacheClearFilters": Regex(".*")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Regex collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_code",
        command={"planCacheClearFilters": Code("function(){}")},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Code collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_minkey",
        command={"planCacheClearFilters": MinKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MinKey collection name should be rejected as invalid type",
    ),
    CommandTestCase(
        "name_type_maxkey",
        command={"planCacheClearFilters": MaxKey()},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="MaxKey collection name should be rejected as invalid type",
    ),
]

# Property [Namespace Edge Cases]: empty string and null byte collection
# names produce an invalid namespace error.
CLEAR_FILTERS_NAME_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_empty_string",
        command={"planCacheClearFilters": ""},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Empty string collection name should be rejected",
    ),
    CommandTestCase(
        "name_null_byte_embedded",
        command={"planCacheClearFilters": "test\x00coll"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="Null byte embedded in collection name should be rejected",
    ),
]

CLEAR_FILTERS_ERROR_TESTS: list[CommandTestCase] = (
    CLEAR_FILTERS_VIEW_REJECTION_TESTS
    + CLEAR_FILTERS_TIMESERIES_REJECTION_TESTS
    + CLEAR_FILTERS_NAME_TYPE_ERROR_TESTS
    + CLEAR_FILTERS_NAME_EDGE_CASE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CLEAR_FILTERS_ERROR_TESTS))
def test_planCacheClearFilters_errors(database_client, collection, test):
    """Test planCacheClearFilters command error cases."""
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
