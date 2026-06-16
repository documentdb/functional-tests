"""Tests for listDatabases readConcern behavior."""

from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.listDatabases.utils.listDatabases_common import (  # noqa: E501
    basic_success,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Concern Accepted Values]: readConcern with level local,
# an empty document, or null is accepted; writeConcern with null is
# accepted. All other concern values are rejected.
CONCERN_ACCEPTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"level": "local"}},
        expected=basic_success,
        msg="readConcern with level local should be accepted",
        id="read_concern_local",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {}},
        expected=basic_success,
        msg="readConcern with empty document should be accepted",
        id="read_concern_empty",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": None},
        expected=basic_success,
        msg="readConcern with null should be accepted",
        id="read_concern_null",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "writeConcern": None},
        expected=basic_success,
        msg="writeConcern with null should be accepted",
        id="write_concern_null",
    ),
]

# Property [readConcern Type Strictness]: readConcern with a
# non-document type produces a TypeMismatch error.
READ_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with int32 should produce TypeMismatch",
        id="read_concern_type_int32",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with Int64 should produce TypeMismatch",
        id="read_concern_type_int64",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": 3.14},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with double should produce TypeMismatch",
        id="read_concern_type_double",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Decimal128("99")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with Decimal128 should produce TypeMismatch",
        id="read_concern_type_decimal128",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with bool should produce TypeMismatch",
        id="read_concern_type_bool",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": "bad"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with string should produce TypeMismatch",
        id="read_concern_type_string",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": [{}]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with array should produce TypeMismatch",
        id="read_concern_type_array",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with ObjectId should produce TypeMismatch",
        id="read_concern_type_objectid",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with datetime should produce TypeMismatch",
        id="read_concern_type_datetime",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with Timestamp should produce TypeMismatch",
        id="read_concern_type_timestamp",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with Binary should produce TypeMismatch",
        id="read_concern_type_binary",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with Regex should produce TypeMismatch",
        id="read_concern_type_regex",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Code("function(){}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with Code should produce TypeMismatch",
        id="read_concern_type_code",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": Code("function(){}", {"x": 1})},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with CodeWithScope should produce TypeMismatch",
        id="read_concern_type_code_with_scope",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with MinKey should produce TypeMismatch",
        id="read_concern_type_minkey",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern with MaxKey should produce TypeMismatch",
        id="read_concern_type_maxkey",
    ),
]

# Property [readConcern Unsupported Levels]: unsupported read concern
# levels (majority, available, linearizable, snapshot) produce an
# InvalidOptions error.
READ_CONCERN_UNSUPPORTED_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"level": "majority"}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level majority should produce InvalidOptions",
        id="read_concern_majority",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"level": "available"}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level available should produce InvalidOptions",
        id="read_concern_available",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"level": "linearizable"}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level linearizable should produce InvalidOptions",
        id="read_concern_linearizable",
    ),
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"level": "snapshot"}},
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level snapshot should produce InvalidOptions",
        id="read_concern_snapshot",
    ),
]

# Property [readConcern Invalid Value]: an invalid read concern level
# value produces a BadValue error.
READ_CONCERN_INVALID_VALUE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"level": "invalid_value"}},
        error_code=BAD_VALUE_ERROR,
        msg="readConcern with invalid level value should produce BadValue",
        id="read_concern_invalid_value",
    ),
]

# Property [readConcern Unknown Fields]: unknown fields inside the
# readConcern document produce an IDLUnknownField error.
READ_CONCERN_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listDatabases": 1, "readConcern": {"unknownField": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unknown field inside readConcern should produce IDLUnknownField",
        id="read_concern_unknown_field",
    ),
]

# Property [readConcern afterClusterTime Null]: afterClusterTime set
# to null with level local produces a TypeMismatch error.
READ_CONCERN_AFTER_CLUSTER_TIME_NULL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={
            "listDatabases": 1,
            "readConcern": {"level": "local", "afterClusterTime": None},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="afterClusterTime null with level local should produce TypeMismatch",
        id="read_concern_after_cluster_time_null",
    ),
]

READ_CONCERN_TESTS: list[CommandTestCase] = (
    CONCERN_ACCEPTED_TESTS
    + READ_CONCERN_TYPE_ERROR_TESTS
    + READ_CONCERN_UNSUPPORTED_LEVEL_TESTS
    + READ_CONCERN_INVALID_VALUE_TESTS
    + READ_CONCERN_UNKNOWN_FIELD_TESTS
    + READ_CONCERN_AFTER_CLUSTER_TIME_NULL_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(READ_CONCERN_TESTS))
def test_listDatabases_read_concern(collection, test):
    """Test listDatabases readConcern behavior."""
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
