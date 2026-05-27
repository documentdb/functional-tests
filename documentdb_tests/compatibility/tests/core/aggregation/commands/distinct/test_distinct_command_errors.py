"""Tests for distinct command validation and structural errors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex
from bson.timestamp import Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    DISTINCT_TOO_BIG_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_OPTIONS_ERROR,
    KEY_FIELD_NULL_BYTE_ERROR,
    TYPE_MISMATCH_ERROR,
    UNRECOGNIZED_COMMAND_FIELD_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    DECIMAL128_ONE_AND_HALF,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
    INT32_MAX,
)

# Property [Query Validation]: query semantics are validated even when the
# collection does not exist; invalid operators produce BAD_VALUE_ERROR.
DISTINCT_QUERY_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_invalid_operator_nonexistent_collection",
        docs=None,
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "query": {"$invalid": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject invalid query operators even on non-existent collections",
    ),
]

# Property [Key Field Null Byte Rejection]: a null byte anywhere in the key
# string produces an error.
DISTINCT_KEY_NULL_BYTE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"key_null_byte_{tid}",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx, v=val: {"distinct": ctx.collection, "key": v},
        error_code=KEY_FIELD_NULL_BYTE_ERROR,
        msg=f"distinct should reject a key with a null byte {tid}",
    )
    for tid, val in [
        ("middle", "x\x00y"),
        ("start", "\x00x"),
        ("end", "x\x00"),
        ("only", "\x00"),
    ]
]

# Property [Unrecognized Fields]: unrecognized fields in the command document
# produce an IDLUnknownField error; field name matching is case-sensitive.
DISTINCT_UNRECOGNIZED_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_unknown_field",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "unknownField": 1,
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="distinct should reject unrecognized fields in the command document",
    ),
    CommandTestCase(
        "unrecognized_case_variant_key",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "Key": "y",
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="distinct should treat case variants of known fields as unrecognized",
    ),
    CommandTestCase(
        "unrecognized_case_variant_query",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "Query": {},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="distinct should treat 'Query' as unrecognized (case-sensitive matching)",
    ),
    CommandTestCase(
        "unrecognized_case_variant_hint",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "Hint": {"x": 1},
        },
        error_code=UNRECOGNIZED_COMMAND_FIELD_ERROR,
        msg="distinct should treat 'Hint' as unrecognized (case-sensitive matching)",
    ),
]

# Property [WriteConcern Rejection]: writeConcern is not accepted by the distinct
# command.
DISTINCT_WRITE_CONCERN_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"writeconcern_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "writeConcern": v,
            },
            error_code=INVALID_OPTIONS_ERROR,
            msg=f"distinct should reject writeConcern {tid} as unsupported",
        )
        for tid, val in [
            ("w_1", {"w": 1}),
            ("w_majority", {"w": "majority"}),
            ("w_0", {"w": 0}),
            ("j_true", {"j": True}),
            ("wtimeout", {"wtimeout": 1000}),
            ("empty_doc", {}),
        ]
    ],
    CommandTestCase(
        "writeconcern_null_accepted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "writeConcern": None,
        },
        expected={"values": ["a"], "ok": 1.0},
        msg="distinct should treat writeConcern null as omitted",
    ),
    *[
        CommandTestCase(
            f"writeconcern_type_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "writeConcern": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} as writeConcern",
        )
        for tid, val in [
            ("string", "majority"),
            ("int32", 1),
            ("int64", Int64(1)),
            ("double", 1.0),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1]),
            ("objectid", ObjectId("000000000000000000000001")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"data", 0)),
            ("regex", Regex("abc", "")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"s": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [maxTimeMS Validation Errors]: invalid maxTimeMS values produce
# appropriate errors based on the type of invalidity.
DISTINCT_MAXTIMEMS_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "maxtimems_err_negative",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "maxTimeMS": -1},
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject negative maxTimeMS",
    ),
    CommandTestCase(
        "maxtimems_err_exceeds_int32_max",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "maxTimeMS": INT32_MAX + 1,
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject maxTimeMS exceeding the maximum int32 value",
    ),
    CommandTestCase(
        "maxtimems_err_int64_exceeds_int32_max",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "maxTimeMS": Int64(INT32_MAX + 1),
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject Int64 maxTimeMS exceeding the maximum int32 value",
    ),
    *[
        CommandTestCase(
            f"maxtimems_err_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "maxTimeMS": v,
            },
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"distinct should reject {tid} as maxTimeMS",
        )
        for tid, val in [
            ("fractional", 1.5),
            ("decimal128_fractional", DECIMAL128_ONE_AND_HALF),
            ("nan", FLOAT_NAN),
            ("neg_nan", FLOAT_NEGATIVE_NAN),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
            ("infinity", FLOAT_INFINITY),
            ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
        ]
    ],
    *[
        CommandTestCase(
            f"maxtimems_err_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "maxTimeMS": v,
            },
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} as maxTimeMS",
        )
        for tid, val in [
            ("string", "hello"),
            ("bool", True),
            ("array", [1]),
            ("object", {"a": 1}),
            ("objectid", ObjectId("000000000000000000000001")),
            ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
            ("timestamp", Timestamp(1, 1)),
            ("binary", Binary(b"data", 0)),
            ("regex", Regex("abc", "")),
            ("code", Code("function(){}")),
            ("code_with_scope", Code("function(){}", {"s": 1})),
            ("minkey", MinKey()),
            ("maxkey", MaxKey()),
        ]
    ],
]

# Property [BSON Size Limit]: when the distinct values exceed the maximum BSON
# document size (16MB), the command produces an error.
DISTINCT_BSON_SIZE_LIMIT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "bson_size_limit_exceeded",
        docs=[{"_id": i, "x": f"v{i}" + "x" * 17_000} for i in range(1100)],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x"},
        error_code=DISTINCT_TOO_BIG_ERROR,
        msg="distinct should produce an error when results exceed the 16MB BSON size limit",
    ),
]

DISTINCT_COMMAND_ERROR_TESTS: list[CommandTestCase] = (
    DISTINCT_QUERY_ERROR_TESTS
    + DISTINCT_KEY_NULL_BYTE_TESTS
    + DISTINCT_UNRECOGNIZED_FIELDS_TESTS
    + DISTINCT_WRITE_CONCERN_TESTS
    + DISTINCT_MAXTIMEMS_ERROR_TESTS
    + DISTINCT_BSON_SIZE_LIMIT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_COMMAND_ERROR_TESTS))
def test_distinct_command_errors(
    database_client: Any, collection: Any, test: CommandTestCase
) -> None:
    """Test distinct command error cases."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
        ignore_order_in=test.ignore_order_in,
    )
