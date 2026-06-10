"""
Operator conflict tests for $currentDate update field operator.

Tests $currentDate interactions with other update operators on same/different fields,
and path prefix conflicts.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertProperties, assertResult
from documentdb_tests.framework.error_codes import CONFLICTING_UPDATE_OPERATORS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import IsType

# ---------------------------------------------------------------------------
# Property [Conflicts]: $currentDate + other operators on same field → error
# ---------------------------------------------------------------------------

CONFLICT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "conflict_with_set_same_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True}, "$set": {"x": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate + $set on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_inc_same_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True}, "$inc": {"x": 1}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate + $inc on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_unset_same_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True}, "$unset": {"x": ""}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate + $unset on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_mul_same_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True}, "$mul": {"x": 2}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate + $mul on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_min_same_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True}, "$min": {"x": 0}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate + $min on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_with_max_same_field",
        setup_docs=[{"_id": 1, "x": 1}],
        query={"_id": 1},
        update={"$currentDate": {"x": True}, "$max": {"x": 100}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate + $max on same field should produce conflict error",
    ),
    UpdateTestCase(
        "conflict_path_prefix",
        setup_docs=[{"_id": 1, "x": {"y": 1}}],
        query={"_id": 1},
        update={"$currentDate": {"x.y": True}, "$set": {"x": {}}},
        error_code=CONFLICTING_UPDATE_OPERATORS_ERROR,
        msg="$currentDate on child path + $set on parent path should produce conflict error",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONFLICT_TESTS))
def test_currentDate_conflicts(collection, test: UpdateTestCase):
    """Test $currentDate with conflicting operators on same field produces error."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    result = execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )
    assertResult(result, error_code=test.error_code, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [No Conflict]: $currentDate + other operators on different fields → OK
# ---------------------------------------------------------------------------


def test_currentDate_with_set_different_fields_succeeds(collection):
    """Test $currentDate combined with $set on different fields succeeds."""
    collection.insert_one({"_id": 1, "name": "old"})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$currentDate": {"modified": True}, "$set": {"name": "new"}},
                }
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"modified": IsType("date")},
        msg="$currentDate should produce Date when combined with $set on different field",
    )


def test_currentDate_with_inc_different_fields_succeeds(collection):
    """Test $currentDate combined with $inc on different fields succeeds."""
    collection.insert_one({"_id": 1, "version": 1})

    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {
                        "$currentDate": {"modified": {"$type": "timestamp"}},
                        "$inc": {"version": 1},
                    },
                }
            ],
        },
    )

    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertProperties(
        result,
        {"modified": IsType("timestamp")},
        msg="$currentDate should produce Timestamp when combined with $inc on different field",
    )
