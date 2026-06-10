"""Tests for planCacheSetFilter error cases."""

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
    COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
    INVALID_NAMESPACE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import ViewCollection

# Property [Non-Existent Collection]: planCacheSetFilter rejects a non-existent collection.
SET_FILTER_NON_EXISTENT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_existent_collection",
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        error_code=BAD_VALUE_ERROR,
        msg="planCacheSetFilter should reject a non-existent collection",
    ),
]

# Property [View Collection]: planCacheSetFilter rejects views.
SET_FILTER_VIEW_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "view_collection",
        target_collection=ViewCollection(),
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": ctx.collection,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        error_code=COMMAND_NOT_SUPPORTED_ON_VIEW_ERROR,
        msg="planCacheSetFilter should reject views",
    ),
]

# Property [Type Strictness: collection name]: the collection name field must be a string.
SET_FILTER_COLLECTION_NAME_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"collection_name_{type_id}",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx, v=value: {
            "planCacheSetFilter": v,
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
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

# Property [Invalid Collection Name]: planCacheSetFilter rejects invalid collection name strings.
SET_FILTER_INVALID_COLLECTION_NAME_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_name_empty_string",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": "",
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
        error_code=INVALID_NAMESPACE_ERROR,
        msg="planCacheSetFilter should reject empty string as collection name",
    ),
    CommandTestCase(
        "collection_name_system_prefix",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {
            "planCacheSetFilter": "system.views",
            "query": {"a": 1},
            "indexes": [{"a": 1}],
        },
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
        error_code=BAD_VALUE_ERROR,
        msg=f"planCacheSetFilter should reject {type_id} as query",
    )
    for type_id, value in [
        ("string", "abc"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
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
        error_code=BAD_VALUE_ERROR,
        msg=f"planCacheSetFilter should reject {type_id} as sort",
    )
    for type_id, value in [
        ("string", "abc"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
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
        error_code=BAD_VALUE_ERROR,
        msg=f"planCacheSetFilter should reject {type_id} as projection",
    )
    for type_id, value in [
        ("string", "abc"),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("null", None),
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
        ("null", None),
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

SET_FILTER_ERROR_TESTS: list[CommandTestCase] = (
    SET_FILTER_NON_EXISTENT_TESTS
    + SET_FILTER_VIEW_TESTS
    + SET_FILTER_COLLECTION_NAME_TYPE_TESTS
    + SET_FILTER_INVALID_COLLECTION_NAME_TESTS
    + SET_FILTER_QUERY_REQUIRED_TESTS
    + SET_FILTER_QUERY_TYPE_TESTS
    + SET_FILTER_INDEXES_REQUIRED_TESTS
    + SET_FILTER_INDEXES_TYPE_TESTS
    + SET_FILTER_EMPTY_INDEXES_TESTS
    + SET_FILTER_SORT_TYPE_TESTS
    + SET_FILTER_PROJECTION_TYPE_TESTS
    + SET_FILTER_COLLATION_TYPE_TESTS
)


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_FILTER_ERROR_TESTS))
def test_planCacheSetFilter_errors(database_client, collection, test):
    """Test planCacheSetFilter error cases."""
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
