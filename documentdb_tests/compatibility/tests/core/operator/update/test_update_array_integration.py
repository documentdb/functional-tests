"""Integration tests for array update operators with query operators.

Tests that verify interactions between array update operators and various
query operators, ensuring correct element matching and update behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

POSITIONAL_INTEGRATION_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "gt_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$gt": 10}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [5, 99, 25]},
        msg="$ with $gt should match first element > value",
    ),
    UpdateTestCase(
        "lt_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$lt": 20}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 15, 25]},
        msg="$ with $lt should match first element < value",
    ),
    UpdateTestCase(
        "gte_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$gte": 15}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [5, 99, 25]},
        msg="$ with $gte should match first element >= value",
    ),
    UpdateTestCase(
        "lte_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$lte": 15}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [99, 15, 25]},
        msg="$ with $lte should match first element <= value",
    ),
    UpdateTestCase(
        "in_condition",
        setup_docs=[{"_id": 1, "arr": [5, 15, 25]}],
        query={"_id": 1, "arr": {"$in": [15, 25]}},
        update={"$set": {"arr.$": 99}},
        expected={"_id": 1, "arr": [5, 99, 25]},
        msg="$ with $in should match first element in list",
    ),
    UpdateTestCase(
        "elemMatch_comparison_operators",
        setup_docs=[{"_id": 1, "arr": [{"v": 5}, {"v": 15}, {"v": 25}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"v": {"$gt": 10, "$lt": 20}}}},
        update={"$set": {"arr.$.v": 99}},
        expected={"_id": 1, "arr": [{"v": 5}, {"v": 99}, {"v": 25}]},
        msg="$ with $elemMatch containing comparison operators should match correct position",
    ),
    UpdateTestCase(
        "elemMatch_with_regex",
        setup_docs=[{"_id": 1, "arr": [{"s": "abc"}, {"s": "xyz"}, {"s": "def"}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"s": {"$regex": "^x"}}}},
        update={"$set": {"arr.$.s": "matched"}},
        expected={"_id": 1, "arr": [{"s": "abc"}, {"s": "matched"}, {"s": "def"}]},
        msg="$ with $elemMatch containing $regex should match correct position",
    ),
    UpdateTestCase(
        "negation_inside_elemMatch",
        setup_docs=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        query={"_id": 1, "arr": {"$elemMatch": {"x": {"$ne": 1}}}},
        update={"$set": {"arr.$.x": 99}},
        expected={"_id": 1, "arr": [{"x": 1}, {"x": 99}, {"x": 3}]},
        msg="$ with negation inside $elemMatch should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POSITIONAL_INTEGRATION_TESTS))
def test_positional_query_operators(collection, test: UpdateTestCase):
    """Test $ positional with various query operators."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection, {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]}
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
