"""Tests for listCollections readConcern behavior."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    INVALID_OPTIONS_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq, Len

# Property [readConcern Success Behavior]: readConcern with level
# "local" or as an empty document is accepted.
READ_CONCERN_SUCCESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        docs=[{"_id": 1}],
        id="read_concern_local",
        command={"listCollections": 1, "readConcern": {"level": "local"}},
        msg="readConcern with level 'local' should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
    CommandTestCase(
        docs=[{"_id": 1}],
        id="read_concern_empty",
        command={"listCollections": 1, "readConcern": {}},
        msg="readConcern={} should succeed",
        expected=lambda ctx: {
            "ok": Eq(1.0),
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0.name": Eq(ctx.collection),
        },
    ),
]

# Property [readConcern Level Unsupported]: non-local read concern
# levels produce INVALID_OPTIONS_ERROR.
READ_CONCERN_LEVEL_UNSUPPORTED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listCollections": 1, "readConcern": {"level": "available"}},
        msg="readConcern level 'available' should produce INVALID_OPTIONS_ERROR",
        id="available",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "readConcern": {"level": "majority"}},
        msg="readConcern level 'majority' should produce INVALID_OPTIONS_ERROR",
        id="majority",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "readConcern": {"level": "linearizable"}},
        msg="readConcern level 'linearizable' should produce INVALID_OPTIONS_ERROR",
        id="linearizable",
        error_code=INVALID_OPTIONS_ERROR,
    ),
    CommandTestCase(
        command={"listCollections": 1, "readConcern": {"level": "snapshot"}},
        msg="readConcern level 'snapshot' should produce INVALID_OPTIONS_ERROR",
        id="snapshot",
        error_code=INVALID_OPTIONS_ERROR,
    ),
]

# Property [readConcern Level Invalid Name]: an unrecognized read
# concern level name produces BAD_VALUE_ERROR.
READ_CONCERN_LEVEL_INVALID_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        command={"listCollections": 1, "readConcern": {"level": "invalid"}},
        msg="readConcern level 'invalid' should produce BAD_VALUE_ERROR",
        id="invalid_level",
        error_code=BAD_VALUE_ERROR,
    ),
]

# Property [readConcern Type Errors]: when readConcern is a
# non-document BSON type, the command produces a TYPE_MISMATCH_ERROR.
READ_CONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="read_concern_int32",
        command={"listCollections": 1, "readConcern": 42},
        msg="readConcern=int32 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_int64",
        command={"listCollections": 1, "readConcern": Int64(42)},
        msg="readConcern=Int64 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_double",
        command={"listCollections": 1, "readConcern": 3.14},
        msg="readConcern=double should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_decimal128",
        command={"listCollections": 1, "readConcern": Decimal128("99")},
        msg="readConcern=Decimal128 should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_bool",
        command={"listCollections": 1, "readConcern": True},
        msg="readConcern=bool should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_string",
        command={"listCollections": 1, "readConcern": "local"},
        msg="readConcern=string should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_array",
        command={"listCollections": 1, "readConcern": [{"level": "local"}]},
        msg="readConcern=array should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_objectid",
        command=lambda _: {"listCollections": 1, "readConcern": ObjectId()},
        msg="readConcern=ObjectId should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_datetime",
        command={"listCollections": 1, "readConcern": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        msg="readConcern=datetime should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_timestamp",
        command={"listCollections": 1, "readConcern": Timestamp(1, 1)},
        msg="readConcern=Timestamp should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_binary",
        command={"listCollections": 1, "readConcern": Binary(b"hello")},
        msg="readConcern=Binary should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_regex",
        command={"listCollections": 1, "readConcern": Regex(".*")},
        msg="readConcern=Regex should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_code",
        command={"listCollections": 1, "readConcern": Code("function(){}")},
        msg="readConcern=Code should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_code_with_scope",
        command={"listCollections": 1, "readConcern": Code("function(){}", {"x": 1})},
        msg="readConcern=CodeWithScope should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_minkey",
        command={"listCollections": 1, "readConcern": MinKey()},
        msg="readConcern=MinKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
    CommandTestCase(
        id="read_concern_maxkey",
        command={"listCollections": 1, "readConcern": MaxKey()},
        msg="readConcern=MaxKey should produce TYPE_MISMATCH_ERROR",
        error_code=TYPE_MISMATCH_ERROR,
    ),
]

READ_CONCERN_TESTS: list[CommandTestCase] = (
    READ_CONCERN_SUCCESS_TESTS
    + READ_CONCERN_LEVEL_UNSUPPORTED_TESTS
    + READ_CONCERN_LEVEL_INVALID_NAME_TESTS
    + READ_CONCERN_TYPE_ERROR_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(READ_CONCERN_TESTS))
def test_listCollections_read_concern(database_client, collection, test):
    """Test listCollections readConcern behavior."""
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
