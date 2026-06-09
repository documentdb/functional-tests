"""Tests for planCacheSetFilter type strictness and argument validation."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import BAD_VALUE_ERROR, INVALID_NAMESPACE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


# Property [Type Strictness: planCacheSetFilter]: the collection name field must be a string.
SET_FILTER_COLLECTION_NAME_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collection_name_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command={"planCacheSetFilter": value, "query": {"a": 1}, "indexes": [{"a": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg=f"planCacheSetFilter should reject {type_id} as collection name",
    )
    for type_id, value in [
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("document", {}),
        ("array", []),
        ("binary", Binary(b"\x00")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("null", None),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(0, 0)),
        ("code", Code("x")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Invalid Collection Name]: planCacheSetFilter rejects invalid collection names.
SET_FILTER_INVALID_COLLECTION_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_name_empty_string",
        docs=[{"_id": 1, "a": 1}],
        command={"planCacheSetFilter": "", "query": {"a": 1}, "indexes": [{"a": 1}]},
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheSetFilter should reject empty string as collection name",
    ),
    CommandTestCase(
        "collection_name_system_prefix",
        docs=[{"_id": 1, "a": 1}],
        command={"planCacheSetFilter": "system.views", "query": {"a": 1}, "indexes": [{"a": 1}]},
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject system-prefixed collection names",
    ),
]

# Property [Query Required]: planCacheSetFilter requires the query field.
SET_FILTER_QUERY_REQUIRED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "query_missing",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject missing query field",
    ),
]

# Property [Type Strictness: query]: the query field must be a document.
SET_FILTER_QUERY_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"query_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": v,
            "indexes": [{"a": 1}],
        },
        error_code=error,
        expected=exp,
        msg=f"planCacheSetFilter should reject {type_id} as query",
    )
    for type_id, value, error, exp in [
        ("string", "abc", BAD_VALUE_ERROR, None),
        ("int32", 42, BAD_VALUE_ERROR, None),
        ("int64", Int64(42), BAD_VALUE_ERROR, None),
        ("double", 3.14, BAD_VALUE_ERROR, None),
        ("decimal128", Decimal128("1"), BAD_VALUE_ERROR, None),
        ("bool_true", True, BAD_VALUE_ERROR, None),
        ("bool_false", False, BAD_VALUE_ERROR, None),
        ("array", [], None, {"ok": 1.0}),
        ("binary", Binary(b"\x00"), BAD_VALUE_ERROR, None),
        ("objectid", ObjectId(), BAD_VALUE_ERROR, None),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc), BAD_VALUE_ERROR, None),
        ("null", None, BAD_VALUE_ERROR, None),
        ("regex", Regex(".*"), BAD_VALUE_ERROR, None),
        ("timestamp", Timestamp(0, 0), BAD_VALUE_ERROR, None),
        ("code", Code("x"), BAD_VALUE_ERROR, None),
        ("minkey", MinKey(), BAD_VALUE_ERROR, None),
        ("maxkey", MaxKey(), BAD_VALUE_ERROR, None),
    ]
]

# Property [Indexes Required]: planCacheSetFilter requires the indexes field.
SET_FILTER_INDEXES_REQUIRED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "indexes_missing",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject missing indexes field",
    ),
]

# Property [Type Strictness: indexes]: the indexes field must be an array.
SET_FILTER_INDEXES_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"indexes_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": v,
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"planCacheSetFilter should reject {type_id} as indexes",
    )
    for type_id, value in [
        ("string", "abc"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("document", {}),
        ("binary", Binary(b"\x00")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("null", None),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(0, 0)),
        ("code", Code("x")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Empty Indexes Array]: planCacheSetFilter rejects an empty indexes array.
SET_FILTER_EMPTY_INDEXES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "indexes_empty_array",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject an empty indexes array",
    ),
]

# Property [Type Strictness: sort]: the sort field must be a document when provided.
SET_FILTER_SORT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"sort_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "sort": v,
            "indexes": [{"a": 1}],
        },
        error_code=error,
        expected=exp,
        msg=f"planCacheSetFilter should reject {type_id} as sort",
    )
    for type_id, value, error, exp in [
        ("string", "abc", BAD_VALUE_ERROR, None),
        ("int32", 42, BAD_VALUE_ERROR, None),
        ("int64", Int64(42), BAD_VALUE_ERROR, None),
        ("double", 3.14, BAD_VALUE_ERROR, None),
        ("decimal128", Decimal128("1"), BAD_VALUE_ERROR, None),
        ("bool_true", True, BAD_VALUE_ERROR, None),
        ("bool_false", False, BAD_VALUE_ERROR, None),
        ("array", [], None, {"ok": 1.0}),
        ("binary", Binary(b"\x00"), BAD_VALUE_ERROR, None),
        ("objectid", ObjectId(), BAD_VALUE_ERROR, None),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc), BAD_VALUE_ERROR, None),
        ("regex", Regex(".*"), BAD_VALUE_ERROR, None),
        ("timestamp", Timestamp(0, 0), BAD_VALUE_ERROR, None),
        ("code", Code("x"), BAD_VALUE_ERROR, None),
        ("minkey", MinKey(), BAD_VALUE_ERROR, None),
        ("maxkey", MaxKey(), BAD_VALUE_ERROR, None),
    ]
]

# Property [Null Sort/Projection/Collation]: null values are rejected.
# Property [Empty Sort Document]: planCacheSetFilter with empty sort document succeeds.
SET_FILTER_SORT_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_null",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "sort": None,
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject null sort value",
    ),
    CommandTestCase(
        "sort_empty_document",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "sort": {},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept empty sort document",
    ),
]

# Property [Type Strictness: projection]: the projection field must be a document when provided.
SET_FILTER_PROJECTION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"projection_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": v,
            "indexes": [{"a": 1}],
        },
        error_code=error,
        expected=exp,
        msg=f"planCacheSetFilter should reject {type_id} as projection",
    )
    for type_id, value, error, exp in [
        ("string", "abc", BAD_VALUE_ERROR, None),
        ("int32", 42, BAD_VALUE_ERROR, None),
        ("int64", Int64(42), BAD_VALUE_ERROR, None),
        ("double", 3.14, BAD_VALUE_ERROR, None),
        ("decimal128", Decimal128("1"), BAD_VALUE_ERROR, None),
        ("bool_true", True, BAD_VALUE_ERROR, None),
        ("bool_false", False, BAD_VALUE_ERROR, None),
        ("array", [], None, {"ok": 1.0}),
        ("binary", Binary(b"\x00"), BAD_VALUE_ERROR, None),
        ("objectid", ObjectId(), BAD_VALUE_ERROR, None),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc), BAD_VALUE_ERROR, None),
        ("regex", Regex(".*"), BAD_VALUE_ERROR, None),
        ("timestamp", Timestamp(0, 0), BAD_VALUE_ERROR, None),
        ("code", Code("x"), BAD_VALUE_ERROR, None),
        ("minkey", MinKey(), BAD_VALUE_ERROR, None),
        ("maxkey", MaxKey(), BAD_VALUE_ERROR, None),
    ]
]

# Property [Null Projection]: planCacheSetFilter rejects null projection.
# Property [Empty Projection Document]: planCacheSetFilter with empty projection document succeeds.
# Property [Inclusion/Exclusion Projection]: planCacheSetFilter accepts inclusion and exclusion projections.
SET_FILTER_PROJECTION_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "projection_null",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": None,
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject null projection value",
    ),
    CommandTestCase(
        "projection_empty_document",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": {},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept empty projection document",
    ),
    CommandTestCase(
        "projection_inclusion",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": {"b": 1},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept inclusion projection",
    ),
    CommandTestCase(
        "projection_exclusion",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "projection": {"b": 0},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept exclusion projection",
    ),
]

# Property [Type Strictness: collation]: the collation field must be a document when provided.
SET_FILTER_COLLATION_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collation_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "collation": v,
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg=f"planCacheSetFilter should reject {type_id} as collation",
    )
    for type_id, value in [
        ("string", "abc"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", []),
        ("binary", Binary(b"\x00")),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("regex", Regex(".*")),
        ("timestamp", Timestamp(0, 0)),
        ("code", Code("x")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [Null Collation]: planCacheSetFilter rejects null collation.
# Property [Collation Wiring]: planCacheSetFilter accepts a valid collation document.
SET_FILTER_COLLATION_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collation_null",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "collation": None,
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject null collation value",
    ),
    CommandTestCase(
        "collation_wiring",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "collation": {"locale": "en_US"},
            "indexes": [{"a": 1}],
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should accept a valid collation document",
    ),
]

# Property [Comment Accepts Any BSON Type]: the comment field accepts any BSON type.
SET_FILTER_COMMENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
            "comment": v,
        },
        expected={"ok": 1.0},
        msg=f"planCacheSetFilter should accept {type_id} as comment",
    )
    for type_id, value in [
        ("string", "a comment"),
        ("int32", 42),
        ("document", {"key": "value"}),
        ("array", [1, 2, 3]),
        ("bool_true", True),
        ("null", None),
    ]
]

# Property [Unrecognized Fields Accepted]: planCacheSetFilter silently accepts unrecognized fields.
SET_FILTER_UNRECOGNIZED_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "unrecognized_field",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
            "unknownField": 1,
        },
        expected={"ok": 1.0},
        msg="planCacheSetFilter should silently accept unrecognized fields",
    ),
]

SET_FILTER_TYPE_ERROR_TESTS: list[CommandTestCase] = (
    SET_FILTER_COLLECTION_NAME_TYPE_TESTS
    + SET_FILTER_INVALID_COLLECTION_NAME_TESTS
    + SET_FILTER_QUERY_REQUIRED_TESTS
    + SET_FILTER_QUERY_TYPE_TESTS
    + SET_FILTER_INDEXES_REQUIRED_TESTS
    + SET_FILTER_INDEXES_TYPE_TESTS
    + SET_FILTER_EMPTY_INDEXES_TESTS
    + SET_FILTER_SORT_TYPE_TESTS
    + SET_FILTER_SORT_EDGE_TESTS
    + SET_FILTER_PROJECTION_TYPE_TESTS
    + SET_FILTER_PROJECTION_EDGE_TESTS
    + SET_FILTER_COLLATION_TYPE_TESTS
    + SET_FILTER_COLLATION_EDGE_TESTS
    + SET_FILTER_COMMENT_TESTS
    + SET_FILTER_UNRECOGNIZED_FIELD_TESTS
)


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_TYPE_ERROR_TESTS))
def test_planCacheSetFilter_type_errors(database_client, collection, test):
    """Test planCacheSetFilter type strictness and argument validation."""
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
