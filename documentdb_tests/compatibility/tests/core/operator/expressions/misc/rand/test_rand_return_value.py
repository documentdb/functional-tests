"""
Tests for $rand return value properties.

Validates return type (double), range [0, 1), per-document independence,
statistical distribution, and precision.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.expressions.utils.utils import (
    assert_expression_result,
    execute_expression,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.test_constants import DOUBLE_ZERO


def test_rand_basic(collection):
    """Test {$rand: {}} is >= 0.0 and < 1.0."""
    result = execute_expression(collection, {"$rand": {}})
    assert_expression_result(
        result, expected=pytest.approx(0.5, abs=0.5), msg="Should return value in [0, 1)"
    )


def test_rand_return_type(collection):
    """Test {$type: {$rand: {}}} returns 'double'."""
    result = execute_expression(collection, {"$type": {"$rand": {}}})
    assert_expression_result(result, expected="double", msg="Should return double type")


def test_rand_two_calls_differ(collection):
    """Test two $rand calls in same $project produce different values (high probability)."""
    result = execute_expression(collection, {"$ne": [{"$rand": {}}, {"$rand": {}}]})
    assert_expression_result(
        result, expected=True, msg="Should produce different values per invocation"
    )


def test_rand_per_document_independence(collection):
    """Test $rand produces unique values across 100 documents."""
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


def test_rand_statistical_average(collection):
    """Test $rand average over 10000 docs is near 0.5 (within 10 std devs)."""
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


def test_rand_range_validation_1000(collection):
    """Test all 1000 $rand values are in [0, 1)."""
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


def test_rand_uniform_distribution(collection):
    """Test $rand follows uniform distribution by checking 10 equal buckets."""
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
