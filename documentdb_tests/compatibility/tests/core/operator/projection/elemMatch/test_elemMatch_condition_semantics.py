"""
Tests condition document semantics for the $elemMatch projection operator.
"""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Scalar Array Matching]: a field-name condition matches sub-document
# fields within array elements but does not match scalar values; top-level
# operators ($eq, $gt, $in, etc.) must be used to match scalars in an array.
ELEMMATCH_SCALAR_ARRAY_MATCHING_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "scalar_field_name_does_not_match_scalars",
        doc=[{"_id": 1, "tags": ["basketball", "soccer", "tennis"]}],
        projection={"tags": {"$elemMatch": {"sport": "basketball"}}},
        expected=[{"_id": 1}],
        msg="$elemMatch field-name condition should not match scalar values in the array",
    ),
    ProjectionTestCase(
        "scalar_field_name_matches_subdoc_field",
        doc=[
            {
                "_id": 1,
                "items": [{"sport": "basketball"}, {"sport": "soccer"}],
            }
        ],
        projection={"items": {"$elemMatch": {"sport": "basketball"}}},
        expected=[{"_id": 1, "items": [{"sport": "basketball"}]}],
        msg="$elemMatch field-name condition should match sub-document fields",
    ),
    ProjectionTestCase(
        "scalar_eq_matches_scalar_string",
        doc=[{"_id": 1, "tags": ["basketball", "soccer", "tennis"]}],
        projection={"tags": {"$elemMatch": {"$eq": "basketball"}}},
        expected=[{"_id": 1, "tags": ["basketball"]}],
        msg="$elemMatch $eq should match scalar string values in an array",
    ),
    ProjectionTestCase(
        "scalar_gt_matches_scalar_string",
        doc=[{"_id": 1, "tags": ["basketball", "soccer", "tennis"]}],
        projection={"tags": {"$elemMatch": {"$gt": "soccer"}}},
        expected=[{"_id": 1, "tags": ["tennis"]}],
        msg="$elemMatch $gt should match scalar string values in an array",
    ),
    ProjectionTestCase(
        "scalar_in_matches_scalar",
        doc=[{"_id": 1, "tags": ["basketball", "soccer", "tennis"]}],
        projection={"tags": {"$elemMatch": {"$in": ["tennis", "golf"]}}},
        expected=[{"_id": 1, "tags": ["tennis"]}],
        msg="$elemMatch $in should match scalar values in an array",
    ),
    ProjectionTestCase(
        "scalar_field_name_no_match_in_mixed_array",
        doc=[{"_id": 1, "mixed": [1, "hello", {"name": "x"}, True]}],
        projection={"mixed": {"$elemMatch": {"name": "hello"}}},
        expected=[{"_id": 1}],
        msg="$elemMatch field-name condition should not match scalars in a mixed array",
    ),
    ProjectionTestCase(
        "scalar_field_name_matches_doc_in_mixed_array",
        doc=[{"_id": 1, "mixed": [1, "hello", {"name": "x"}, True]}],
        projection={"mixed": {"$elemMatch": {"name": "x"}}},
        expected=[{"_id": 1, "mixed": [{"name": "x"}]}],
        msg="$elemMatch field-name condition should match document elements in a mixed array",
    ),
    ProjectionTestCase(
        "scalar_eq_matches_scalar_in_mixed_array",
        doc=[{"_id": 1, "mixed": [1, "hello", {"name": "x"}, True]}],
        projection={"mixed": {"$elemMatch": {"$eq": "hello"}}},
        expected=[{"_id": 1, "mixed": ["hello"]}],
        msg="$elemMatch $eq should match scalar values in a mixed array",
    ),
]

# Property [Empty Condition]: an empty condition {} matches elements that are objects
# or arrays but does not match scalar elements.
ELEMMATCH_EMPTY_CONDITION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "empty_cond_matches_first_object",
        doc=[{"_id": 1, "arr": [{"x": 1}, {"y": 2}]}],
        projection={"arr": {"$elemMatch": {}}},
        expected=[{"_id": 1, "arr": [{"x": 1}]}],
        msg="$elemMatch with empty condition should match the first object element",
    ),
    ProjectionTestCase(
        "empty_cond_matches_nested_array",
        doc=[{"_id": 1, "arr": [[1], [2, 3]]}],
        projection={"arr": {"$elemMatch": {}}},
        expected=[{"_id": 1, "arr": [[1]]}],
        msg="$elemMatch with empty condition should match array elements",
    ),
    ProjectionTestCase(
        "empty_cond_skips_scalars_matches_object",
        doc=[{"_id": 1, "arr": [42, "hello", True, None, {"x": 1}]}],
        projection={"arr": {"$elemMatch": {}}},
        expected=[{"_id": 1, "arr": [{"x": 1}]}],
        msg="$elemMatch with empty condition should skip scalars and match the first object",
    ),
    ProjectionTestCase(
        "empty_cond_all_scalars_no_match",
        doc=[{"_id": 1, "arr": [1, "two", True, None]}],
        projection={"arr": {"$elemMatch": {}}},
        expected=[{"_id": 1}],
        msg="$elemMatch with empty condition should omit field when all elements are scalars",
    ),
    ProjectionTestCase(
        "empty_cond_skips_scalars_matches_array_element",
        doc=[{"_id": 1, "arr": [42, "hello", [1, 2, 3]]}],
        projection={"arr": {"$elemMatch": {}}},
        expected=[{"_id": 1, "arr": [[1, 2, 3]]}],
        msg="$elemMatch with empty condition should skip scalars and match a nested array",
    ),
]

# Property [Condition Conjunction]: every condition in the condition document must be
# satisfied by the same array element, so multiple top-level operators or multiple field
# conditions are conjoined and the first element satisfying all of them is returned.
ELEMMATCH_CONJUNCTION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "conjunction_multi_op_range_returns_first",
        doc=[{"_id": 1, "arr": [1, 5, 10]}],
        projection={"arr": {"$elemMatch": {"$gte": 2, "$lte": 8}}},
        expected=[{"_id": 1, "arr": [5]}],
        msg="$elemMatch should return the first element satisfying all top-level operators",
    ),
    ProjectionTestCase(
        "conjunction_multi_op_impossible_condition",
        doc=[{"_id": 1, "arr": [1, 4, 9]}],
        projection={"arr": {"$elemMatch": {"$gt": 5, "$lt": 3}}},
        expected=[{"_id": 1}],
        msg="$elemMatch should omit the field when the condition is logically unsatisfiable",
    ),
    ProjectionTestCase(
        "conjunction_multi_op_satisfiable_no_single_element",
        doc=[{"_id": 1, "arr": [3, 10]}],
        projection={"arr": {"$elemMatch": {"$gt": 5, "$lt": 9}}},
        expected=[{"_id": 1}],
        msg="$elemMatch should omit the field when no single element satisfies all operators",
    ),
    ProjectionTestCase(
        "conjunction_multi_op_negation_combo",
        doc=[{"_id": 1, "arr": [5, 4, 10]}],
        projection={"arr": {"$elemMatch": {"$ne": 5, "$gt": 3}}},
        expected=[{"_id": 1, "arr": [4]}],
        msg="$elemMatch should conjoin a negation operator with a comparison operator",
    ),
    ProjectionTestCase(
        "conjunction_multi_field_match",
        doc=[{"_id": 1, "arr": [{"x": 1, "y": 9}, {"x": 1, "y": 2}]}],
        projection={"arr": {"$elemMatch": {"x": 1, "y": 2}}},
        expected=[{"_id": 1, "arr": [{"x": 1, "y": 2}]}],
        msg="$elemMatch should require a single element to satisfy all field conditions",
    ),
    ProjectionTestCase(
        "conjunction_multi_field_no_single_element",
        doc=[{"_id": 1, "arr": [{"x": 1, "y": 9}, {"x": 3, "y": 2}]}],
        projection={"arr": {"$elemMatch": {"x": 1, "y": 2}}},
        expected=[{"_id": 1}],
        msg="$elemMatch should omit the field when no single element satisfies all fields",
    ),
    ProjectionTestCase(
        "conjunction_multi_field_operator_combo",
        doc=[{"_id": 1, "arr": [{"x": 1, "y": "b"}, {"x": 5, "y": "a"}, {"x": 7, "y": "b"}]}],
        projection={"arr": {"$elemMatch": {"x": {"$gte": 5}, "y": "b"}}},
        expected=[{"_id": 1, "arr": [{"x": 7, "y": "b"}]}],
        msg="$elemMatch should conjoin an operator field condition with an equality condition",
    ),
]

CONDITION_SEMANTICS_TESTS = (
    ELEMMATCH_SCALAR_ARRAY_MATCHING_TESTS
    + ELEMMATCH_EMPTY_CONDITION_TESTS
    + ELEMMATCH_CONJUNCTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(CONDITION_SEMANTICS_TESTS))
def test_elemmatch_condition_semantics(collection, test):
    """Test $elemMatch projection condition document cases."""
    collection.insert_many(test.doc)
    cmd = {
        "find": collection.name,
        "projection": test.projection,
    }
    if test.filter is not None:
        cmd["filter"] = test.filter
    result = execute_command(collection, cmd)
    assertResult(result, expected=test.expected, error_code=test.error_code, msg=test.msg)
