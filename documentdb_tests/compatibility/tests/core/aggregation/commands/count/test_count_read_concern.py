"""Tests for count command readConcern behavior and type strictness."""

from __future__ import annotations

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
    ILLEGAL_OPERATION_ERROR,
    INVALID_OPTIONS_ERROR,
    NOT_A_REPLICA_SET_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [ReadConcern Behavior]: the count command accepts valid readConcern
# levels.
COUNT_READ_CONCERN_BEHAVIOR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_local",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "local"},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with readConcern level 'local' should succeed",
    ),
    CommandTestCase(
        "readconcern_available",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "available"},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with readConcern level 'available' should succeed",
    ),
    CommandTestCase(
        "readconcern_majority",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "majority"},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with readConcern level 'majority' should succeed",
    ),
    CommandTestCase(
        "readconcern_empty_doc",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with empty readConcern document should succeed with default behavior",
    ),
    CommandTestCase(
        "readconcern_level_null",
        docs=[{"_id": i} for i in range(5)],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": None},
        },
        expected={"n": 5, "ok": 1.0},
        msg="count with readConcern level null should succeed with default behavior",
    ),
]

# Property [Type Strictness: readConcern]: the readConcern field validates
# type, sub-field types, and level values.
COUNT_TYPE_STRICTNESS_READ_CONCERN_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "type_readconcern_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": "local"},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject string for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": 42},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject int32 for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": Int64(1)},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Int64 for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": 3.14},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject double for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": Decimal128("1"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Decimal128 for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": True},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject bool for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": [1, 2]},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject array for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": ObjectId()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject ObjectId for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": datetime(2024, 1, 1, tzinfo=timezone.utc),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject datetime for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": Timestamp(1, 1),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Timestamp for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": Binary(b"\x01\x02"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Binary for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": Regex("^abc"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Regex for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": Code("function(){}"),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Code for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": Code("function(){}", {"x": 1}),
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Code with scope for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": MinKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject MinKey for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {"count": ctx.collection, "readConcern": MaxKey()},
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject MaxKey for readConcern",
    ),
    CommandTestCase(
        "type_readconcern_level_int32",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": 42},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject int32 for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_bool",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": True},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject bool for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_array",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": ["local"]},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject array for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_object",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": {"a": 1}},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject object for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_int64",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Int64(1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Int64 for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_double",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": 3.14},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject double for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_decimal128",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Decimal128("1")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Decimal128 for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_objectid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": ObjectId()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject ObjectId for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_datetime",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject datetime for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Timestamp(1, 1)},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Timestamp for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_binary",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Binary(b"\x01\x02")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Binary for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_regex",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Regex("^abc")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Regex for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_code",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Code("function(){}")},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Code for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_code_with_scope",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": Code("function(){}", {"x": 1})},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject Code with scope for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_minkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": MinKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject MinKey for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_maxkey",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": MaxKey()},
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="count should reject MaxKey for readConcern level sub-field",
    ),
    CommandTestCase(
        "type_readconcern_level_empty_string",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject empty string for readConcern level",
    ),
    CommandTestCase(
        "type_readconcern_level_unknown",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "unknown"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject unknown readConcern level string",
    ),
    CommandTestCase(
        "type_readconcern_level_wrong_case",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "LOCAL"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count should reject wrong-case readConcern level string",
    ),
    CommandTestCase(
        "type_readconcern_linearizable",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "linearizable"},
        },
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="count with linearizable readConcern should fail on non-replica-set",
    ),
    CommandTestCase(
        "type_readconcern_snapshot",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "snapshot"},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="count should reject snapshot readConcern level",
    ),
    CommandTestCase(
        "type_readconcern_unknown_field",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"level": "local", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="count should reject unknown fields in readConcern document",
    ),
]

# Property [ReadConcern afterClusterTime]: afterClusterTime validates type
# and is rejected on standalone.
COUNT_READ_CONCERN_AFTER_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_after_cluster_time_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="count afterClusterTime should be rejected on standalone",
    ),
    *[
        CommandTestCase(
            f"rc_after_cluster_time_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "count": ctx.collection,
                "readConcern": {"afterClusterTime": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count afterClusterTime as {tid} should produce TypeMismatch",
        )
        for tid, val in [
            ("null", None),
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("string", "hello"),
            ("bool", True),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [ReadConcern atClusterTime]: atClusterTime validates type and
# requires snapshot read concern level.
COUNT_READ_CONCERN_AT_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "rc_at_cluster_time_timestamp",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"atClusterTime": Timestamp(1, 1)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="count atClusterTime without snapshot level should be rejected",
    ),
    *[
        CommandTestCase(
            f"rc_at_cluster_time_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "count": ctx.collection,
                "readConcern": {"atClusterTime": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count atClusterTime as {tid} should produce TypeMismatch",
        )
        for tid, val in [
            ("null", None),
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("string", "hello"),
            ("bool", True),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [ReadConcern provenance]: the provenance sub-field validates type
# and enum value.
COUNT_READ_CONCERN_PROVENANCE_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"rc_provenance_{prov}",
            docs=[{"_id": 1}],
            command=lambda ctx, p=prov: {
                "count": ctx.collection,
                "readConcern": {"provenance": p},
            },
            expected={"n": 1, "ok": 1.0},
            msg=f"count readConcern provenance '{prov}' should succeed",
        )
        for prov in [
            "clientSupplied",
            "implicitDefault",
            "customDefault",
            "getLastErrorDefaults",
        ]
    ],
    CommandTestCase(
        "rc_provenance_null",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"provenance": None},
        },
        expected={"n": 1, "ok": 1.0},
        msg="count readConcern provenance null should succeed",
    ),
    CommandTestCase(
        "rc_provenance_invalid",
        docs=[{"_id": 1}],
        command=lambda ctx: {
            "count": ctx.collection,
            "readConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="count readConcern provenance invalid string should be rejected",
    ),
    *[
        CommandTestCase(
            f"rc_provenance_type_{tid}",
            docs=[{"_id": 1}],
            command=lambda ctx, v=val: {
                "count": ctx.collection,
                "readConcern": {"provenance": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"count readConcern provenance as {tid} should produce TypeMismatch",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1, 2]),
            ("object", {"a": 1}),
            ("objectid", ObjectId()),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"\x01\x02")),
            ("regex", Regex("^abc")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"x": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

COUNT_READ_CONCERN_ALL_TESTS: list[CommandTestCase] = (
    COUNT_READ_CONCERN_BEHAVIOR_TESTS
    + COUNT_TYPE_STRICTNESS_READ_CONCERN_TESTS
    + COUNT_READ_CONCERN_AFTER_CLUSTER_TIME_TESTS
    + COUNT_READ_CONCERN_AT_CLUSTER_TIME_TESTS
    + COUNT_READ_CONCERN_PROVENANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COUNT_READ_CONCERN_ALL_TESTS))
def test_count_read_concern(database_client, collection, test):
    """Test count command readConcern behavior."""
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
