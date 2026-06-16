"""Tests for collation effects on _id field filtering."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Find on _id with Collation]: collation affects equality and
# comparison operators on the _id field, enabling case-insensitive matching
# despite the unique _id index.
COLLATION_ID_FIND_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "find_id_eq_case_insensitive",
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 2},
            {"_id": "cherry", "v": 3},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": "APPLE"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": "apple", "v": 1}],
        msg="find on _id with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "find_id_in_case_insensitive",
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 2},
            {"_id": "cherry", "v": 3},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": {"$in": ["APPLE", "BANANA"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 2},
        ],
        msg="find $in on _id with collation should match case variants",
    ),
    CommandTestCase(
        "find_id_gt_case_insensitive",
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 2},
            {"_id": "cherry", "v": 3},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": {"$gt": "banana"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": "cherry", "v": 3}],
        msg="find $gt on _id with collation should compare case-insensitively",
    ),
    CommandTestCase(
        "find_id_no_collation_binary",
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Apple", "v": 2},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": "apple"},
        },
        expected=[{"_id": "apple", "v": 1}],
        msg="find on _id without collation should use binary comparison",
    ),
]

# Property [Collection Default Collation on _id]: a collection with a default
# collation uses it for _id field matching when no explicit collation is
# specified.
COLLATION_ID_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_id_match",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 2},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"_id": "APPLE"},
        },
        expected=[{"_id": "apple", "v": 1}],
        msg="collection default collation should apply to _id matching",
    ),
]

# Property [Update on _id with Collation]: collation affects the filter on _id
# in update commands.
COLLATION_ID_UPDATE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "update_id_filter_case_insensitive",
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 1},
        ],
        command=lambda ctx: {
            "update": ctx.collection,
            "updates": [
                {
                    "q": {"_id": "APPLE"},
                    "u": {"$set": {"v": 2}},
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1, "nModified": 1},
        msg="update filter on _id should use collation",
    ),
]

# Property [Delete on _id with Collation]: collation affects the filter on _id
# in delete commands.
COLLATION_ID_DELETE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "delete_id_filter_case_insensitive",
        docs=[
            {"_id": "apple", "v": 1},
            {"_id": "Banana", "v": 2},
        ],
        command=lambda ctx: {
            "delete": ctx.collection,
            "deletes": [
                {
                    "q": {"_id": "APPLE"},
                    "limit": 1,
                    "collation": {"locale": "en", "strength": 2},
                }
            ],
        },
        expected={"ok": 1.0, "n": 1},
        msg="delete filter on _id should use collation",
    ),
]

# Property [Sort on _id with Collation]: collation affects sort ordering on the
# _id field.
COLLATION_ID_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_id_case_insensitive",
        docs=[
            {"_id": "cherry"},
            {"_id": "Apple"},
            {"_id": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": "Apple"},
            {"_id": "banana"},
            {"_id": "cherry"},
        ],
        msg="sort on _id should use collation for case-insensitive ordering",
    ),
]

COLLATION_ID_FIELD_TESTS: list[CommandTestCase] = (
    COLLATION_ID_FIND_TESTS
    + COLLATION_ID_COLLECTION_DEFAULT_TESTS
    + COLLATION_ID_UPDATE_TESTS
    + COLLATION_ID_DELETE_TESTS
    + COLLATION_ID_SORT_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_ID_FIELD_TESTS))
def test_collation_id_field(database_client, collection, test):
    """Test collation effects on _id field operations."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=not isinstance(test.build_expected(ctx), list),
    )
