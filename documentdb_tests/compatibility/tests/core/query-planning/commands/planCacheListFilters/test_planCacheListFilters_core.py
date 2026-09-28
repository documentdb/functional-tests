"""Tests for planCacheListFilters command core behavior and field acceptance."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import (
    CappedCollection,
    ClusteredCollection,
    NamedCollection,
)

# Property [Basic Success]: planCacheListFilters returns ok: 1.0 and empty
# filters array on existing, empty, and non-existent collections.
LIST_FILTERS_BASIC_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "basic_with_documents",
        docs=[{"_id": 1, "a": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on collection with documents",
    ),
    CommandTestCase(
        "basic_empty_collection",
        docs=[],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on empty collection",
    ),
    CommandTestCase(
        "basic_nonexistent_collection",
        docs=None,
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on non-existent collection",
    ),
]

# Property [Capped Collection]: planCacheListFilters succeeds on capped
# collections.
LIST_FILTERS_CAPPED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "capped_collection",
        target_collection=CappedCollection(size=4096),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on a capped collection",
    ),
]

# Property [Clustered Collection]: planCacheListFilters succeeds on clustered
# collections.
LIST_FILTERS_CLUSTERED_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "clustered_collection",
        target_collection=ClusteredCollection(),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed on a clustered collection",
    ),
]

# Property [Unknown Fields Accepted]: planCacheListFilters silently accepts
# unrecognized fields without error.
LIST_FILTERS_UNKNOWN_FIELD_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "accepts_unknown_field",
        command=lambda ctx: {"planCacheListFilters": ctx.collection, "foo": "bar"},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should silently accept unknown field",
    ),
    CommandTestCase(
        "accepts_case_variant_Comment",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "Comment": "test",
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat capitalized Comment as unknown field",
    ),
    CommandTestCase(
        "accepts_case_variant_Query",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "Query": {"a": 1},
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat capitalized Query as unknown field",
    ),
    CommandTestCase(
        "accepts_case_variant_Sort",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "Sort": {"a": 1},
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should treat capitalized Sort as unknown field",
    ),
]

# Property [Collection Name Edge Cases]: planCacheListFilters succeeds with
# special characters, unicode, and long collection names.
LIST_FILTERS_NAME_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "name_accepts_long_suffix",
        target_collection=NamedCollection(suffix="_" + "a" * 150),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with a long collection name",
    ),
    CommandTestCase(
        "name_accepts_hyphen",
        target_collection=NamedCollection(suffix="_my-coll"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with hyphen in name",
    ),
    CommandTestCase(
        "name_accepts_unicode",
        target_collection=NamedCollection(suffix="_\u00e9"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with unicode name",
    ),
    CommandTestCase(
        "name_accepts_single_char",
        target_collection=NamedCollection(suffix="_x"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with single-character suffix name",
    ),
    CommandTestCase(
        "name_accepts_underscores",
        target_collection=NamedCollection(suffix="_my_test_coll"),
        docs=[{"_id": 1}],
        command=lambda ctx: {"planCacheListFilters": ctx.collection},
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with underscores in name",
    ),
]

# Property [Comment Edge Cases]: planCacheListFilters succeeds with edge-case
# comment values.
LIST_FILTERS_COMMENT_EDGE_CASE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "comment_accepts_long_string",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": "x" * 10_000,
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with very long comment",
    ),
    CommandTestCase(
        "comment_accepts_empty_string",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": "",
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with empty string comment",
    ),
    CommandTestCase(
        "comment_accepts_nested_object",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": {"a": {"b": {"c": {"d": {"e": 1}}}}},
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with deeply nested object comment",
    ),
    CommandTestCase(
        "comment_accepts_mixed_array",
        command=lambda ctx: {
            "planCacheListFilters": ctx.collection,
            "comment": [1, "two", True, None, {"a": 1}],
        },
        expected={"filters": [], "ok": 1.0},
        msg="planCacheListFilters should succeed with array of mixed types as comment",
    ),
]

_BSON_TYPE_VALUES = [
    ("document", {"a": 1}),
    ("empty_document", {}),
    ("string", "test"),
    ("int32", 123),
    ("int64", Int64(1)),
    ("double", 1.5),
    ("decimal128", Decimal128("1")),
    ("bool_true", True),
    ("bool_false", False),
    ("null", None),
    ("array", [1, 2]),
    ("empty_array", []),
    ("binary", Binary(b"\x00")),
    ("objectid", ObjectId()),
    ("datetime", datetime(2024, 1, 1, tzinfo=timezone.utc)),
    ("regex", Regex(".*")),
    ("timestamp", Timestamp(0, 0)),
    ("code", Code("function(){}")),
    ("minkey", MinKey()),
    ("maxkey", MaxKey()),
]

# Property [Comment Type Acceptance]: the comment field accepts any valid
# BSON type.
LIST_FILTERS_COMMENT_TYPE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        f"comment_{tid}",
        command=lambda ctx, v=val: {
            "planCacheListFilters": ctx.collection,
            "comment": v,
        },
        expected={"filters": [], "ok": 1.0},
        msg=f"planCacheListFilters should accept comment of type {tid}",
    )
    for tid, val in _BSON_TYPE_VALUES
]

LIST_FILTERS_CORE_TESTS: list[CommandTestCase] = (
    LIST_FILTERS_BASIC_TESTS
    + LIST_FILTERS_CAPPED_TESTS
    + LIST_FILTERS_CLUSTERED_TESTS
    + LIST_FILTERS_UNKNOWN_FIELD_TESTS
    + LIST_FILTERS_NAME_EDGE_CASE_TESTS
    + LIST_FILTERS_COMMENT_EDGE_CASE_TESTS
    + LIST_FILTERS_COMMENT_TYPE_TESTS
)


@pytest.mark.parametrize("test", pytest_params(LIST_FILTERS_CORE_TESTS))
def test_planCacheListFilters_core(database_client, collection, test):
    """Test planCacheListFilters command core behavior and field acceptance."""
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
