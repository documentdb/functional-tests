"""
Tests for $meta "textScore" behavior in aggregation.

Must use $match with $text for textScore to be valid.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


@pytest.fixture
def text_collection(collection):
    collection.create_index([("content", "text")])
    collection.insert_many(
        [
            {"_id": 1, "content": "apple banana cherry"},
            {"_id": 2, "content": "apple apple apple"},
            {"_id": 3, "content": "banana cherry date"},
        ]
    )
    return collection


def test_meta_textscore_single_word(text_collection):
    """Test $meta textScore returns higher score for more term matches."""
    result = execute_command(
        text_collection,
        {
            "aggregate": text_collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "apple"}}},
                {"$project": {"_id": 1, "score": {"$meta": "textScore"}}},
                {"$sort": {"score": 1}},
                {"$project": {"score": 0}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1},
            {"_id": 2},
        ],
    )


def test_meta_textscore_no_matches_returns_empty(text_collection):
    """Test $meta textScore with $text query that matches no documents returns empty result."""
    result = execute_command(
        text_collection,
        {
            "aggregate": text_collection.name,
            "pipeline": [
                {"$match": {"$text": {"$search": "nonexistant"}}},
                {"$project": {"_id": 1, "score": {"$meta": "textScore"}}},
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [])
