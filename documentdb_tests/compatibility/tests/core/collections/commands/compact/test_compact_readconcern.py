"""Tests for compact command readConcern behavior."""

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

# Property [readConcern Acceptance]: readConcern is accepted when
# specifying a supported level or when empty.
COMPACT_READCONCERN_ACCEPTANCE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_local",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {"level": "local"},
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="readConcern level 'local' should be accepted",
    ),
    CommandTestCase(
        "readconcern_empty_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {},
        },
        expected={"bytesFreed": 0, "ok": 1.0},
        msg="readConcern as empty object should be accepted",
    ),
]

# Property [readConcern Unsupported Levels]: unsupported read concern
# levels produce an invalid options error.
COMPACT_READCONCERN_UNSUPPORTED_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_available",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {"level": "available"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level 'available' should be rejected",
    ),
    CommandTestCase(
        "readconcern_majority",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {"level": "majority"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level 'majority' should be rejected",
    ),
    CommandTestCase(
        "readconcern_linearizable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {"level": "linearizable"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level 'linearizable' should be rejected",
    ),
    CommandTestCase(
        "readconcern_snapshot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="readConcern level 'snapshot' should be rejected",
    ),
]

# Property [readConcern Invalid Level]: invalid level strings that are not
# a recognized read concern level produce a bad value error.
COMPACT_READCONCERN_INVALID_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_invalid_level",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": {"level": "bogus"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="readConcern with unrecognized level string should be rejected",
    ),
]

# Property [readConcern Type Strictness]: non-object types for readConcern
# produce a type mismatch error.
COMPACT_READCONCERN_TYPE_STRICTNESS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_type_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": "local"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as string should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": 1},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as int32 should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Int64 should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": 1.0},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as double should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": Decimal128("1")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Decimal128 should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as bool should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": [{"level": "local"}],
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as array should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as ObjectId should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as datetime should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": Timestamp(1, 1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Timestamp should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": Binary(b"\x01")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Binary should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": Regex(".*")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Regex should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": Code("x")},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Code should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "compact": ctx.collection,
            "readConcern": Code("x", {"a": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as Code with scope should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as MinKey should be rejected as wrong type",
    ),
    CommandTestCase(
        "readconcern_type_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"compact": ctx.collection, "readConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="readConcern as MaxKey should be rejected as wrong type",
    ),
]

COMPACT_READCONCERN_TESTS: list[CommandTestCase] = (
    COMPACT_READCONCERN_ACCEPTANCE_TESTS
    + COMPACT_READCONCERN_UNSUPPORTED_LEVEL_TESTS
    + COMPACT_READCONCERN_INVALID_LEVEL_TESTS
    + COMPACT_READCONCERN_TYPE_STRICTNESS_TESTS
)


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(COMPACT_READCONCERN_TESTS))
def test_compact_readconcern(database_client, collection, test):
    """Test compact command readConcern behavior."""
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
