"""
Integration tests for $rand with pipeline stages.

Covers $rand used within $project, $group, and $match stages:
per-document independence, statistical distribution, range validation,
null field handling, and empty collection behavior.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import DOUBLE_ZERO


def test_rand_project_on_null_field_document(collection):
    """Test rand in $project on a document with null fields still returns a double."""
    collection.insert_one({"_id": 1, "a": None})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "result": {"$type": {"$rand": {}}}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"result": "double"}], msg="Should return double on null field doc")


def test_rand_project_on_empty_collection(collection):
    """Test rand in $project on empty collection returns empty result."""
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"_id": 0, "r": {"$rand": {}}}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [], msg="Should return empty result on empty collection")


def test_rand_project_group_per_document_independence(collection):
    """Test $rand produces unique values across 100 documents via $project and $group."""
    collection.insert_many([{"_id": i} for i in range(100)])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "r": {"$rand": {}}}},
                {"$group": {"_id": None, "vals": {"$addToSet": "$r"}}},
                {"$project": {"_id": 0, "uniqueCount": {"$size": "$vals"}}},
            ],
            "cursor": {},
        },
    )
    # With ~17 significant digits (~10^17 possible values), collision probability
    # among 100 values is ~100^2 / (2 * 10^17) = 5e-14
    assertSuccess(result, [{"uniqueCount": 100}], msg="Should produce unique value per document")


def test_rand_project_group_statistical_average(collection):
    """Test $rand average over 10000 docs is near 0.5 via $project and $group."""
    collection.insert_many([{"_id": i} for i in range(10000)])
    # Mean of uniform [0,1) = 0.5, std = 1/sqrt(12) ~ 0.2887
    # std of mean = 0.2887/sqrt(10000) ~ 0.002887
    # ±0.03 = ~10.4 std devs, so average should be in [0.47, 0.53]
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "r": {"$rand": {}}}},
                {"$group": {"_id": None, "avg": {"$avg": "$r"}}},
                {
                    "$project": {
                        "_id": 0,
                        "inRange": {
                            "$and": [
                                {"$gte": ["$avg", 0.47]},
                                {"$lte": ["$avg", 0.53]},
                            ]
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"inRange": True}], msg="Should average near 0.5 over 10000 samples")


def test_rand_project_match_range_validation(collection):
    """Test all 1000 $rand values are in [0, 1) via $project and $match."""
    collection.insert_many([{"_id": i} for i in range(1000)])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "r": {"$rand": {}}}},
                {
                    "$match": {
                        "$expr": {
                            "$or": [
                                {"$lt": ["$r", DOUBLE_ZERO]},
                                {"$gte": ["$r", 1.0]},
                            ]
                        }
                    }
                },
                {"$count": "outOfRange"},
            ],
            "cursor": {},
        },
    )
    # Expect empty result (no out-of-range values)
    assertSuccess(result, [], msg="Should have no out-of-range values")


def test_rand_project_group_uniform_distribution(collection):
    """Test $rand uniform distribution by checking 10 equal buckets via $project and $group."""
    collection.insert_many([{"_id": i} for i in range(100000)])
    # Bucket each value into [0..9] via floor(rand * 10).
    # For uniform [0,1), each bucket expects ~10000 of 100000 samples.
    # Binomial std for each bucket: sqrt(100000 * 0.1 * 0.9) ~ 95.
    # We check each bucket has at least 9000 (~10.5 std devs below expected).
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"_id": 0, "bucket": {"$floor": {"$multiply": [{"$rand": {}}, 10]}}}},
                {"$group": {"_id": "$bucket", "count": {"$sum": 1}}},
                {"$match": {"$expr": {"$lt": ["$count", 9000]}}},
                {"$count": "underfilled"},
            ],
            "cursor": {},
        },
    )
    # Expect empty result (no underfilled buckets)
    assertSuccess(result, [], msg="Should have no underfilled buckets")
