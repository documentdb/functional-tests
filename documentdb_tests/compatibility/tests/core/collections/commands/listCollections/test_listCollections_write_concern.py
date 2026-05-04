"""Tests for listCollections writeConcern behavior."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Unsupported]: when writeConcern is a valid
# document, the command produces INVALID_OPTIONS_ERROR because write
# concern is not supported for this command.
WRITE_CONCERN_UNSUPPORTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listCollections": 1, "writeConcern": {"w": 1}},
        msg="writeConcern={w: 1} should produce INVALID_OPTIONS_ERROR",
        id="write_concern_w_1",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "writeConcern": {}},
        msg="writeConcern={} should produce INVALID_OPTIONS_ERROR",
        id="write_concern_empty_doc",
        error_code=INVALID_OPTIONS_ERROR,
    ),
]

# Property [writeConcern Type Errors]: when writeConcern is a
# non-document BSON type, the command produces a TYPE_MISMATCH_ERROR.
WRITE_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="write_concern_int32",
        command={"listCollections": 1, "writeConcern": 42},
        msg="writeConcern=int32 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_int64",
        command={"listCollections": 1, "writeConcern": Int64(42)},
        msg="writeConcern=Int64 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_double",
        command={"listCollections": 1, "writeConcern": 3.14},
        msg="writeConcern=double should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_decimal128",
        command={"listCollections": 1, "writeConcern": Decimal128("99")},
        msg="writeConcern=Decimal128 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_bool",
        command={"listCollections": 1, "writeConcern": True},
        msg="writeConcern=bool should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_string",
        command={"listCollections": 1, "writeConcern": "hello"},
        msg="writeConcern=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_array",
        command={"listCollections": 1, "writeConcern": [{"w": 1}]},
        msg="writeConcern=array should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_objectid",
        command=lambda _: {"listCollections": 1, "writeConcern": ObjectId()},
        msg="writeConcern=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_datetime",
        command={"listCollections": 1, "writeConcern": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="writeConcern=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_timestamp",
        command={"listCollections": 1, "writeConcern": Timestamp(1, 1)},
        msg="writeConcern=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_binary",
        command={"listCollections": 1, "writeConcern": Binary(b"hello")},
        msg="writeConcern=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_regex",
        command={"listCollections": 1, "writeConcern": Regex(".*")},
        msg="writeConcern=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_code",
        command={"listCollections": 1, "writeConcern": Code("function(){}")},
        msg="writeConcern=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_code_with_scope",
        command={"listCollections": 1, "writeConcern": Code("function(){}", {"x": 1})},
        msg="writeConcern=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_minkey",
        command={"listCollections": 1, "writeConcern": MinKey()},
        msg="writeConcern=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="write_concern_maxkey",
        command={"listCollections": 1, "writeConcern": MaxKey()},
        msg="writeConcern=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

WRITE_CONCERN_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_UNSUPPORTED_TESTS + WRITE_CONCERN_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_TESTS))
def test_listCollections_write_concern(database_client, collection, test):
    """Test listCollections writeConcern behavior."""
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
