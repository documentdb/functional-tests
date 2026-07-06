"""Tests for collation with text and geospatial indexes."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import CANNOT_CREATE_INDEX_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Text Index Collation Incompatibility]: a text index cannot be
# created with a collation other than simple; creating one on a collection
# with a non-simple default collation requires specifying
# collation {locale: "simple"} on the index.
COLLATION_TEXT_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "text_index_with_non_simple_collation_rejected",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [{"key": {"x": "text"}, "name": "x_text", "collation": {"locale": "en"}}],
        },
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="text index with non-simple collation should be rejected",
    ),
    CommandTestCase(
        "text_index_inherits_non_simple_collation_rejected",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [{"key": {"x": "text"}, "name": "x_text"}],
        },
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="text index inheriting non-simple collation from collection should be rejected",
    ),
    CommandTestCase(
        "text_index_on_simple_collection",
        docs=[{"_id": 1, "x": "hello world"}],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [{"key": {"x": "text"}, "name": "x_text"}],
        },
        expected={"ok": Eq(1.0)},
        msg="text index should be creatable on collection without collation",
    ),
    CommandTestCase(
        "text_index_with_simple_collation_on_collated_collection",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[{"_id": 1, "x": "hello world"}],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {"key": {"x": "text"}, "name": "x_text", "collation": {"locale": "simple"}}
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="text index with simple collation should be creatable on collated collection",
    ),
    CommandTestCase(
        "text_search_ignores_collation",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "cafe latte"},
            {"_id": 2, "x": "Cafe Mocha"},
            {"_id": 3, "x": "tea"},
        ],
        indexes=[
            IndexModel([("x", "text")], collation={"locale": "simple"}, name="x_text"),
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$text": {"$search": "cafe"}},
            "sort": {"_id": 1},
        },
        expected=[
            {"_id": 1, "x": "cafe latte"},
            {"_id": 2, "x": "Cafe Mocha"},
        ],
        msg="text search should use its own case-folding, not collection or index collation",
    ),
]

# Property [2d Index Collation Restriction]: a 2d index cannot be created with
# a non-simple collation, including when inherited from a collated collection;
# specifying {locale: "simple"} explicitly is accepted.
COLLATION_2D_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "2d_index_rejects_non_simple_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"loc": "2d"},
                    "name": "loc_2d",
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="2d index should reject non-simple collation",
    ),
    CommandTestCase(
        "2d_index_inherits_non_simple_collation_rejected",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [{"key": {"loc": "2d"}, "name": "loc_2d"}],
        },
        error_code=CANNOT_CREATE_INDEX_ERROR,
        msg="2d index inheriting non-simple collation from collection should be rejected",
    ),
    CommandTestCase(
        "2d_index_accepts_simple_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"loc": "2d"},
                    "name": "loc_2d",
                    "collation": {"locale": "simple"},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="2d index should accept simple collation",
    ),
    CommandTestCase(
        "2d_on_collated_collection_explicit_simple_accepted",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"loc": "2d"},
                    "name": "loc_2d",
                    "collation": {"locale": "simple"},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="2d index with explicit simple collation on collated collection should succeed",
    ),
]

# Property [2dsphere Index Collation Support]: a 2dsphere index can be created
# with any collation, including non-simple and inherited from a collated
# collection.
COLLATION_2DSPHERE_INDEX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "2dsphere_index_accepts_non_simple_collation",
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [
                {
                    "key": {"loc": "2dsphere"},
                    "name": "loc_2dsphere_collated",
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": Eq(1.0)},
        msg="2dsphere index should accept non-simple collation",
    ),
    CommandTestCase(
        "2dsphere_on_collated_collection_inherits",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[],
        command=lambda ctx: {
            "createIndexes": ctx.collection,
            "indexes": [{"key": {"loc": "2dsphere"}, "name": "loc_2ds"}],
        },
        expected={"ok": Eq(1.0)},
        msg="2dsphere index on collated collection should inherit collation",
    ),
]

COLLATION_SPECIAL_INDEX_TESTS = (
    COLLATION_TEXT_INDEX_TESTS + COLLATION_2D_INDEX_TESTS + COLLATION_2DSPHERE_INDEX_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_SPECIAL_INDEX_TESTS))
def test_collation_special_indexes(database_client, collection, test):
    """Test collation with text and geospatial indexes."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    expected = test.build_expected(ctx)
    assertResult(
        result,
        expected=expected,
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(expected, list),
    )
