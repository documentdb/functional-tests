"""Tests for setQuerySettings command BSON type rejection.

Validates that the setQuerySettings command rejects invalid BSON types for
the primary argument field, the queryFramework sub-field, the reject sub-field,
and the indexHints namespace and allowedIndexes sub-fields.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    FAILED_TO_PARSE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = [pytest.mark.requires(cluster_admin=True), pytest.mark.no_parallel]

# Property [Primary Argument Type Rejection]: the setQuerySettings field must
# be a document (query shape) or string (hash). All other BSON types are
# rejected with TYPE_MISMATCH_ERROR.
SET_QUERY_SETTINGS_PRIMARY_ARG_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"primary_arg_{tid}",
        command=lambda ctx, v=value: {
            "setQuerySettings": v,
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as the primary argument",
    )
    for tid, value in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1, 2, 3]),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 0)),
        ("binary", Binary(b"\x00")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [queryFramework Type Rejection]: the queryFramework field must be a
# string. Non-string BSON types are rejected with TYPE_MISMATCH_ERROR.
SET_QUERY_SETTINGS_QUERY_FRAMEWORK_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"query_framework_{tid}",
        command=lambda ctx, v=value: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "queryFramework": v,
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as queryFramework",
    )
    for tid, value in [
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("bool_true", True),
        ("bool_false", False),
        ("array", [1]),
        ("object", {"k": "v"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 0)),
        ("binary", Binary(b"\x00")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [reject Type Rejection]: the reject field must be a boolean.
# Non-boolean BSON types are rejected with TYPE_MISMATCH_ERROR.
SET_QUERY_SETTINGS_REJECT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"reject_{tid}",
        command=lambda ctx, v=value: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
                "reject": v,
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as reject field",
    )
    for tid, value in [
        ("null", None),
        ("int32", 42),
        ("int64", Int64(42)),
        ("double", 3.14),
        ("decimal128", Decimal128("1")),
        ("string", "true"),
        ("array", [True]),
        ("object", {"k": "v"}),
        ("objectid", ObjectId()),
        ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
        ("timestamp", Timestamp(0, 0)),
        ("binary", Binary(b"\x00")),
        ("regex", Regex(".*")),
        ("code", Code("function(){}")),
        ("minkey", MinKey()),
        ("maxkey", MaxKey()),
    ]
]

# Property [indexHints.ns.db Type Rejection]: the ns.db field must be a string.
SET_QUERY_SETTINGS_NS_DB_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"ns_db_{tid}",
        command=lambda ctx, v=value: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": v, "coll": ctx.collection},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as indexHints.ns.db",
    )
    for tid, value in [
        ("int32", 42),
        ("bool", True),
        ("array", ["test"]),
        ("object", {"k": "v"}),
    ]
]

# Property [indexHints.ns.coll Type Rejection]: the ns.coll field must be a string.
SET_QUERY_SETTINGS_NS_COLL_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"ns_coll_{tid}",
        command=lambda ctx, v=value: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": v},
                        "allowedIndexes": ["_id_"],
                    }
                ],
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as indexHints.ns.coll",
    )
    for tid, value in [
        ("int32", 42),
        ("bool", True),
    ]
]

# Property [indexHints.allowedIndexes Type Rejection]: allowedIndexes must be an array.
SET_QUERY_SETTINGS_ALLOWED_INDEXES_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"allowed_indexes_{tid}",
        command=lambda ctx, v=value: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": v,
                    }
                ],
            },
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg=f"setQuerySettings should reject {tid} as indexHints.allowedIndexes",
    )
    for tid, value in [
        ("string", "_id_"),
        ("int32", 42),
    ]
]

# Property [allowedIndexes null]: null allowedIndexes treated as missing required field.
SET_QUERY_SETTINGS_ALLOWED_INDEXES_EDGE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "allowed_indexes_null_missing",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": None,
                    }
                ],
            },
        },
        error_code=MISSING_FIELD_ERROR,
        msg="setQuerySettings should reject null allowedIndexes as missing field",
    ),
    CommandTestCase(
        "allowed_indexes_non_string_element",
        command=lambda ctx: {
            "setQuerySettings": {
                "find": ctx.collection,
                "filter": {"x": 1},
                "$db": ctx.database,
            },
            "settings": {
                "indexHints": [
                    {
                        "ns": {"db": ctx.database, "coll": ctx.collection},
                        "allowedIndexes": [42],
                    }
                ],
            },
        },
        error_code=FAILED_TO_PARSE_ERROR,
        msg="setQuerySettings should reject non-string elements in allowedIndexes",
    ),
]

SET_QUERY_SETTINGS_TYPE_ERROR_TESTS: list[CommandTestCase] = (
    SET_QUERY_SETTINGS_PRIMARY_ARG_TYPE_TESTS
    + SET_QUERY_SETTINGS_QUERY_FRAMEWORK_TYPE_TESTS
    + SET_QUERY_SETTINGS_REJECT_TYPE_TESTS
    + SET_QUERY_SETTINGS_NS_DB_TYPE_TESTS
    + SET_QUERY_SETTINGS_NS_COLL_TYPE_TESTS
    + SET_QUERY_SETTINGS_ALLOWED_INDEXES_TYPE_TESTS
    + SET_QUERY_SETTINGS_ALLOWED_INDEXES_EDGE_TESTS
)


@pytest.mark.admin
@pytest.mark.parametrize("test", pytest_params(SET_QUERY_SETTINGS_TYPE_ERROR_TESTS))
def test_setQuerySettings_type_errors(collection, test):
    """Test setQuerySettings BSON type rejection."""
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        error_code=test.error_code,
        msg=test.msg,
    )
