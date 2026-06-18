"""
Placement and validation rules for `$meta: "textScore"` with the $text operator.

Existing coverage asserts that a projected textScore is returned and that
results can be ordered by it. This file covers the placement contract around
the metadata: the score may be sorted on without being projected, it ranks
documents by match frequency (assertions are on ordering, never on the
engine-specific score value), and requesting the score in a projection or a
sort without any `$text` query in the filter is rejected with the documented
metadata-not-available error.

Oracle: MongoDB 7.0 (functional-tests CI baseline). The engine under test
matches native behavior on every case; no engine divergences are tracked here.
"""

import pytest

from documentdb_tests.framework.assertions import assertFailureCode, assertProperties, assertSuccess
from documentdb_tests.framework.error_codes import QUERY_METADATA_NOT_AVAILABLE_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.property_checks import Exists, IsType, Len

pytestmark = pytest.mark.find


def _create_text_index(collection):
    collection.create_index([("content", "text")])


def test_text_score_projection_returns_double(collection):
    """A projected textScore is a numeric (double) field on each matched document."""
    _create_text_index(collection)
    collection.insert_one({"_id": 1, "content": "coffee and more coffee"})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "coffee"}},
            "projection": {"score": {"$meta": "textScore"}},
        },
    )
    assertProperties(
        result,
        {
            "cursor.firstBatch": Len(1),
            "cursor.firstBatch.0._id": Exists(),
            "cursor.firstBatch.0.score": IsType("double"),
        },
        raw_res=True,
        msg="A projected textScore should be a double on the matched document.",
    )


def test_text_score_sort_without_projection_ranks_by_frequency(collection):
    """Sorting by textScore (without projecting it) orders documents by match frequency."""
    _create_text_index(collection)
    collection.insert_many(
        [
            {"_id": 1, "content": "coffee"},
            {"_id": 2, "content": "coffee coffee coffee"},
            {"_id": 3, "content": "coffee coffee"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"$text": {"$search": "coffee"}},
            "sort": {"score": {"$meta": "textScore"}},
            "projection": {"_id": 1},
        },
    )
    # Assert ordering only; the absolute textScore value is engine-specific.
    assertSuccess(
        result,
        [{"_id": 2}, {"_id": 3}, {"_id": 1}],
        msg="textScore sort orders the most-frequent match first, even unprojected.",
    )


def test_text_score_projection_without_text_query_errors(collection):
    """Projecting textScore without a $text query fails with the metadata-not-available code."""
    _create_text_index(collection)
    collection.insert_one({"_id": 1, "content": "coffee"})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "projection": {"score": {"$meta": "textScore"}},
        },
    )
    assertFailureCode(
        result,
        QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="textScore projection requires a $text query in the filter.",
    )


def test_text_score_sort_without_text_query_errors(collection):
    """Sorting by textScore without a $text query fails with the metadata-not-available code."""
    _create_text_index(collection)
    collection.insert_one({"_id": 1, "content": "coffee"})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {},
            "sort": {"score": {"$meta": "textScore"}},
            "projection": {"score": {"$meta": "textScore"}},
        },
    )
    assertFailureCode(
        result,
        QUERY_METADATA_NOT_AVAILABLE_ERROR,
        msg="textScore sort requires a $text query in the filter.",
    )
