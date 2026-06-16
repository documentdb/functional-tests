"""
Integration tests for conflicting update operators.

Tests that combining update operators on the same field or overlapping paths
produces ConflictingUpdateOperators errors (code 40).
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertFailureCode
from documentdb_tests.framework.error_codes import CONFLICTING_UPDATE_OPERATORS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

MUL_CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "mul_and_set_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$mul": {"val": 2}, "$set": {"val": 5}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$mul and $set on same field should produce conflict error",
    ),
    UpdateTestCase(
        "mul_and_inc_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$mul": {"val": 2}, "$inc": {"val": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$mul and $inc on same field should produce conflict error",
    ),
    UpdateTestCase(
        "mul_and_set_path_prefix",
        setup_docs=[{"_id": 1, "x": {"y": 5}}],
        query={"_id": 1},
        update={"$mul": {"x.y": 2}, "$set": {"x": {}}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$mul on x.y with $set on x should produce path conflict error",
    ),
    UpdateTestCase(
        "mul_and_unset_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$mul": {"val": 2}, "$unset": {"val": ""}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$mul and $unset on same field should produce conflict error",
    ),
    UpdateTestCase(
        "mul_and_rename_same_field",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$mul": {"val": 2}, "$rename": {"val": "other"}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$mul and $rename on same field should produce conflict error",
    ),
]

ALL_CONFLICT_TESTS = MUL_CONFLICT_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_CONFLICT_TESTS))
def test_update_conflict(collection, test: UpdateTestCase):
    """Test that conflicting update operators produce error code 40."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)  # type: ignore[arg-type]
