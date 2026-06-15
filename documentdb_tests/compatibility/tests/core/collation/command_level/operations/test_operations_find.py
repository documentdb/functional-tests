"""Tests for collation behavior in the find command."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BAD_VALUE_ERROR,
    MISSING_FIELD_ERROR,
    TYPE_MISMATCH_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.target_collection import CustomCollection

# Property [Find Filter Matching]: collation affects equality and comparison
# operators in the find filter, enabling case-insensitive and accent-insensitive
# matching depending on strength.
COLLATION_FIND_FILTER_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "filter_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
            {"_id": 4, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        msg="find with strength 2 should match case-insensitively",
    ),
    CommandTestCase(
        "filter_eq_accent_insensitive",
        docs=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "caf\u00e9"},
            {"_id": 3, "x": "other"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "cafe"},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "cafe"},
            {"_id": 2, "x": "caf\u00e9"},
        ],
        msg="find with strength 1 should match accent-insensitively",
    ),
    CommandTestCase(
        "filter_ne_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$ne": "apple"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="find $ne with strength 2 should exclude case variants",
    ),
    CommandTestCase(
        "filter_gt_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "Banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$gt": "apple"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}, {"_id": 4, "x": "Banana"}],
        msg="find $gt with strength 2 should compare case-insensitively",
    ),
    CommandTestCase(
        "filter_in_case_insensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$in": ["apple", "cherry"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 4, "x": "cherry"},
        ],
        msg="find $in with strength 2 should match case variants",
    ),
    CommandTestCase(
        "filter_lte_gte_range",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$gte": "apple", "$lte": "banana"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        msg="find $gte/$lte with strength 2 should define range case-insensitively",
    ),
    CommandTestCase(
        "filter_strength3_case_sensitive",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find with strength 3 should match case-sensitively",
    ),
    CommandTestCase(
        "filter_dotted_path_case_insensitive",
        docs=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
            {"_id": 3, "a": {"b": "banana"}},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"a.b": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "a": {"b": "apple"}},
            {"_id": 2, "a": {"b": "Apple"}},
        ],
        msg="find on dotted path should use collation for case-insensitive matching",
    ),
]

# Property [Find Sort Ordering]: collation affects the sort order of string
# values in find results, respecting locale-specific ordering rules.
COLLATION_FIND_SORT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_strength1_groups_variants",
        docs=[
            {"_id": 1, "x": "b"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
            {"_id": 1, "x": "b"},
        ],
        msg="find sort with strength 1 should group case and accent variants together",
    ),
    CommandTestCase(
        "sort_strength2_separates_accents",
        docs=[
            {"_id": 1, "x": "b"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 3, "x": "A"},
            {"_id": 4, "x": "a"},
            {"_id": 2, "x": "\u00e1"},
            {"_id": 1, "x": "b"},
        ],
        msg="find sort with strength 2 should separate accented from unaccented",
    ),
    CommandTestCase(
        "sort_numeric_ordering",
        docs=[
            {"_id": 1, "x": "file2"},
            {"_id": 2, "x": "file10"},
            {"_id": 3, "x": "file1"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "numericOrdering": True},
        },
        expected=[
            {"_id": 3, "x": "file1"},
            {"_id": 1, "x": "file2"},
            {"_id": 2, "x": "file10"},
        ],
        msg="find sort with numericOrdering should sort embedded numbers numerically",
    ),
    CommandTestCase(
        "sort_casefirst_upper",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "APPLE"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "caseFirst": "upper"},
        },
        expected=[
            {"_id": 3, "x": "APPLE"},
            {"_id": 2, "x": "Apple"},
            {"_id": 1, "x": "apple"},
        ],
        msg="find sort with caseFirst upper should sort uppercase before lowercase",
    ),
    CommandTestCase(
        "sort_backwards_accents",
        docs=[
            {"_id": 1, "x": "cot\u00e9"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 3, "x": "c\u00f4t\u00e9"},
            {"_id": 4, "x": "cote"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "collation": {"locale": "en", "backwards": True},
        },
        expected=[
            {"_id": 4, "x": "cote"},
            {"_id": 2, "x": "c\u00f4te"},
            {"_id": 1, "x": "cot\u00e9"},
            {"_id": 3, "x": "c\u00f4t\u00e9"},
        ],
        msg="find sort with backwards should reverse secondary (accent) differences",
    ),
    CommandTestCase(
        "sort_descending_with_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": -1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 3, "x": "cherry"},
            {"_id": 2, "x": "banana"},
            {"_id": 1, "x": "apple"},
        ],
        msg="find sort descending should respect collation ordering in reverse",
    ),
]

# Property [Find Collation Validation]: the find command validates the collation
# document the same way as aggregate - non-object types, missing locale, and
# invalid locale strings produce errors.
COLLATION_FIND_VALIDATION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "validation_non_object_collation",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "collation": "en",
        },
        error_code=TYPE_MISMATCH_ERROR,
        msg="find with non-object collation should produce an error",
    ),
    CommandTestCase(
        "validation_missing_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "collation": {"strength": 2},
        },
        error_code=MISSING_FIELD_ERROR,
        msg="find with collation missing locale should produce an error",
    ),
    CommandTestCase(
        "validation_invalid_locale",
        docs=[{"_id": 1, "x": "a"}],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "collation": {"locale": "invalid_locale_xyz"},
        },
        error_code=BAD_VALUE_ERROR,
        msg="find with invalid locale string should produce an error",
    ),
]

# Property [Find Collection Default Collation]: when no collation is specified
# on the find command, the collection's default collation is used; an explicit
# collation overrides the collection default.
COLLATION_FIND_COLLECTION_DEFAULT_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "collection_default_inherited",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="find should inherit collection default collation when none specified",
    ),
    CommandTestCase(
        "collection_default_overridden",
        target_collection=CustomCollection(options={"collation": {"locale": "en", "strength": 2}}),
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "collation": {"locale": "en", "strength": 3},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find with explicit collation should override collection default",
    ),
    CommandTestCase(
        "no_collation_binary_comparison",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find without collation should use binary comparison",
    ),
]

# Property [Find Min Max with Collation]: collation affects the min/max bounds
# used for index-based range queries in the find command.
COLLATION_FIND_MIN_MAX_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "sort_with_limit",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "limit": 2,
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
        ],
        msg="find with collation sort and limit should return first N in collation order",
    ),
    CommandTestCase(
        "sort_with_skip",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {},
            "sort": {"x": 1},
            "skip": 2,
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 3, "x": "banana"},
            {"_id": 4, "x": "cherry"},
        ],
        msg="find with collation sort and skip should skip first N in collation order",
    ),
]

# Property [Find Non-String Values Unaffected]: collation does not change the
# comparison behavior of non-string types.
COLLATION_FIND_NON_STRING_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "non_string_int_filter",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 2},
            {"_id": 3, "x": 3},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$gt": 1}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 2, "x": 2}, {"_id": 3, "x": 3}],
        msg="collation should not affect integer comparison in find",
    ),
    CommandTestCase(
        "non_string_null_filter",
        docs=[
            {"_id": 1, "x": None},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "Apple"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": None},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": None}],
        msg="collation should not affect null matching in find",
    ),
]

# Property [Find Array Field Matching]: collation affects element-wise
# comparison when filtering on array fields, matching any element that
# satisfies the collation comparison.
COLLATION_FIND_ARRAY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "array_eq_case_insensitive",
        docs=[
            {"_id": 1, "x": ["Apple", "banana"]},
            {"_id": 2, "x": ["cherry", "date"]},
            {"_id": 3, "x": ["APPLE", "fig"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": ["Apple", "banana"]},
            {"_id": 3, "x": ["APPLE", "fig"]},
        ],
        msg="find on array field with strength 2 should match any case-variant element",
    ),
    CommandTestCase(
        "array_in_case_insensitive",
        docs=[
            {"_id": 1, "x": ["apple", "banana"]},
            {"_id": 2, "x": ["Cherry", "date"]},
            {"_id": 3, "x": ["fig"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$in": ["APPLE", "cherry"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": ["apple", "banana"]},
            {"_id": 2, "x": ["Cherry", "date"]},
        ],
        msg="find $in on array field with collation should match case-variant elements",
    ),
    CommandTestCase(
        "array_gt_case_insensitive",
        docs=[
            {"_id": 1, "x": ["apple"]},
            {"_id": 2, "x": ["banana"]},
            {"_id": 3, "x": ["cherry"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$gt": "Apple"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 2, "x": ["banana"]},
            {"_id": 3, "x": ["cherry"]},
        ],
        msg="find $gt on array field with collation should compare case-insensitively",
    ),
    CommandTestCase(
        "array_elemmatch_case_insensitive",
        docs=[
            {"_id": 1, "x": [{"v": "Apple"}, {"v": "banana"}]},
            {"_id": 2, "x": [{"v": "cherry"}]},
            {"_id": 3, "x": [{"v": "APPLE"}]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$elemMatch": {"v": "apple"}}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": [{"v": "Apple"}, {"v": "banana"}]},
            {"_id": 3, "x": [{"v": "APPLE"}]},
        ],
        msg="find $elemMatch with collation should match case-variant elements",
    ),
    CommandTestCase(
        "array_no_collation_binary",
        docs=[
            {"_id": 1, "x": ["Apple", "banana"]},
            {"_id": 2, "x": ["apple", "cherry"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": "apple"},
        },
        expected=[{"_id": 2, "x": ["apple", "cherry"]}],
        msg="find on array field without collation should use binary comparison",
    ),
]

COLLATION_FIND_TESTS = (
    COLLATION_FIND_FILTER_TESTS
    + COLLATION_FIND_SORT_TESTS
    + COLLATION_FIND_VALIDATION_TESTS
    + COLLATION_FIND_COLLECTION_DEFAULT_TESTS
    + COLLATION_FIND_MIN_MAX_TESTS
    + COLLATION_FIND_NON_STRING_TESTS
    + COLLATION_FIND_ARRAY_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_FIND_TESTS))
def test_collation_find(database_client, collection, test):
    """Test collation behavior in the find command."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
