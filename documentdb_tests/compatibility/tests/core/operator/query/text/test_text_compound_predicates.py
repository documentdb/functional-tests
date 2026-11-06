"""
$text query operator combined with non-text query predicates (implicit and
explicit $and).

Existing $text coverage exercises the operator in isolation and with a single
co-located equality predicate. This file covers a richer set of compound
filters: $text intersected with an equality, a range ($gt), an `$in`, an array
equality, a `$ne`, an explicit `$and`, and a predicate that excludes every text
match. In every case the result is the intersection of the text match and the
scalar predicate.

Oracle: MongoDB 8.2.4 (functional-tests CI baseline). The engine under test
matches native behavior on every case; no engine divergences are tracked here.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

DOCS = [
    {"_id": 1, "content": "coffee and tea", "category": "drinks", "rating": 5, "tags": ["hot"]},
    {"_id": 2, "content": "coffee beans roasted", "category": "food", "rating": 3, "tags": ["beans"]},
    {"_id": 3, "content": "green tea leaves", "category": "drinks", "rating": 4, "tags": ["green"]},
    {"_id": 4, "content": "python programming", "category": "tech", "rating": 5, "tags": ["code"]},
]

# Property [Compound Intersection]: $text composes with non-text predicates as a
# conjunction; only documents matching both the text search and the scalar
# predicate are returned.
TEXT_COMPOUND_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="text_and_equality",
        filter={"$text": {"$search": "coffee"}, "category": "drinks"},
        expected=[{"_id": 1}],
        msg="$text intersected with an equality predicate returns the common match.",
    ),
    QueryTestCase(
        id="text_and_range_gt",
        filter={"$text": {"$search": "coffee"}, "rating": {"$gt": 4}},
        expected=[{"_id": 1}],
        msg="$text intersected with a $gt range keeps only the high-rated match.",
    ),
    QueryTestCase(
        id="text_or_terms_and_in",
        filter={"$text": {"$search": "coffee tea"}, "category": {"$in": ["drinks"]}},
        expected=[{"_id": 1}, {"_id": 3}],
        msg="$text OR-of-terms intersected with an $in keeps the drinks documents.",
    ),
    QueryTestCase(
        id="text_explicit_and_with_range",
        filter={"$and": [{"$text": {"$search": "coffee"}}, {"rating": {"$gte": 3}}]},
        expected=[{"_id": 1}, {"_id": 2}],
        msg="$text inside an explicit $and intersects with a $gte range predicate.",
    ),
    QueryTestCase(
        id="text_and_array_equality",
        filter={"$text": {"$search": "coffee"}, "tags": "beans"},
        expected=[{"_id": 2}],
        msg="$text intersected with an array-membership equality returns the match.",
    ),
    QueryTestCase(
        id="text_and_not_equal",
        filter={"$text": {"$search": "tea"}, "category": {"$ne": "food"}},
        expected=[{"_id": 1}, {"_id": 3}],
        msg="$text intersected with a $ne predicate excludes the food document.",
    ),
    QueryTestCase(
        id="text_and_predicate_excludes_all",
        filter={"$text": {"$search": "coffee"}, "category": "tech"},
        expected=[],
        msg="When the scalar predicate excludes every text match the result is empty.",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TEXT_COMPOUND_TESTS))
def test_text_compound_predicates(collection, test: QueryTestCase):
    """$text intersects with co-located non-text predicates as a conjunction."""
    collection.create_index([("content", "text")])
    collection.insert_many([dict(d) for d in DOCS])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": {"_id": 1},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)
