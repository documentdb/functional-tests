"""Tests for distinct command readConcern sub-field validation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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

# Property [ReadConcern Level Validation]: the readConcern level sub-field
# validates type and value; null is treated as omitted; invalid strings produce
# BadValue; non-string types produce TypeMismatch.
DISTINCT_READCONCERN_LEVEL_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_level_null_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": None},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should accept null readConcern level (treated as omitted)",
    ),
    CommandTestCase(
        "readconcern_level_empty_string",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": ""},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject empty string for readConcern level",
    ),
    CommandTestCase(
        "readconcern_level_unknown",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "unknown"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject unknown readConcern level string",
    ),
    CommandTestCase(
        "readconcern_level_wrong_case",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "LOCAL"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject wrong-case readConcern level string",
    ),
    CommandTestCase(
        "readconcern_linearizable",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "linearizable"},
        },
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="distinct with linearizable readConcern should fail on non-replica-set",
    ),
    CommandTestCase(
        "readconcern_snapshot",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "snapshot"},
        },
        error_code=NOT_A_REPLICA_SET_ERROR,
        msg="distinct with snapshot readConcern should fail on non-replica-set",
    ),
    *[
        CommandTestCase(
            f"readconcern_level_type_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "readConcern": {"level": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} for readConcern level sub-field",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", ["local"]),
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

# Property [ReadConcern Unknown Fields]: unknown fields in the readConcern
# document produce an UnrecognizedCommandField error.
DISTINCT_READCONCERN_UNKNOWN_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_unknown_field",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"level": "local", "unknownField": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="distinct should reject unknown fields in readConcern document",
    ),
]

# Property [ReadConcern afterClusterTime]: afterClusterTime validates type
# and is rejected on standalone.
DISTINCT_READCONCERN_AFTER_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_after_cluster_time_timestamp",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"afterClusterTime": Timestamp(1, 1)},
        },
        error_code=ILLEGAL_OPERATION_ERROR,
        msg="distinct afterClusterTime should be rejected on standalone",
    ),
    *[
        CommandTestCase(
            f"readconcern_after_cluster_time_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "readConcern": {"afterClusterTime": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct afterClusterTime as {tid} should produce TypeMismatch",
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
DISTINCT_READCONCERN_AT_CLUSTER_TIME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "readconcern_at_cluster_time_timestamp",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"atClusterTime": Timestamp(1, 1)},
        },
        error_code=INVALID_OPTIONS_ERROR,
        msg="distinct atClusterTime without snapshot level should be rejected",
    ),
    *[
        CommandTestCase(
            f"readconcern_at_cluster_time_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "readConcern": {"atClusterTime": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct atClusterTime as {tid} should produce TypeMismatch",
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
DISTINCT_READCONCERN_PROVENANCE_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"readconcern_provenance_{prov}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, p=prov: {
                "distinct": ctx.collection,
                "key": "x",
                "readConcern": {"provenance": p},
            },
            expected={"values": ["a"], "ok": 1.0},
            msg=f"distinct readConcern provenance '{prov}' should succeed",
        )
        for prov in [
            "clientSupplied",
            "implicitDefault",
            "customDefault",
            "getLastErrorDefaults",
        ]
    ],
    CommandTestCase(
        "readconcern_provenance_null",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"provenance": None},
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct readConcern provenance null should succeed",
    ),
    CommandTestCase(
        "readconcern_provenance_invalid",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": {"provenance": "invalid"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct readConcern provenance invalid string should be rejected",
    ),
    *[
        CommandTestCase(
            f"readconcern_provenance_type_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "readConcern": {"provenance": v},
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct readConcern provenance as {tid} should produce TypeMismatch",
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

DISTINCT_READCONCERN_SUBFIELD_TESTS: list[CommandTestCase] = (
    DISTINCT_READCONCERN_LEVEL_TESTS
    + DISTINCT_READCONCERN_UNKNOWN_FIELDS_TESTS
    + DISTINCT_READCONCERN_AFTER_CLUSTER_TIME_TESTS
    + DISTINCT_READCONCERN_AT_CLUSTER_TIME_TESTS
    + DISTINCT_READCONCERN_PROVENANCE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_READCONCERN_SUBFIELD_TESTS))
def test_distinct_readconcern_subfields(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test distinct command readConcern sub-field validation."""
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
