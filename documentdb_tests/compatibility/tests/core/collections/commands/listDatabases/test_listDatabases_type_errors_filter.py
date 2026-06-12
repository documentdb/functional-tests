"""Tests for listDatabases filter type strictness."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DECIMAL128_ZERO, INT64_ZERO

# Property [filter Type Strictness]: filter rejects all non-document,
# non-null BSON types with a TypeMismatch error.
FILTER_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "filter": "bad"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with string should produce TypeMismatch",
        id="filter_type_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with int32 should produce TypeMismatch",
        id="filter_type_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": INT64_ZERO},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with Int64 should produce TypeMismatch",
        id="filter_type_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with double should produce TypeMismatch",
        id="filter_type_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": DECIMAL128_ZERO},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with Decimal128 should produce TypeMismatch",
        id="filter_type_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with bool should produce TypeMismatch",
        id="filter_type_bool",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": []},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with empty array should produce TypeMismatch",
        id="filter_type_empty_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with non-empty array should produce TypeMismatch",
        id="filter_type_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with ObjectId should produce TypeMismatch",
        id="filter_type_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with datetime should produce TypeMismatch",
        id="filter_type_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": Timestamp(0, 0)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with Timestamp should produce TypeMismatch",
        id="filter_type_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with Binary should produce TypeMismatch",
        id="filter_type_binary",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": Regex("^x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with Regex should produce TypeMismatch",
        id="filter_type_regex",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with Code should produce TypeMismatch",
        id="filter_type_code",
    ),
    CommandTestCase(
        command={
            "listDatabases": 1,
            "filter": Code("function(){}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with CodeWithScope should produce TypeMismatch",
        id="filter_type_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with MinKey should produce TypeMismatch",
        id="filter_type_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "filter": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="filter with MaxKey should produce TypeMismatch",
        id="filter_type_maxkey",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_TYPE_ERROR_TESTS))
def test_listDatabases_type_errors_filter(collection, test):
    """Test listDatabases filter type strictness."""
    ctx = CommandContext.from_collection(collection)
    collection.database.create_collection(collection.name)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
