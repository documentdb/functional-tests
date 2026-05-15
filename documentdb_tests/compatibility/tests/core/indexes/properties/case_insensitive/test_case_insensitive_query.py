"""Tests for case-insensitive index query behavior.

Validates that queries use case-insensitive indexes correctly:
string matching, collation requirement, $regex behavior,
multikey arrays, sort ordering, and collection default collation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="mixed_case",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "name": "hello"},
            {"_id": 2, "name": "Hello"},
            {"_id": 3, "name": "HELLO"},
            {"_id": 4, "name": "hElLo"},
        ),
        filter={"name": "hello"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "name": "hello"},
            {"_id": 2, "name": "Hello"},
            {"_id": 3, "name": "HELLO"},
            {"_id": 4, "name": "hElLo"},
        ],
        msg="Should match all case variations",
    ),
    IndexQueryTestCase(
        id="empty_string",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": ""}, {"_id": 2, "name": "a"}),
        filter={"name": ""},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "name": ""}],
        msg="Should match empty string",
    ),
    IndexQueryTestCase(
        id="single_char",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": "a"}, {"_id": 2, "name": "A"}, {"_id": 3, "name": "b"}),
        filter={"name": "a"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "name": "a"}, {"_id": 2, "name": "A"}],
        msg="Should match single char case-insensitively",
    ),
    IndexQueryTestCase(
        id="numeric_string",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "v": "123abc"}, {"_id": 2, "v": "123ABC"}, {"_id": 3, "v": "123xyz"}),
        filter={"v": "123abc"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "123abc"}, {"_id": 2, "v": "123ABC"}],
        msg="Should match numeric strings case-insensitively",
    ),
    IndexQueryTestCase(
        id="special_chars",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "v": "!@#"}, {"_id": 2, "v": "abc"}),
        filter={"v": "!@#"},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": "!@#"}],
        msg="Should match special characters exactly",
    ),
    IndexQueryTestCase(
        id="different_strength",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": "cafe"}, {"_id": 2, "name": "café"}),
        filter={"name": "cafe"},
        collation={"locale": "en", "strength": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "name": "cafe"}, {"_id": 2, "name": "café"}],
        msg="Strength 1 should match accented variants too",
    ),
    IndexQueryTestCase(
        id="different_locale",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}),
        filter={"name": "Alice"},
        collation={"locale": "fr", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}],
        msg="Should match case-insensitively with different locale at same strength",
    ),
    IndexQueryTestCase(
        id="regex_with_i_flag",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": "Hello"}, {"_id": 2, "name": "world"}),
        filter={"name": {"$regex": "^hello", "$options": "i"}},
        expected=[{"_id": 1, "name": "Hello"}],
        msg="$regex with i flag should still work via collection scan",
    ),
    IndexQueryTestCase(
        id="regex_without_i_flag",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": "Hello"}, {"_id": 2, "name": "hello"}),
        filter={"name": {"$regex": "^hello"}},
        expected=[{"_id": 2, "name": "hello"}],
        msg="$regex without i flag should be case-sensitive",
    ),
    IndexQueryTestCase(
        id="multikey_array_match",
        indexes=(
            {"key": {"tags": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "tags": ["Hello", "World"]},
            {"_id": 2, "tags": ["other"]},
        ),
        filter={"tags": "hello"},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "tags": ["Hello", "World"]}],
        msg="Should match array element case-insensitively",
    ),
    IndexQueryTestCase(
        id="multikey_multiple_matches",
        indexes=(
            {"key": {"tags": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "tags": ["Apple", "Banana"]},
            {"_id": 2, "tags": ["APPLE", "cherry"]},
            {"_id": 3, "tags": ["other"]},
        ),
        filter={"tags": "apple"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "tags": ["Apple", "Banana"]},
            {"_id": 2, "tags": ["APPLE", "cherry"]},
        ],
        msg="Should match array elements across documents case-insensitively",
    ),
    IndexQueryTestCase(
        id="multikey_in_query",
        indexes=(
            {"key": {"tags": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "tags": ["Hello"]},
            {"_id": 2, "tags": ["World"]},
            {"_id": 3, "tags": ["other"]},
        ),
        filter={"tags": {"$in": ["HELLO", "WORLD"]}},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "tags": ["Hello"]},
            {"_id": 2, "tags": ["World"]},
        ],
        msg="Should match $in values case-insensitively on multikey",
    ),
    IndexQueryTestCase(
        id="strength_null_defaults_to_tertiary",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "name": "hello"},
            {"_id": 2, "name": "Hello"},
        ),
        filter={"name": "hello"},
        collation={"locale": "en"},
        expected=[{"_id": 1, "name": "hello"}],
        msg="Omitting strength should default to tertiary (case-sensitive)",
    ),
    IndexQueryTestCase(
        id="expr_eq",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "name": "Hello"},
            {"_id": 2, "name": "hello"},
            {"_id": 3, "name": "world"},
        ),
        filter={"$expr": {"$eq": ["$name", "hello"]}},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "name": "Hello"},
            {"_id": 2, "name": "hello"},
        ],
        msg="$expr with $eq should match case-insensitively when collation is specified",
    ),
    IndexQueryTestCase(
        id="sort_with_collation",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "name": "banana"},
            {"_id": 2, "name": "Apple"},
            {"_id": 3, "name": "cherry"},
        ),
        filter={},
        collation={"locale": "en", "strength": 2},
        sort={"name": 1},
        expected=[
            {"_id": 2, "name": "Apple"},
            {"_id": 1, "name": "banana"},
            {"_id": 3, "name": "cherry"},
        ],
        msg="Should sort case-insensitively with collation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(QUERY_TESTS))
def test_case_insensitive_query(collection, test):
    """Test case-insensitive index query behavior."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    if test.collation:
        cmd["collation"] = test.collation
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)
