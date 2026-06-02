"""
Error case tests for positional ($) projection operator.

Tests argument handling, placement restrictions, combination restrictions, error codes,
context restrictions, and edge case errors.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    FIELD_PATH_DOLLAR_PREFIX_ERROR,
    POSITIONAL_ARRAY_CONDITION_ERROR,
    POSITIONAL_IN_AGGREGATE_ERROR,
    POSITIONAL_INDEX_OUT_OF_BOUNDS_ERROR,
    POSITIONAL_MIDDLE_OF_PATH_ERROR,
    POSITIONAL_MULTIPLE_ERROR,
    PROJECT_ELEMATCH_CONFLICT_ERROR,
    PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
    PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
    QUERY_FEATURE_NOT_ALLOWED,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

PLACEMENT_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "middle_of_path",
        doc=[{"_id": 1, "grades": [{"score": 80}, {"score": 90}]}],
        filter={"grades.score": {"$gte": 85}},
        projection={"grades.$.score": 1},
        error_code=POSITIONAL_MIDDLE_OF_PATH_ERROR,
        msg="$ in middle of path errors",
    ),
    ProjectionTestCase(
        "multiple_positional",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": [4, 5, 6]}],
        filter={"a": 1, "b": 4},
        projection={"a.$": 1, "b.$": 1},
        error_code=POSITIONAL_MULTIPLE_ERROR,
        msg="Multiple $ projections errors",
    ),
    ProjectionTestCase(
        "with_slice_same_field",
        doc=[{"_id": 1, "grades": [80, 85, 90]}],
        filter={"grades": {"$gte": 85}},
        projection={"grades.$": 1, "grades": {"$slice": 1}},
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$ combined with $slice on same field errors",
    ),
    ProjectionTestCase(
        "with_exclusion",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": "x"}],
        filter={"a": 1},
        projection={"a.$": 1, "b": 0},
        error_code=PROJECT_EXCLUSION_IN_INCLUSION_ERROR,
        msg="$ with exclusion projection errors",
    ),
    ProjectionTestCase(
        "with_elemMatch_same_field",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}, {"x": 3}]}],
        filter={"arr.x": 1},
        projection={"arr.$": 1, "arr": {"$elemMatch": {"x": 2}}},
        error_code=PROJECT_ELEMATCH_CONFLICT_ERROR,
        msg="$ with $elemMatch on same field errors",
    ),
    ProjectionTestCase(
        "conflicting_embedded",
        doc=[{"_id": 1, "arr": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}],
        filter={"arr.x": 1},
        projection={"arr.$": 1, "arr.y": 1},
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$ conflicting with embedded field projection errors",
    ),
    ProjectionTestCase(
        "bare_dollar_path",
        doc=[{"_id": 1, "arr": [10, 20, 30]}],
        filter={"arr": 20},
        projection={"$": 1},
        error_code=FIELD_PATH_DOLLAR_PREFIX_ERROR,
        msg="Bare '$' as projection path errors",
    ),
    ProjectionTestCase(
        "parallel_array_index_out_of_bounds",
        doc=[{"_id": 1, "a": [1, 2, 3, 4, 5], "b": [10, 20]}],
        filter={"a": 5},
        projection={"b.$": 1},
        error_code=POSITIONAL_INDEX_OUT_OF_BOUNDS_ERROR,
        msg="Parallel array smaller than match index errors",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PLACEMENT_TESTS))
def test_positional_placement_errors(collection, test):
    """Test $ projection placement and combination restrictions."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertFailureCode(result, test.error_code)


MISSING_CONDITION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "no_array_condition",
        doc=[{"_id": 1, "grades": [80, 85, 90]}],
        filter={"_id": 1},
        projection={"grades.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="No matching query condition on array errors",
    ),
    ProjectionTestCase(
        "array_equality",
        doc=[{"_id": 1, "grades": [80, 85, 90]}],
        filter={"grades": [80, 85, 90]},
        projection={"grades.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="Array equality match errors",
    ),
    ProjectionTestCase(
        "or_different_fields",
        doc=[{"_id": 1, "a": [1, 2, 3], "b": 10}],
        filter={"$or": [{"a": 1}, {"b": 10}]},
        projection={"a.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="$or on different fields errors",
    ),
    ProjectionTestCase(
        "nor",
        doc=[{"_id": 1, "grades": [80, 85, 90]}],
        filter={"$nor": [{"grades": 100}]},
        projection={"grades.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="$nor errors",
    ),
    ProjectionTestCase(
        "not",
        doc=[{"_id": 1, "grades": [80, 85, 90]}],
        filter={"grades": {"$not": {"$lt": 50}}},
        projection={"grades.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="$not errors",
    ),
    ProjectionTestCase(
        "non_array_query",
        doc=[{"_id": 1, "status": "active", "scores": [10, 20, 30]}],
        filter={"status": "active"},
        projection={"scores.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="Query on non-array field with existing array errors",
    ),
    ProjectionTestCase(
        "empty_array_matched",
        doc=[{"_id": 1, "arr": []}],
        filter={"arr": {"$exists": True}},
        projection={"arr.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="Empty array matched by $exists errors — no element to project",
    ),
    ProjectionTestCase(
        "or_mixed_array_and_non_array",
        doc=[{"_id": 1, "arr": [10, 20, 30], "status": "A"}],
        filter={"$or": [{"arr": 20}, {"status": "A"}]},
        projection={"arr.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="$or with mixed array/non-array branches errors",
    ),
    ProjectionTestCase(
        "array_index_path",
        doc=[{"_id": 1, "arr": [10, 20, 30]}],
        filter={"arr.0": 10},
        projection={"arr.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="Dotted-index path filter does not pin element for $",
    ),
    ProjectionTestCase(
        "size_filter",
        doc=[{"_id": 1, "arr": [10, 20, 30]}],
        filter={"arr": {"$size": 3}},
        projection={"arr.$": 1},
        error_code=POSITIONAL_ARRAY_CONDITION_ERROR,
        msg="$size matches doc but does not target an element",
    ),
    ProjectionTestCase(
        "expr_in_filter",
        doc=[{"_id": 1, "arr": [10, 20, 30]}],
        filter={"arr": {"$gte": 20}, "$expr": {"$gt": [{"$size": "$arr"}, 1]}},
        projection={"arr.$": 1},
        error_code=QUERY_FEATURE_NOT_ALLOWED,
        msg="$expr in filter with $ projection errors",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MISSING_CONDITION_TESTS))
def test_positional_missing_condition_errors(collection, test):
    """Test $ projection without valid array query condition errors."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertFailureCode(result, test.error_code)


def test_positional_in_aggregate_project_errors(collection):
    """Test $ projection in aggregate $project stage errors."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$match": {"arr": {"$gte": 20}}},
                {"$project": {"arr.$": 1}},
            ],
            "cursor": {},
        },
    )
    assertFailureCode(result, POSITIONAL_IN_AGGREGATE_ERROR)


def test_positional_on_view_errors(database_client, collection):
    """Test $ projection on a view errors."""
    collection.insert_one({"_id": 1, "arr": [10, 20, 30]})
    view_name = collection.name + "_view"
    database_client.command(
        {
            "create": view_name,
            "viewOn": collection.name,
            "pipeline": [],
        }
    )
    try:
        result = execute_command(
            collection,
            {
                "find": view_name,
                "filter": {"arr": {"$gte": 20}},
                "projection": {"arr.$": 1},
            },
        )
        assertFailureCode(result, POSITIONAL_IN_AGGREGATE_ERROR)
    finally:
        database_client.drop_collection(view_name)
