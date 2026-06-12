"""Tests for distinct command parameter type errors."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex
from bson.timestamp import Timestamp
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    FAILED_TO_PARSE_ERROR,
    INVALID_NAMESPACE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_INFINITY,
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_INFINITY,
    DECIMAL128_NEGATIVE_NAN,
    FLOAT_INFINITY,
    FLOAT_NAN,
    FLOAT_NEGATIVE_INFINITY,
    FLOAT_NEGATIVE_NAN,
)

# Property [Null Hint Error]: unlike other optional parameters, hint=null produces
# a parse error instead of being treated as omitted.
DISTINCT_NULL_HINT_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "null_hint_param_error",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": None},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="distinct should reject hint=null with a parse error",
    ),
]

# Property [Query Parameter Type Errors]: all non-object, non-null BSON types
# for query produce TypeMismatch error; invalid query operators produce
# BAD_VALUE_ERROR.
DISTINCT_QUERY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"query_type_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {"distinct": ctx.collection, "key": "x", "query": v},
            error_code=TYPE_MISMATCH_ERROR,
            msg=f"distinct should reject {tid} as query",
        )
        for tid, val in [
            ("string", "hello"),
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1, 2]),
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
    *[
        CommandTestCase(
            f"query_invalid_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "query": v,
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"distinct should reject {tid} in query",
        )
        for tid, val in [
            ("update_operator", {"$set": {"x": 1}}),
            ("aggregation_stage", {"$group": {"_id": None}}),
            ("unknown_operator", {"$foobar": 1}),
        ]
    ],
]

# Property [ReadConcern Parameter Type Errors]: all non-object, non-null BSON
# types for readConcern produce TypeMismatch error.
DISTINCT_READCONCERN_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"readconcern_type_{tid}",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx, v=val: {
            "distinct": ctx.collection,
            "key": "x",
            "readConcern": v,
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"distinct should reject {tid} as readConcern",
    )
    for tid, val in [
        ("string", "local"),
        ("int32", 42),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
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
]

# Property [Key Parameter Type Errors]: all non-string BSON types for key produce
# TypeMismatch error; null or omitted key produces a missing field error.
DISTINCT_KEY_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"key_type_{tid}",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx, v=val: {"distinct": ctx.collection, "key": v},
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"distinct should reject {tid} as key",
    )
    for tid, val in [
        ("int32", 123),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", ["x"]),
        ("object", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary", Binary(b"data", 0)),
        ("regex", Regex("abc", "")),
        ("code", Code("function(){}")),
        ("code_with_scope", Code("function(){}", {"s": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
] + [
    CommandTestCase(
        "key_type_null",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": None},
        error_code=MISSING_FIELD_ERROR,
        msg="distinct should reject null key as a missing required field",
    ),
    CommandTestCase(
        "key_type_omitted",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection},
        error_code=MISSING_FIELD_ERROR,
        msg="distinct should reject omitted key field as a missing required field",
    ),
]

# Property [Hint Parameter Type Errors]: invalid BSON types and values for the
# hint parameter produce appropriate errors.
DISTINCT_HINT_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    *[
        CommandTestCase(
            f"hint_type_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "hint": v,
            },
            error_code=FAILED_TO_PARSE_ERROR,
            msg=f"distinct should reject {tid} as hint",
        )
        for tid, val in [
            ("int32", 42),
            ("int64", Int64(1)),
            ("double", 3.14),
            ("decimal128", Decimal128("1")),
            ("bool", True),
            ("array", [1, 2]),
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
    CommandTestCase(
        "hint_nonexistent_index_name",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": "nonexistent_index",
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject a non-existent index name on an existing collection",
    ),
    CommandTestCase(
        "hint_empty_string_existing_collection",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {"distinct": ctx.collection, "key": "x", "hint": ""},
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject empty string as hint on an existing collection",
    ),
    CommandTestCase(
        "hint_doc_wrong_field_order",
        indexes=[IndexModel([("x", 1), ("y", 1)])],
        docs=[{"_id": 1, "x": "a", "y": "b"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"y": 1, "x": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject document hint with incorrect field order",
    ),
    CommandTestCase(
        "hint_string_case_sensitive",
        indexes=[IndexModel([("x", 1)], name="x_1")],
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": "X_1",
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct string hint should be case-sensitive",
    ),
    CommandTestCase(
        "hint_string_no_trimming",
        indexes=[IndexModel([("x", 1)], name="x_1")],
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": " x_1 ",
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct string hint should not trim whitespace",
    ),
    CommandTestCase(
        "hint_nonexistent_index_empty_collection",
        docs=[],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": "nonexistent_idx",
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject a non-existent index name on an empty collection",
    ),
    *[
        CommandTestCase(
            f"hint_direction_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "hint": {"x": v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"distinct should reject {tid} as direction value in document hint",
        )
        for tid, val in [
            ("zero", 0),
            ("two", 2),
            ("fractional", 0.5),
            ("nan", FLOAT_NAN),
            ("neg_nan", FLOAT_NEGATIVE_NAN),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
            ("infinity", FLOAT_INFINITY),
            ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
            ("bool", True),
            ("null", None),
            ("string", "asc"),
            ("string_text", "text"),
            ("string_hashed", "hashed"),
            ("string_2dsphere", "2dsphere"),
            ("string_2d", "2d"),
        ]
    ],
    *[
        CommandTestCase(
            f"hint_natural_direction_{tid}",
            docs=[{"_id": 1, "x": "a"}],
            command=lambda ctx, v=val: {
                "distinct": ctx.collection,
                "key": "x",
                "hint": {"$natural": v},
            },
            error_code=BAD_VALUE_ERROR,
            msg=f"distinct should reject $natural {tid} direction value",
        )
        for tid, val in [
            ("zero", 0),
            ("two", 2),
            ("neg_two", -2),
            ("fractional", 0.5),
            ("nan", FLOAT_NAN),
            ("neg_nan", FLOAT_NEGATIVE_NAN),
            ("decimal128_nan", DECIMAL128_NAN),
            ("decimal128_neg_nan", DECIMAL128_NEGATIVE_NAN),
            ("infinity", FLOAT_INFINITY),
            ("neg_infinity", FLOAT_NEGATIVE_INFINITY),
            ("decimal128_infinity", DECIMAL128_INFINITY),
            ("decimal128_neg_infinity", DECIMAL128_NEGATIVE_INFINITY),
            ("bool", True),
            ("string", "forward"),
            ("null", None),
            ("array", [1]),
            ("object", {"a": 1}),
        ]
    ],
    CommandTestCase(
        "hint_natural_combined_with_other_fields",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "distinct": ctx.collection,
            "key": "x",
            "hint": {"$natural": 1, "x": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="distinct should reject $natural combined with other fields in hint",
    ),
]

# Property [Collection Name Type Errors]: non-string types (except Binary subtype
# 4) and null as collection name produce InvalidNamespace error.
DISTINCT_COLLNAME_TYPE_ERROR_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collname_type_{tid}",
        docs=None,
        command=lambda ctx, v=val: {"distinct": v, "key": "x"},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"distinct should reject {tid} as collection name",
    )
    for tid, val in [
        ("null", None),
        ("int32", 123),
        ("int64", Int64(1)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool", True),
        ("array", [1, 2]),
        ("object", {"a": 1}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(1, 1)),
        ("binary_subtype0", Binary(b"hello", 0)),
        ("binary_subtype5", Binary(b"hello", 5)),
        ("regex", Regex("abc", "")),
        ("code", Code("function(){}")),
        ("code_scope", Code("function(){}", {"s": 1})),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

DISTINCT_TYPE_ERROR_TESTS: list[CommandTestCase] = (
    DISTINCT_NULL_HINT_ERROR_TESTS
    + DISTINCT_QUERY_TYPE_ERROR_TESTS
    + DISTINCT_READCONCERN_TYPE_ERROR_TESTS
    + DISTINCT_KEY_TYPE_ERROR_TESTS
    + DISTINCT_HINT_TYPE_ERROR_TESTS
    + DISTINCT_COLLNAME_TYPE_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(DISTINCT_TYPE_ERROR_TESTS))
def test_distinct_type_errors(database_client: Any, collection: Any, test: CommandTestCase) -> None:
    """Test distinct type error cases."""
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
