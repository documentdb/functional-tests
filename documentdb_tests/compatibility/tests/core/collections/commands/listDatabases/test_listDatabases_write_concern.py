"""Tests for listDatabases writeConcern behavior."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR, TYPE_MISMATCH_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Type Strictness]: writeConcern with a
# non-document type produces a TypeMismatch error.
WRITE_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with int32 should produce TypeMismatch",
        id="write_concern_type_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with Int64 should produce TypeMismatch",
        id="write_concern_type_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": 3.14},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with double should produce TypeMismatch",
        id="write_concern_type_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Decimal128("99")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with Decimal128 should produce TypeMismatch",
        id="write_concern_type_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with bool should produce TypeMismatch",
        id="write_concern_type_bool",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": "bad"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with string should produce TypeMismatch",
        id="write_concern_type_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": [{"w": 1}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with array should produce TypeMismatch",
        id="write_concern_type_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with ObjectId should produce TypeMismatch",
        id="write_concern_type_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with datetime should produce TypeMismatch",
        id="write_concern_type_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with Timestamp should produce TypeMismatch",
        id="write_concern_type_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with Binary should produce TypeMismatch",
        id="write_concern_type_binary",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with Regex should produce TypeMismatch",
        id="write_concern_type_regex",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with Code should produce TypeMismatch",
        id="write_concern_type_code",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": Code("function(){}", {"x": 1})},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with CodeWithScope should produce TypeMismatch",
        id="write_concern_type_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with MinKey should produce TypeMismatch",
        id="write_concern_type_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="writeConcern with MaxKey should produce TypeMismatch",
        id="write_concern_type_maxkey",
    ),
]

# Property [writeConcern Not Supported]: a valid writeConcern
# document produces an InvalidOptions error because listDatabases is a
# read command that does not support write concern.
WRITE_CONCERN_NOT_SUPPORTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": {}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="Empty writeConcern document should produce InvalidOptions",
        id="write_concern_empty_doc",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": {"w": 1}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="writeConcern with w:1 should produce InvalidOptions",
        id="write_concern_w_1",
    ),
]

WRITE_CONCERN_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_TYPE_ERROR_TESTS + WRITE_CONCERN_NOT_SUPPORTED_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_TESTS))
def test_listDatabases_write_concern(collection, test):
    """Test listDatabases writeConcern behavior."""
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
