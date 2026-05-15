"""Tests for validateDBMetadata index types triggering APIStrictError."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import API_STRICT_ERROR
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Index Types Triggering APIStrictError]: text and sparse
# indexes produce APIStrictError under strict validation, while other
# index types do not.
VALIDATE_DB_METADATA_INDEX_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "index_text",
        indexes=[IndexModel([("field", "text")], name="field_text")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_text is not allowed in API version 1.",
                }
            ],
        },
        msg="validateDBMetadata should report text index as APIStrictError",
    ),
    CommandTestCase(
        "index_sparse",
        indexes=[IndexModel([("field", 1)], sparse=True, name="field_sparse")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_sparse is not allowed in API version 1.",
                }
            ],
        },
        msg="validateDBMetadata should report sparse index as APIStrictError",
    ),
    CommandTestCase(
        "index_unique_sparse",
        indexes=[IndexModel([("field", 1)], unique=True, sparse=True, name="field_unique_sparse")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_unique_sparse"
                    " is not allowed in API version 1.",
                }
            ],
        },
        msg="validateDBMetadata should report unique+sparse index as APIStrictError",
    ),
    CommandTestCase(
        "index_compound_sparse",
        indexes=[
            IndexModel([("field", 1), ("other", 1)], sparse=True, name="field_compound_sparse")
        ],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_compound_sparse"
                    " is not allowed in API version 1.",
                }
            ],
        },
        msg="validateDBMetadata should report compound+sparse index as APIStrictError",
    ),
    CommandTestCase(
        "index_2dsphere_no_error",
        indexes=[IndexModel([("loc", "2dsphere")], name="loc_2dsphere")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report 2dsphere index",
    ),
    CommandTestCase(
        "index_2d_no_error",
        indexes=[IndexModel([("loc", "2d")], name="loc_2d")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report 2d index",
    ),
    CommandTestCase(
        "index_hashed_no_error",
        indexes=[IndexModel([("field", "hashed")], name="field_hashed")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report hashed index",
    ),
    CommandTestCase(
        "index_wildcard_no_error",
        indexes=[IndexModel([("$**", 1)], name="field_wildcard")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report wildcard index",
    ),
    CommandTestCase(
        "index_compound_no_error",
        indexes=[IndexModel([("field", 1), ("other", 1)], name="field_compound")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report compound index",
    ),
    CommandTestCase(
        "index_unique_no_error",
        indexes=[IndexModel([("field", 1)], unique=True, name="field_unique")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report unique index",
    ),
    CommandTestCase(
        "index_ttl_no_error",
        indexes=[IndexModel([("ts", 1)], expireAfterSeconds=3600, name="ts_ttl")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report TTL index",
    ),
    CommandTestCase(
        "index_partial_no_error",
        indexes=[
            IndexModel(
                [("field", 1)],
                partialFilterExpression={"field": {"$exists": True}},
                name="field_partial",
            )
        ],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report partial index",
    ),
    CommandTestCase(
        "index_regular_no_error",
        indexes=[IndexModel([("field", 1)], name="field_regular")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report regular index",
    ),
    CommandTestCase(
        "index_text_sparse_single_error",
        indexes=[IndexModel([("field", "text")], sparse=True, name="field_text_sparse")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_text_sparse"
                    " is not allowed in API version 1.",
                }
            ],
        },
        msg="validateDBMetadata should report text+sparse index as single error per index",
    ),
    CommandTestCase(
        "index_descending_no_error",
        indexes=[IndexModel([("field", -1)], name="field_desc")],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected={"ok": 1.0, "apiVersionErrors": []},
        msg="validateDBMetadata should not report descending index",
    ),
    CommandTestCase(
        "index_multiple_violating",
        indexes=[
            IndexModel([("field", "text")], name="field_text"),
            IndexModel([("other", 1)], sparse=True, name="other_sparse"),
        ],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name field_text is not allowed in API version 1.",
                },
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name other_sparse is not allowed in API version 1.",
                },
            ],
        },
        msg="validateDBMetadata should produce separate error entries per violating index",
    ),
    CommandTestCase(
        "index_multiple_violating_order",
        indexes=[
            IndexModel([("z_field", 1)], sparse=True, name="z_sparse"),
            IndexModel([("a_field", "text")], name="a_text"),
        ],
        docs=[],
        command=lambda ctx: {
            "validateDBMetadata": 1,
            "apiParameters": {"version": "1", "strict": True},
            "db": ctx.database,
            "collection": ctx.collection,
        },
        expected=lambda ctx: {
            "ok": 1.0,
            "apiVersionErrors": [
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name z_sparse is not allowed in API version 1.",
                },
                {
                    "ns": ctx.namespace,
                    "code": API_STRICT_ERROR,
                    "codeName": "APIStrictError",
                    "errmsg": "The index with name a_text is not allowed in API version 1.",
                },
            ],
        },
        msg="validateDBMetadata should order errors by index creation order",
    ),
]


@pytest.mark.collection_mgmt
@pytest.mark.parametrize("test", pytest_params(VALIDATE_DB_METADATA_INDEX_TYPE_TESTS))
def test_validateDBMetadata_index_types(database_client, collection, test):
    """Test validateDBMetadata index types triggering APIStrictError."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_admin_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
