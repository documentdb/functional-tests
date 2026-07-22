"""
Compatibility tests for $maxN array expression operator.

Tests edge cases and additional scenarios for $maxN-array-element expression.
"""

import pytest

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


@pytest.mark.aggregate
def test_maxN_array_element_with_greater_n(collection):
    """When n is greater than the array length, $maxN returns all elements, sorted descending."""
    collection.insert_many(
        [{"_id": 1, "values": [10, 30, 20, 40]}, {"_id": 2, "values": [5, 25, 15, 35]}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": 10, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": [40, 30, 20, 10]}, {"_id": 2, "maxVals": [35, 25, 15, 5]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_n_equals_one(collection):
    """When n is 1, $maxN returns a single-element array holding the largest value, not a scalar."""
    collection.insert_many(
        [{"_id": 1, "values": [10, 30, 20, 40]}, {"_id": 2, "values": [5, 25, 15, 35]}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": 1, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": [40]}, {"_id": 2, "maxVals": [35]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_duplicate_values(collection):
    """Duplicate values in the input array are preserved, not deduplicated."""
    collection.insert_many(
        [{"_id": 1, "values": [5, 5, 3, 5]}, {"_id": 2, "values": [10, 4, 10, 3]}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": 3, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": [5, 5, 5]}, {"_id": 2, "maxVals": [10, 10, 4]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_negative_numbers(collection):
    """Negative numbers are ranked correctly, with values closest to zero treated as largest."""
    collection.insert_many(
        [{"_id": 1, "values": [-10, -30, -20, -40]}, {"_id": 2, "values": [-5, -25, -15, -35]}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": [-10, -20]}, {"_id": 2, "maxVals": [-5, -15]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_empty_array(collection):
    """$maxN over an empty array returns an empty array rather than erroring."""
    collection.insert_many([{"_id": 1, "values": []}, {"_id": 2, "values": []}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": []}, {"_id": 2, "maxVals": []}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_null_values(collection):
    """Null values are ignored by $maxN and do not count toward n."""
    collection.insert_many(
        [{"_id": 1, "values": [None, 30, None, 4]}, {"_id": 2, "values": [None, None, 2, None]}]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": 2, "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": [30, 4]}, {"_id": 2, "maxVals": [2]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_n_as_dynamic_reference(collection):
    """n can be a field reference and is evaluated independently for each document."""
    collection.insert_many(
        [
            {"_id": 1, "values": [10, 30, 20, 40], "nval": 2},
            {"_id": 2, "values": [5, 25, 15, 35], "nval": 3},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": {"maxVals": {"$maxN": {"n": "$nval", "input": "$values"}}}}],
            "cursor": {},
        },
    )

    expected = [{"_id": 1, "maxVals": [40, 30]}, {"_id": 2, "maxVals": [35, 25, 15]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")


@pytest.mark.aggregate
def test_maxN_array_element_with_accumulator_context(collection):
    """$maxN works as a $group accumulator, returning the N largest values per group."""
    collection.insert_many(
        [
            {"_id": 1, "category": "A", "score": 10},
            {"_id": 2, "category": "A", "score": 4},
            {"_id": 3, "category": "A", "score": 8},
            {"_id": 4, "category": "A", "score": 1},
            {"_id": 5, "category": "B", "score": 20},
            {"_id": 6, "category": "B", "score": 20},
            {"_id": 7, "category": "B", "score": 4},
        ]
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$group": {"_id": "$category", "topTwo": {"$maxN": {"n": 2, "input": "$score"}}}},
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
    )

    expected = [{"_id": "A", "topTwo": [10, 8]}, {"_id": "B", "topTwo": [20, 20]}]
    assertSuccess(result, expected, msg="Should support $maxN-array-element expression")
