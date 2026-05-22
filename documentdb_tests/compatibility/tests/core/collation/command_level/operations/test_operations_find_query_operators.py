"""Representative query operator wiring tests for collation in the find command.

One test per operator category confirms collation is correctly wired to the
query engine for find. Exhaustive collation behavior is tested in the
collation-specific parameter files (strength, locale, etc.).
"""

from __future__ import annotations

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Find Query Operator Wiring]: the find command's collation parameter
# affects comparison, logical, array, and expression operators in the filter;
# $regex, $exists, $type, bitwise, and geospatial operators are NOT affected.
COLLATION_FIND_QUERY_OPERATOR_TESTS: list[CommandTestCase] = [
    # Comparison operators - affected.
    CommandTestCase(
        "find_eq_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$eq": "apple"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="find $eq should use collation for case-insensitive matching",
    ),
    CommandTestCase(
        "find_ne_collation",
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
        msg="find $ne should use collation",
    ),
    CommandTestCase(
        "find_gt_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$gt": "apple"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="find $gt should use collation",
    ),
    CommandTestCase(
        "find_lte_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$lte": "apple"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="find $lte should use collation",
    ),
    CommandTestCase(
        "find_in_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$in": ["APPLE"]}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 2, "x": "Apple"}],
        msg="find $in should use collation",
    ),
    CommandTestCase(
        "find_nin_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$nin": ["APPLE"]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="find $nin should use collation",
    ),
    # Logical operators - affected (they wrap affected operators).
    CommandTestCase(
        "find_and_collation",
        docs=[
            {"_id": 1, "x": "apple", "y": "red"},
            {"_id": 2, "x": "Apple", "y": "Red"},
            {"_id": 3, "x": "banana", "y": "yellow"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$and": [{"x": "apple"}, {"y": "red"}]},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[
            {"_id": 1, "x": "apple", "y": "red"},
            {"_id": 2, "x": "Apple", "y": "Red"},
        ],
        msg="find $and should use collation in sub-conditions",
    ),
    CommandTestCase(
        "find_or_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "Cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$or": [{"x": "APPLE"}, {"x": "cherry"}]},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}, {"_id": 3, "x": "Cherry"}],
        msg="find $or should use collation in sub-conditions",
    ),
    CommandTestCase(
        "find_nor_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "banana"},
            {"_id": 3, "x": "Cherry"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$nor": [{"x": "APPLE"}, {"x": "cherry"}]},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 2, "x": "banana"}],
        msg="find $nor should use collation in sub-conditions",
    ),
    CommandTestCase(
        "find_not_collation",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$not": {"$eq": "apple"}}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 3, "x": "banana"}],
        msg="find $not should use collation in wrapped condition",
    ),
    # Array operators - affected.
    CommandTestCase(
        "find_all_collation",
        docs=[
            {"_id": 1, "arr": ["Apple", "Banana"]},
            {"_id": 2, "arr": ["cherry", "date"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"arr": {"$all": ["apple", "banana"]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "arr": ["Apple", "Banana"]}],
        msg="find $all should use collation",
    ),
    CommandTestCase(
        "find_elemMatch_collation",
        docs=[
            {"_id": 1, "arr": [{"name": "Apple", "v": 1}]},
            {"_id": 2, "arr": [{"name": "banana", "v": 2}]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"arr": {"$elemMatch": {"name": "apple"}}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "arr": [{"name": "Apple", "v": 1}]}],
        msg="find $elemMatch should use collation",
    ),
    # $size - NOT affected (numeric comparison).
    CommandTestCase(
        "find_size_not_affected",
        docs=[
            {"_id": 1, "arr": ["a", "b"]},
            {"_id": 2, "arr": ["a"]},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"arr": {"$size": 2}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "arr": ["a", "b"]}],
        msg="find $size is not affected by collation (numeric)",
    ),
    # $exists - NOT affected.
    CommandTestCase(
        "find_exists_not_affected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$exists": True}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find $exists is not affected by collation",
    ),
    # $type - NOT affected.
    CommandTestCase(
        "find_type_not_affected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": 42},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$type": "string"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find $type is not affected by collation",
    ),
    # $regex - NOT affected by collation (uses its own flags).
    CommandTestCase(
        "find_regex_not_affected",
        docs=[
            {"_id": 1, "x": "Apple"},
            {"_id": 2, "x": "apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$regex": "^apple$"}},
            "sort": {"_id": 1},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 2, "x": "apple"}],
        msg="find $regex is not affected by collation (only matches exact case)",
    ),
    # $mod - NOT affected (numeric).
    CommandTestCase(
        "find_mod_not_affected",
        docs=[
            {"_id": 1, "x": 6},
            {"_id": 2, "x": 7},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"x": {"$mod": [3, 0]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": 6}],
        msg="find $mod is not affected by collation (numeric)",
    ),
    # Bitwise - NOT affected.
    CommandTestCase(
        "find_bitsAllSet_not_affected",
        docs=[
            {"_id": 1, "flags": 7},
            {"_id": 2, "flags": 3},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"flags": {"$bitsAllSet": 5}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "flags": 7}],
        msg="find $bitsAllSet is not affected by collation",
    ),
    # $expr - affected.
    CommandTestCase(
        "find_expr_collation",
        docs=[
            {"_id": 1, "a": "apple", "b": "Apple"},
            {"_id": 2, "a": "apple", "b": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$expr": {"$eq": ["$a", "$b"]}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "a": "apple", "b": "Apple"}],
        msg="find $expr should use collation for expression comparisons",
    ),
    # $where - NOT affected (JavaScript evaluation ignores collation).
    CommandTestCase(
        "find_where_not_affected",
        docs=[
            {"_id": 1, "x": "apple"},
            {"_id": 2, "x": "Apple"},
            {"_id": 3, "x": "banana"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$where": "this.x == 'apple'"},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "apple"}],
        msg="find $where is not affected by collation (JavaScript uses binary comparison)",
    ),
    # Geospatial - NOT affected.
    CommandTestCase(
        "find_geoWithin_not_affected",
        docs=[
            {"_id": 1, "loc": [0, 0], "x": "Apple"},
            {"_id": 2, "loc": [50, 50], "x": "apple"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"loc": {"$geoWithin": {"$center": [[0, 0], 10]}}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "loc": [0, 0], "x": "Apple"}],
        msg="find $geoWithin is not affected by collation",
    ),
    # Text search - NOT affected by explicit collation.
    CommandTestCase(
        "find_text_not_affected",
        indexes=[IndexModel([("x", "text")])],
        docs=[
            {"_id": 1, "x": "hello world"},
            {"_id": 2, "x": "goodbye"},
        ],
        command=lambda ctx: {
            "find": ctx.collection,
            "filter": {"$text": {"$search": "hello"}},
            "collation": {"locale": "en", "strength": 2},
        },
        expected=[{"_id": 1, "x": "hello world"}],
        msg="find $text uses its own locale, not command-level collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_FIND_QUERY_OPERATOR_TESTS))
def test_collation_find_query_operators(database_client, collection, test):
    """Test collation wiring for each query operator category in find."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
