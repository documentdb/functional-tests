"""Tests for listCollections command."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Filter Type Errors]: when filter is a non-document BSON
# type, the command produces a TYPE_MISMATCH_ERROR.
FILTER_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="filter_string",
        command={"listCollections": 1, "filter": "hello"},
        msg="filter=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_int32",
        command={"listCollections": 1, "filter": 42},
        msg="filter=int32 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_int64",
        command={"listCollections": 1, "filter": Int64(42)},
        msg="filter=Int64 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_double",
        command={"listCollections": 1, "filter": 3.14},
        msg="filter=double should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_decimal128",
        command={"listCollections": 1, "filter": Decimal128("99")},
        msg="filter=Decimal128 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_bool",
        command={"listCollections": 1, "filter": True},
        msg="filter=bool should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_empty_array",
        command={"listCollections": 1, "filter": []},
        msg="filter=[] should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_array_string",
        command={"listCollections": 1, "filter": ["a"]},
        msg='filter=["a"] should produce TYPE_MISMATCH_ERROR',
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_array_doc",
        command={"listCollections": 1, "filter": [{}]},
        msg="filter=[{}] should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_objectid",
        command=lambda _: {"listCollections": 1, "filter": ObjectId()},
        msg="filter=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_datetime",
        command={"listCollections": 1, "filter": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="filter=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_timestamp",
        command={"listCollections": 1, "filter": Timestamp(1, 1)},
        msg="filter=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_binary",
        command={"listCollections": 1, "filter": Binary(b"hello")},
        msg="filter=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_regex",
        command={"listCollections": 1, "filter": Regex(".*")},
        msg="filter=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_code",
        command={"listCollections": 1, "filter": Code("function(){}")},
        msg="filter=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_code_with_scope",
        command={"listCollections": 1, "filter": Code("function(){}", {"x": 1})},
        msg="filter=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_minkey",
        command={"listCollections": 1, "filter": MinKey()},
        msg="filter=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="filter_maxkey",
        command={"listCollections": 1, "filter": MaxKey()},
        msg="filter=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(FILTER_TYPE_ERROR_TESTS))
def test_listCollections_type_errors_filter(database_client, collection, test):
    """Test listCollections command input acceptance and output structure."""
    target = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(target)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
