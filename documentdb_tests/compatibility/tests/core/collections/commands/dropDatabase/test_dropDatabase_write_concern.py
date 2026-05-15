from __future__ import annotations

import datetime

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [writeConcern Document Acceptance]: only document type and
# null are accepted for writeConcern; an empty document succeeds.
WRITE_CONCERN_DOCUMENT_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {}},
        expected={"ok": 1.0},
        msg="Empty writeConcern document should be accepted",
        id="write_concern_empty_doc",
    ),
]

# Property [writeConcern Type Rejection]: all non-document BSON types
# (except null) produce a type mismatch error when used as writeConcern.
WRITE_CONCERN_TYPE_REJECTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": "majority"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="String writeConcern should produce type mismatch error",
        id="write_concern_string",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="int32 writeConcern should produce type mismatch error",
        id="write_concern_int32",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Int64 writeConcern should produce type mismatch error",
        id="write_concern_int64",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="double writeConcern should produce type mismatch error",
        id="write_concern_double",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Decimal128 writeConcern should produce type mismatch error",
        id="write_concern_decimal128",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="bool writeConcern should produce type mismatch error",
        id="write_concern_bool",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="array writeConcern should produce type mismatch error",
        id="write_concern_array",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="ObjectId writeConcern should produce type mismatch error",
        id="write_concern_objectid",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": datetime.datetime(2024, 1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="datetime writeConcern should produce type mismatch error",
        id="write_concern_datetime",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Timestamp writeConcern should produce type mismatch error",
        id="write_concern_timestamp",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": Binary(b"data")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Binary writeConcern should produce type mismatch error",
        id="write_concern_binary",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": Regex("pattern")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Regex writeConcern should produce type mismatch error",
        id="write_concern_regex",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": Code("function() {}")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="Code writeConcern should produce type mismatch error",
        id="write_concern_code",
    ),
    CommandTestCase(
        command={
            "dropDatabase": 1,
            "writeConcern": Code("function() {}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="CodeWithScope writeConcern should produce type mismatch error",
        id="write_concern_code_with_scope",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MinKey writeConcern should produce type mismatch error",
        id="write_concern_minkey",
    ),
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="MaxKey writeConcern should produce type mismatch error",
        id="write_concern_maxkey",
    ),
]

# Property [writeConcern Unrecognized Fields]: unrecognized fields
# within the writeConcern document produce an unknown field error.
WRITE_CONCERN_UNRECOGNIZED_FIELDS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"dropDatabase": 1, "writeConcern": {"unknownField": 1}},
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="Unrecognized field in writeConcern should produce unknown field error",
        id="write_concern_unknown_field",
    ),
]

WRITE_CONCERN_TESTS: list[CommandTestCase] = (
    WRITE_CONCERN_DOCUMENT_ACCEPTANCE_TESTS
    + WRITE_CONCERN_TYPE_REJECTION_TESTS
    + WRITE_CONCERN_UNRECOGNIZED_FIELDS_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(WRITE_CONCERN_TESTS))
def test_dropDatabase_write_concern(database_client, collection, register_db_cleanup, test):
    """Test dropDatabase command inputs and error handling."""
    coll = test.prepare(database_client, collection)
    result = execute_command(coll, test.command)
    assertResult(
        result,
        expected=test.expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
