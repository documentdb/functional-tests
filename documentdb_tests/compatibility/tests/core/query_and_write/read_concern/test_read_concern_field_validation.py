"""
readConcern field validation tests.

Tests type validation for the readConcern field and readConcern.level sub-field,
including invalid level strings, null coercion, and unknown extra fields.
"""

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.query_and_write.read_concern.utils import (
    is_cursor_command,
)
from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH, OID_EPOCH, TS_EPOCH


def _rc_find(ctx, rc):
    return {"find": ctx.collection, "filter": {}, "readConcern": rc}


def _rc_aggregate(ctx, rc):
    return {"aggregate": ctx.collection, "pipeline": [], "cursor": {}, "readConcern": rc}


def _rc_count(ctx, rc):
    return {"count": ctx.collection, "query": {}, "readConcern": rc}


def _rc_distinct(ctx, rc):
    return {"distinct": ctx.collection, "key": "x", "readConcern": rc}


# Property [Non-Document Rejection]: readConcern field rejects non-document types with TypeMismatch.
_NON_DOCUMENT_TYPES = [
    ("int", 1),
    ("double", 1.0),
    ("string", "local"),
    ("bool", True),
    ("array", [{"level": "local"}]),
    ("int64", Int64(1)),
    ("decimal128", Decimal128("1")),
    ("objectId", OID_EPOCH),
    ("date", DATE_EPOCH),
    ("regex", Regex(".*")),
    ("timestamp", TS_EPOCH),
    ("binary", Binary(b"\x01")),
    ("code", Code("function(){}")),
    ("minKey", MinKey()),
    ("maxKey", MaxKey()),
]

NON_DOCUMENT_READ_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_rejects_non_document_read_concern_{type_name}",
        command=lambda ctx, _rc=value, _cmd=cmd: {
            _cmd: ctx.collection,
            **(_build_extra_fields(_cmd)),
            "readConcern": _rc,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{cmd} should reject readConcern of type {type_name}.",
    )
    for cmd in ["find", "aggregate", "count", "distinct"]
    for type_name, value in _NON_DOCUMENT_TYPES
]


def _build_extra_fields(cmd: str) -> dict:
    """Return extra fields needed per command type."""
    if cmd == "find":
        return {"filter": {}}
    elif cmd == "aggregate":
        return {"pipeline": [], "cursor": {}}
    elif cmd == "count":
        return {"query": {}}
    elif cmd == "distinct":
        return {"key": "x"}
    return {}


@pytest.mark.parametrize("test", pytest_params(NON_DOCUMENT_READ_CONCERN_TESTS))
def test_read_concern_rejects_non_document(collection, test: CommandTestCase):
    """Test readConcern rejects non-document types."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Invalid Level Type Rejection]: readConcern.level rejects non-string types.
_INVALID_LEVEL_TYPES = [
    ("int", 1),
    ("double", 1.0),
    ("bool", True),
    ("array", ["local"]),
    ("document", {"value": "local"}),
    ("int64", Int64(1)),
    ("decimal128", Decimal128("1")),
    ("objectId", OID_EPOCH),
    ("date", DATE_EPOCH),
    ("regex", Regex(".*")),
    ("timestamp", TS_EPOCH),
    ("binary", Binary(b"\x01")),
    ("code", Code("function(){}")),
    ("minKey", MinKey()),
    ("maxKey", MaxKey()),
]

INVALID_LEVEL_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_rejects_non_string_level_{type_name}",
        command=lambda ctx, _rc={"level": value}, _cmd=cmd: {
            _cmd: ctx.collection,
            **(_build_extra_fields(_cmd)),
            "readConcern": _rc,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"{cmd} should reject readConcern level of type {type_name}.",
    )
    for cmd in ["find", "aggregate", "count", "distinct"]
    for type_name, value in _INVALID_LEVEL_TYPES
]


@pytest.mark.parametrize("test", pytest_params(INVALID_LEVEL_TYPE_TESTS))
def test_read_concern_rejects_non_string_level(collection, test: CommandTestCase):
    """Test readConcern.level rejects non-string types."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Invalid Level String Rejection]: unknown or improperly cased levels are rejected.
_INVALID_LEVEL_STRINGS = [
    ("empty_string", ""),
    ("invalid", "invalid"),
    ("uppercase_local", "LOCAL"),
    ("mixed_case_majority", "Majority"),
    ("nonexistent_strong", "strong"),
]

INVALID_LEVEL_STRING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"{cmd}_rejects_invalid_level_string_{str_name}",
        command=lambda ctx, _rc={"level": value}, _cmd=cmd: {
            _cmd: ctx.collection,
            **(_build_extra_fields(_cmd)),
            "readConcern": _rc,
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"{cmd} should reject invalid readConcern level string '{value}'.",
    )
    for cmd in ["find", "aggregate", "count", "distinct"]
    for str_name, value in _INVALID_LEVEL_STRINGS
]


@pytest.mark.parametrize("test", pytest_params(INVALID_LEVEL_STRING_TESTS))
def test_read_concern_rejects_invalid_level_string(collection, test: CommandTestCase):
    """Test readConcern.level rejects invalid string values."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(result, error_code=test.error_code, msg=test.msg)


# Property [Null readConcern Behavior]: readConcern field set to null is treated as omitted.
NULL_READ_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_null_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"find": ctx.collection, "filter": {}, "readConcern": None},
        expected=[{"_id": 1, "x": 1}],
        msg="find should treat null readConcern as omitted.",
    ),
    CommandTestCase(
        "aggregate_null_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": None,
        },
        expected=[{"_id": 1, "x": 1}],
        msg="aggregate should treat null readConcern as omitted.",
    ),
    CommandTestCase(
        "count_null_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"count": ctx.collection, "query": {}, "readConcern": None},
        expected={"n": 1, "ok": 1.0},
        msg="count should treat null readConcern as omitted.",
    ),
    CommandTestCase(
        "distinct_null_read_concern",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "readConcern": None},
        expected={"ok": 1.0, "values": [1]},
        msg="distinct should treat null readConcern as omitted.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_READ_CONCERN_TESTS))
def test_read_concern_null_behavior(collection, test: CommandTestCase):
    """Test readConcern set to null is treated as omitted."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# Property [Null Level As Default]: readConcern {level: null} uses the implicit default.
NULL_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_null_level_treated_as_default",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {"find": ctx.collection, "filter": {}, "readConcern": {"level": None}},
        expected=[{"_id": 1, "x": 1}],
        msg="find should treat readConcern {level: null} as implicit default.",
    ),
    CommandTestCase(
        "aggregate_null_level_treated_as_default",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": None},
        },
        expected=[{"_id": 1, "x": 1}],
        msg="aggregate should treat readConcern {level: null} as implicit default.",
    ),
    CommandTestCase(
        "count_null_level_treated_as_default",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "query": {},
            "readConcern": {"level": None},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count should treat readConcern {level: null} as implicit default.",
    ),
    CommandTestCase(
        "distinct_null_level_treated_as_default",
        docs=[{"_id": 1, "x": 1}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": None},
        },
        expected={"ok": 1.0, "values": [1]},
        msg="distinct should treat readConcern {level: null} as implicit default.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_LEVEL_TESTS))
def test_read_concern_null_level_treated_as_default(collection, test: CommandTestCase):
    """Test readConcern {level: null} is treated as implicit default."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        msg=test.msg,
        raw_res=not is_cursor_command(test),
    )


# Property [Null Byte In Level String]: readConcern level with embedded null byte is rejected.
def test_aggregate_rejects_null_byte_in_level(collection):
    """Test aggregate rejects readConcern level string containing null byte."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [],
            "cursor": {},
            "readConcern": {"level": "local\x00extra"},
        },
    )
    assertResult(
        result, error_code=BAD_VALUE_ERROR, msg="aggregate should reject null byte in level string."
    )


# Property [Unknown Fields]: readConcern document with unknown fields and no level is rejected.
_UNKNOWN_FIELD_PARAMS = [
    pytest.param("find", id="find_unknown_field_no_level"),
    pytest.param("aggregate", id="aggregate_unknown_field_no_level"),
    pytest.param("count", id="count_unknown_field_no_level"),
    pytest.param("distinct", id="distinct_unknown_field_no_level"),
]


@pytest.mark.parametrize("command_name", _UNKNOWN_FIELD_PARAMS)
def test_read_concern_unknown_field_no_level(collection, command_name):
    """Test readConcern with unknown field and no level field returns error."""
    cmd = {
        command_name: collection.name,
        **_build_extra_fields(command_name),
        "readConcern": {"unknownField": 1},
    }
    result = execute_command(collection, cmd)
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"{command_name} should reject readConcern with unknown field and no level.",
    )


# Property [Extra Fields With Valid Level]: extra unknown fields with valid level are rejected.
_EXTRA_FIELD_PARAMS = [
    pytest.param("find", id="find_extra_field_with_level"),
    pytest.param("aggregate", id="aggregate_extra_field_with_level"),
    pytest.param("count", id="count_extra_field_with_level"),
    pytest.param("distinct", id="distinct_extra_field_with_level"),
]


@pytest.mark.parametrize("command_name", _EXTRA_FIELD_PARAMS)
def test_read_concern_extra_field_with_valid_level(collection, command_name):
    """Test readConcern with valid level plus unknown extra field."""
    cmd = {
        command_name: collection.name,
        **_build_extra_fields(command_name),
        "readConcern": {"level": "local", "unknownField": 1},
    }
    result = execute_command(collection, cmd)
    assertFailureCode(
        result,
        UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg=f"{command_name} should reject readConcern with extra unknown field.",
    )
