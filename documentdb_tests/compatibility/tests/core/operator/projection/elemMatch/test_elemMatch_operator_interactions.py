"""
Tests interaction with other operators for the $elemMatch projection operator.
"""

from __future__ import annotations

import pytest
from bson import SON

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Operator Interactions - Success]: query $elemMatch and projection
# $elemMatch are fully independent. The query selects which documents are
# returned while the projection independently selects which element is returned.
ELEMMATCH_QUERY_INTERACTION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "interaction_same_field_different_conditions",
        doc=[
            {"_id": 1, "arr": [1, 2, 8]},
            {"_id": 2, "arr": [1, 2, 3]},
            {"_id": 3, "arr": [5, 6, 7]},
        ],
        projection={"arr": {"$elemMatch": {"$gte": 2}}},
        filter={"arr": {"$elemMatch": {"$gte": 5}}},
        expected=[{"_id": 1, "arr": [2]}, {"_id": 3, "arr": [5]}],
        msg="$elemMatch projection should select the first matching element independent of filter",
    ),
    ProjectionTestCase(
        "interaction_subdoc_same_field",
        doc=[
            {"_id": 1, "items": [{"x": 1}, {"x": 5}, {"x": 10}]},
            {"_id": 2, "items": [{"x": 1}, {"x": 2}]},
        ],
        projection={"items": {"$elemMatch": {"x": {"$gte": 2}}}},
        filter={"items": {"$elemMatch": {"x": {"$gte": 10}}}},
        expected=[{"_id": 1, "items": [{"x": 5}]}],
        msg="$elemMatch projection should select the matching sub-document independent of filter",
    ),
    ProjectionTestCase(
        "interaction_different_fields",
        doc=[
            {"_id": 1, "tags": [{"k": "a"}, {"k": "z"}], "scores": [10, 20, 30]},
            {"_id": 2, "tags": [{"k": "a"}, {"k": "b"}], "scores": [40, 50]},
        ],
        projection={"scores": {"$elemMatch": {"$gte": 20}}},
        filter={"tags": {"$elemMatch": {"k": "z"}}},
        expected=[{"_id": 1, "scores": [20]}],
        msg="$elemMatch projection should select elements on a different field than the filter",
    ),
]

# Property [Slice Interaction]: $elemMatch and $slice on different fields are applied
# independently, each transforming its own field.
ELEMMATCH_SLICE_INTERACTION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "slice_different_field",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": [10, 20, 30, 40]}],
        projection=SON([("a", {"$elemMatch": {"$gte": 2}}), ("b", {"$slice": 2})]),
        expected=[{"_id": 1, "a": [2], "b": [10, 20]}],
        msg="$elemMatch and $slice on different fields should each apply to their own field",
    ),
]

OPERATOR_INTERACTIONS_TESTS = ELEMMATCH_QUERY_INTERACTION_TESTS + ELEMMATCH_SLICE_INTERACTION_TESTS


@pytest.mark.parametrize("test", pytest_params(OPERATOR_INTERACTIONS_TESTS))
def test_elemmatch_operator_interactions(collection, test):
    """Test $elemMatch projection operator interaction cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
