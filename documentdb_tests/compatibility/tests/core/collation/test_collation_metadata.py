"""Tests for collation metadata reported by listCollections and listIndexes."""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq
from documentdb_tests.framework.target_collection import CustomCollection

# Property [ListCollections Reports Full Collation]: listCollections reports the
# complete collation document including all specified options, not just locale.
COLLATION_LIST_COLLECTIONS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "list_collections_full_collation",
        target_collection=CustomCollection(
            options={"collation": {"locale": "en", "strength": 2, "caseLevel": True}}
        ),
        docs=[],
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "options.collation.locale": Eq("en"),
                "options.collation.strength": Eq(2),
                "options.collation.caseLevel": Eq(True),
            },
        },
        msg="listCollections should report full collation document with all options",
    ),
    CommandTestCase(
        "list_collections_numeric_ordering",
        target_collection=CustomCollection(
            options={"collation": {"locale": "en", "numericOrdering": True}}
        ),
        docs=[],
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "options.collation.locale": Eq("en"),
                "options.collation.numericOrdering": Eq(True),
            },
        },
        msg="listCollections should report numericOrdering in collation",
    ),
    CommandTestCase(
        "list_collections_casefirst",
        target_collection=CustomCollection(
            options={"collation": {"locale": "en", "caseFirst": "upper"}}
        ),
        docs=[],
        command=lambda ctx: {"listCollections": 1, "filter": {"name": ctx.collection}},
        expected={
            "cursor.firstBatch.0": {
                "options.collation.locale": Eq("en"),
                "options.collation.caseFirst": Eq("upper"),
            },
        },
        msg="listCollections should report caseFirst in collation",
    ),
]

# Property [ListIndexes Reports Index Collation]: listIndexes reports the
# collation document for indexes created with a specific collation, including
# all specified collation options.
COLLATION_LIST_INDEXES_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "list_indexes_reports_collation_locale_and_strength",
        docs=[{"_id": 1, "x": "a"}],
        indexes=[
            IndexModel(
                [("x", 1)],
                name="x_collated",
                collation={"locale": "fr", "strength": 1},
            )
        ],
        command=lambda ctx: {"listIndexes": ctx.collection},
        expected={
            "cursor.firstBatch.1": {
                "name": Eq("x_collated"),
                "collation.locale": Eq("fr"),
                "collation.strength": Eq(1),
            },
        },
        msg="listIndexes should report collation locale and strength on index",
    ),
    CommandTestCase(
        "list_indexes_reports_numeric_ordering",
        docs=[{"_id": 1, "x": "a"}],
        indexes=[
            IndexModel(
                [("x", 1)],
                name="x_numeric",
                collation={"locale": "en", "numericOrdering": True},
            )
        ],
        command=lambda ctx: {"listIndexes": ctx.collection},
        expected={
            "cursor.firstBatch.1": {
                "name": Eq("x_numeric"),
                "collation.locale": Eq("en"),
                "collation.numericOrdering": Eq(True),
            },
        },
        msg="listIndexes should report numericOrdering in index collation",
    ),
]

COLLATION_METADATA_TESTS = COLLATION_LIST_COLLECTIONS_TESTS + COLLATION_LIST_INDEXES_TESTS


@pytest.mark.parametrize("test", pytest_params(COLLATION_METADATA_TESTS))
def test_collation_metadata(database_client, collection, test):
    """Test that collation metadata is correctly reported."""
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
