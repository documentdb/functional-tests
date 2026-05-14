"""Tests for case-insensitive index collation behavior.

Validates collation strength semantics (1/2/3), numericOrdering, locale-specific
matching (German, French, Turkish, CJK), collection default collation inheritance
and override, index maintenance (insert/update/delete), long strings, unique
constraint enforcement, range queries, $in queries, and query behavior without
matching collation.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

COLLATION_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="strength_1_ignores_case_and_accents",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 1}},
        ),
        doc=(
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "Cafe"},
            {"_id": 3, "v": "café"},
            {"_id": 4, "v": "CAFÉ"},
        ),
        filter={"v": "cafe"},
        collation={"locale": "en", "strength": 1},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "Cafe"},
            {"_id": 3, "v": "café"},
            {"_id": 4, "v": "CAFÉ"},
        ],
        msg="Strength 1 should ignore both case and accents",
    ),
    IndexQueryTestCase(
        id="strength_2_ignores_case_not_accents",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "Cafe"},
            {"_id": 3, "v": "café"},
        ),
        filter={"v": "cafe"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "cafe"}, {"_id": 2, "v": "Cafe"}],
        msg="Strength 2 should ignore case but distinguish accents",
    ),
    IndexQueryTestCase(
        id="strength_3_case_sensitive_query",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 3}},
        ),
        doc=(
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "Cafe"},
            {"_id": 3, "v": "café"},
        ),
        filter={"v": "cafe"},
        collation={"locale": "en", "strength": 3},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "cafe"}],
        msg="Strength 3 should be case-sensitive",
    ),
    IndexQueryTestCase(
        id="strength_2_accented_not_matched",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "v": "resume"}, {"_id": 2, "v": "résumé"}),
        filter={"v": "resume"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "resume"}],
        msg="Strength 2 should distinguish accented characters",
    ),
    IndexQueryTestCase(
        id="strength_1_accented_matched",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 1}},
        ),
        doc=({"_id": 1, "v": "resume"}, {"_id": 2, "v": "résumé"}),
        filter={"v": "resume"},
        collation={"locale": "en", "strength": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "resume"}, {"_id": 2, "v": "résumé"}],
        msg="Strength 1 should match accented to unaccented",
    ),
    IndexQueryTestCase(
        id="numeric_ordering_match",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_ci",
                "collation": {"locale": "en", "strength": 2, "numericOrdering": True},
            },
        ),
        doc=(
            {"_id": 1, "v": "File2"},
            {"_id": 2, "v": "file2"},
            {"_id": 3, "v": "file10"},
        ),
        filter={"v": "file2"},
        collation={"locale": "en", "strength": 2, "numericOrdering": True},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "File2"}, {"_id": 2, "v": "file2"}],
        msg="Should match case-insensitively with numericOrdering",
    ),
    IndexQueryTestCase(
        id="german_eszett",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "de", "strength": 1}},
        ),
        doc=({"_id": 1, "v": "straße"}, {"_id": 2, "v": "strasse"}),
        filter={"v": "strasse"},
        collation={"locale": "de", "strength": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "straße"}, {"_id": 2, "v": "strasse"}],
        msg="German strength 1 should treat ß and ss as equivalent",
    ),
    IndexQueryTestCase(
        id="french_accents_strength_1",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "fr", "strength": 1}},
        ),
        doc=(
            {"_id": 1, "v": "resume"},
            {"_id": 2, "v": "résumé"},
            {"_id": 3, "v": "RESUME"},
        ),
        filter={"v": "resume"},
        collation={"locale": "fr", "strength": 1},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "v": "resume"},
            {"_id": 2, "v": "résumé"},
            {"_id": 3, "v": "RESUME"},
        ],
        msg="French strength 1 should match all accent and case variants",
    ),
    IndexQueryTestCase(
        id="french_accents_strength_2",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "fr", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "v": "resume"},
            {"_id": 2, "v": "résumé"},
            {"_id": 3, "v": "RESUME"},
        ),
        filter={"v": "resume"},
        collation={"locale": "fr", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "resume"}, {"_id": 3, "v": "RESUME"}],
        msg="French strength 2 should match case variants but not accented",
    ),
    IndexQueryTestCase(
        id="cjk_no_effect",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "zh", "strength": 2}},
        ),
        doc=({"_id": 1, "v": "日本語"}, {"_id": 2, "v": "中文"}),
        filter={"v": "日本語"},
        collation={"locale": "zh", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "日本語"}],
        msg="CJK characters should match exactly",
    ),
    IndexQueryTestCase(
        id="turkish_dotted_i",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "tr", "strength": 2}},
        ),
        doc=({"_id": 1, "v": "i"}, {"_id": 2, "v": "İ"}, {"_id": 3, "v": "I"}),
        filter={"v": "i"},
        collation={"locale": "tr", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "i"}, {"_id": 2, "v": "İ"}],
        msg="Turkish locale should pair i with İ",
    ),
    IndexQueryTestCase(
        id="numeric_ordering_sort",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_ci",
                "collation": {"locale": "en", "strength": 2, "numericOrdering": True},
            },
        ),
        doc=(
            {"_id": 1, "v": "file10"},
            {"_id": 2, "v": "file2"},
            {"_id": 3, "v": "File1"},
        ),
        filter={},
        collation={"locale": "en", "strength": 2, "numericOrdering": True},
        sort={"v": 1},
        expected=[
            {"_id": 3, "v": "File1"},
            {"_id": 2, "v": "file2"},
            {"_id": 1, "v": "file10"},
        ],
        msg="Should sort numerically and case-insensitively",
    ),
    IndexQueryTestCase(
        id="long_string_match",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "v": "a" * 1000}, {"_id": 2, "v": "other"}),
        filter={"v": "A" * 1000},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": "a" * 1000}],
        msg="Should match long strings case-insensitively",
    ),
    IndexQueryTestCase(
        id="range_query_gt",
        indexes=(
            {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "v": "apple"},
            {"_id": 2, "v": "Banana"},
            {"_id": 3, "v": "cherry"},
            {"_id": 4, "v": "APPLE"},
        ),
        filter={"v": {"$gt": "banana"}},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 3, "v": "cherry"}],
        msg="Range query should use case-insensitive ordering",
    ),
    IndexQueryTestCase(
        id="in_query_match",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "name": "Alice"},
            {"_id": 2, "name": "BOB"},
            {"_id": 3, "name": "charlie"},
        ),
        filter={"name": {"$in": ["alice", "bob"]}},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "BOB"}],
        msg="$in should match case-insensitively with collation",
    ),
    IndexQueryTestCase(
        id="insert_after_index",
        indexes=(
            {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=({"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}),
        filter={"name": "ALICE"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}],
        msg="Should find documents inserted after index creation",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COLLATION_TESTS))
def test_case_insensitive_collation(collection, test):
    """Test collation behavior with case-insensitive indexes."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "filter": test.filter,
        "collation": test.collation,
        "sort": test.sort,
    }
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


def test_case_insensitive_collection_default_index_inherits(database_client):
    """Test indexes on collection with default collation inherit it."""
    db = database_client
    db.create_collection("test_inherit", collation={"locale": "en", "strength": 2})
    coll = db["test_inherit"]
    coll.create_index([("name", 1)])
    coll.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}])
    result = execute_command(
        coll,
        {
            "find": coll.name,
            "filter": {"name": "ALICE"},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "name": "Alice"},
            {"_id": 2, "name": "alice"},
        ],
        msg="Index should inherit collection default collation",
    )


def test_case_insensitive_collection_default_explicit_override(database_client):
    """Test index with explicit different collation overrides collection default."""
    db = database_client
    db.create_collection("test_override", collation={"locale": "en", "strength": 2})
    coll = db["test_override"]
    coll.create_index([("name", 1)], collation={"locale": "en", "strength": 3})
    coll.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}])
    result = execute_command(
        coll,
        {
            "find": coll.name,
            "filter": {"name": "Alice"},
            "collation": {"locale": "en", "strength": 3},
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "name": "Alice"}],
        msg="Explicit collation on index should override collection default",
    )


def test_case_insensitive_listindexes_shows_collation(database_client):
    """Test listIndexes shows collation on case-insensitive indexes."""
    db = database_client
    db.create_collection("test_list")
    coll = db["test_list"]
    execute_command(
        coll,
        {
            "createIndexes": coll.name,
            "indexes": [
                {"key": {"name": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}}
            ],
        },
    )
    result = execute_command(coll, {"listIndexes": coll.name})
    indexes = result["cursor"]["firstBatch"]
    ci_index = next(idx for idx in indexes if idx["name"] == "idx_ci")
    collation = ci_index.get("collation", {})
    expected = {"locale": "en", "strength": 2}
    actual = {"locale": collation.get("locale"), "strength": collation.get("strength")}
    assertSuccess(
        actual, expected, raw_res=True, msg="listIndexes should show collation locale and strength"
    )


def test_case_insensitive_maintenance_update_indexed_field(collection):
    """Test updating indexed field value updates the index."""
    collection.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "Bob"}])
    collection.create_index([("name", 1)], collation={"locale": "en", "strength": 2})
    collection.update_one({"_id": 1}, {"$set": {"name": "Charlie"}})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"name": "CHARLIE"},
            "collation": {"locale": "en", "strength": 2},
        },
    )
    assertSuccess(
        result, [{"_id": 1, "name": "Charlie"}], msg="Should find updated value via index"
    )


def test_case_insensitive_maintenance_delete_removes_entry(collection):
    """Test deleting documents removes index entries."""
    collection.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}])
    collection.create_index([("name", 1)], collation={"locale": "en", "strength": 2})
    collection.delete_one({"_id": 1})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"name": "ALICE"},
            "collation": {"locale": "en", "strength": 2},
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "name": "alice"}],
        msg="Should only find remaining document after delete",
    )


def test_case_insensitive_query_without_matching_collation(collection):
    """Test query without collation does not use case-insensitive index for matching."""
    collection.create_index([("name", 1)], collation={"locale": "en", "strength": 2})
    collection.insert_many([{"_id": 1, "name": "Alice"}, {"_id": 2, "name": "alice"}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"name": "alice"},
            "sort": {"_id": 1},
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "name": "alice"}],
        msg="Query without collation should not match case-insensitively",
    )
