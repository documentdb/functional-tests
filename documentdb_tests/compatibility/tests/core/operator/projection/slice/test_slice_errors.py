"""Tests for $slice projection operator: error cases.

Tests invalid argument types, invalid array forms, skip/return errors, restrictions,
and context restrictions (aggregate, views).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import (
    EXPRESSION_ARITY_ERROR,
    PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
    PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
    PROJECTION_INVALID_OBJECT_VALUE_ERROR,
    SLICE_INVALID_ARGUMENT_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SLICE_INVALID_TYPE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "array_one_element",
        projection={"arr": {"$slice": [1]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice with single-element array should error",
    ),
    ProjectionTestCase(
        "empty_array_arg",
        projection={"arr": {"$slice": []}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice with empty array should error",
    ),
    ProjectionTestCase(
        "array_three_elements",
        projection={"arr": {"$slice": [1, 2, 3]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice with three-element array should error",
    ),
    ProjectionTestCase(
        "skip_return_negative_limit",
        projection={"arr": {"$slice": [0, -1]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice: [skip, return] with negative return should error",
    ),
    ProjectionTestCase(
        "skip_return_skip_non_numeric",
        projection={"arr": {"$slice": ["a", 1]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice: [skip, return] with non-numeric skip should error",
    ),
    ProjectionTestCase(
        "skip_return_return_non_numeric",
        projection={"arr": {"$slice": [0, "b"]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice: [skip, return] with non-numeric return should error",
    ),
]

SLICE_SKIP_RETURN_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "skip_0_limit_0_error",
        projection={"arr": {"$slice": [0, 0]}},
        doc=[{"_id": 1, "arr": ["a", "b", "c", "d"]}],
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice: [0, 0] should error — limit 0 is invalid in projection context",
    ),
    ProjectionTestCase(
        "fractional_limit_truncates_to_zero_error",
        projection={"arr": {"$slice": [0, 0.5]}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=SLICE_INVALID_ARGUMENT_ERROR,
        msg="$slice: [0, 0.5] should error — fractional limit truncates to 0 which is invalid",
    ),
]

SLICE_RESTRICTION_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "path_collision_slice_and_embedded",
        projection={"instock": {"$slice": 1}, "instock.warehouse": 1},
        doc=[{"_id": 1, "instock": [{"warehouse": "A", "qty": 5}, {"warehouse": "B", "qty": 10}]}],
        error_code=PROJECT_PATH_COLLISION_CHILD_AFTER_PARENT_ERROR,
        msg="$slice on array and projection of embedded field in same array should error",
    ),
    ProjectionTestCase(
        "path_collision_slice_and_positional_same_field",
        projection={"arr": {"$slice": 1}, "arr.$": 1},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=PROJECT_PATH_COLLISION_PARENT_AFTER_CHILD_ERROR,
        msg="$slice and $ positional on same field should error with path collision",
    ),
]

ALL_ERROR_TESTS = (
    SLICE_INVALID_TYPE_TESTS + SLICE_SKIP_RETURN_ERROR_TESTS + SLICE_RESTRICTION_ERROR_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_ERROR_TESTS))
def test_slice_errors(collection, test: ProjectionTestCase):
    """Test $slice projection error cases."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "projection": test.projection},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


AGGREGATE_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "aggregate_project_slice_syntax_error",
        projection={"arr": {"$slice": 2}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice projection syntax in aggregate $project should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATE_ERROR_TESTS))
def test_slice_aggregate_error(collection, test: ProjectionTestCase):
    """Test $slice projection syntax in aggregate $project — expect error."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$project": test.projection}],
            "cursor": {},
        },
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


VIEW_ERROR_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "view_restriction",
        projection={"arr": {"$slice": 1}},
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        error_code=EXPRESSION_ARITY_ERROR,
        msg="$slice projection on a view should error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VIEW_ERROR_TESTS))
def test_slice_view_restriction(collection, database_client, test: ProjectionTestCase):
    """Test $slice projection on a view errors."""
    db = database_client
    src_name = collection.name
    view_name = f"{src_name}_view"

    collection.insert_many(test.doc)
    db.command({"create": view_name, "viewOn": src_name, "pipeline": [{"$match": {}}]})
    result = execute_command(
        db[view_name],
        {"find": view_name, "projection": test.projection},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]


def test_slice_inside_positional_projection_error(collection):
    """Test $slice nested inside a positional $ projection key errors.

    Distinct from sibling path collision ({"arr": {"$slice": 1}, "arr.$": 1}):
    here $slice is the value of the positional key, which the docs call invalid.
    """
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"arr": 2}, "projection": {"arr.$": {"$slice": 1}}},
    )
    assertFailureCode(
        result,
        PROJECTION_INVALID_OBJECT_VALUE_ERROR,
        msg="$slice inside a positional $ projection should error",
    )
