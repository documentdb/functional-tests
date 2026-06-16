"""
Error case tests for the $pop update array operator.

Consolidates $pop error scenarios that are not BSON-type based: argument values
other than 1 or -1, non-traversable paths, and conflicting update operators on
the same field. Argument-type and target-type validation live in
test_pop_data_types.py.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    CONFLICTING_UPDATE_OPERATORS_ERROR,
    FAILED_TO_PARSE_ERROR,
    PATH_NOT_VIABLE_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Invalid Argument Value]: $pop rejects any numeric value other than 1 or -1.
INVALID_VALUE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "value_zero",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 0}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with 0 should fail to parse",
    ),
    UpdateTestCase(
        "value_positive_other_than_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 10}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with a positive value other than 1 should fail to parse",
    ),
    UpdateTestCase(
        "value_negative_other_than_neg_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": -10}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with a negative value other than -1 should fail to parse",
    ),
    UpdateTestCase(
        "value_whole_double_other_than_one",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 2.0}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with a whole-number double other than 1.0 should fail to parse",
    ),
    UpdateTestCase(
        "value_positive_fraction",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 0.5}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with a fractional value should fail to parse",
    ),
    UpdateTestCase(
        "value_negative_fraction",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": -0.5}},
        error_code=FAILED_TO_PARSE_ERROR,
        msg="$pop with a negative fractional value should fail to parse",
    ),
]

# Property [Non-Traversable Path]: $pop rejects a path whose intermediate cannot be traversed.
PATH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "intermediate_is_scalar",
        setup_docs=[{"_id": 1, "a": "string_value"}],
        query={"_id": 1},
        update={"$pop": {"a.b": 1}},
        error_code=PATH_NOT_VIABLE_ERROR,
        msg="$pop on a path whose intermediate is a scalar should fail as not viable",
    ),
    UpdateTestCase(
        "intermediate_is_array_of_objects",
        setup_docs=[{"_id": 1, "a": [{"b": [1, 2]}, {"b": [3, 4]}]}],
        query={"_id": 1},
        update={"$pop": {"a.b": 1}},
        error_code=PATH_NOT_VIABLE_ERROR,
        msg="$pop on a dotted path through an array of objects should fail as not viable",
    ),
]

# Property [Conflicting Operators]: $pop conflicts with other update operators on the same field.
CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "conflict_with_push",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}, "$push": {"arr": 4}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$pop and $push on the same field should produce a conflict error",
    ),
    UpdateTestCase(
        "conflict_with_add_to_set",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}, "$addToSet": {"arr": 4}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$pop and $addToSet on the same field should produce a conflict error",
    ),
    UpdateTestCase(
        "conflict_with_set",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$pop": {"arr": 1}, "$set": {"arr": [9]}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$pop and $set on the same field should produce a conflict error",
    ),
]

ALL_TESTS = INVALID_VALUE_TESTS + PATH_TESTS + CONFLICT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_pop_error_cases(collection, test: UpdateTestCase):
    """Test $pop error cases produce the expected error codes."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)
