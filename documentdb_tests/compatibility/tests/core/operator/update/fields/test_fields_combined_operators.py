"""
Combined operator tests for $max update field operator.

Tests $max used alongside other update operators on different fields.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

CHANGED_DOC_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "combined_with_set",
        setup_docs=[{"_id": 1, "score": 10, "name": "old"}],
        query={"_id": 1},
        update={"$max": {"score": 50}, "$set": {"name": "new"}},
        expected={"_id": 1, "score": 50, "name": "new"},
        msg="$max combined with $set on different fields should both apply",
    ),
    UpdateTestCase(
        "combined_with_inc",
        setup_docs=[{"_id": 1, "score": 10, "count": 5}],
        query={"_id": 1},
        update={"$max": {"score": 50}, "$inc": {"count": 1}},
        expected={"_id": 1, "score": 50, "count": 6},
        msg="$max combined with $inc on different fields should both apply",
    ),
    UpdateTestCase(
        "combined_with_min",
        setup_docs=[{"_id": 1, "high": 100, "low": 5}],
        query={"_id": 1},
        update={"$max": {"high": 200}, "$min": {"low": 3}},
        expected={"_id": 1, "high": 200, "low": 3},
        msg="$max combined with $min on different fields should both apply",
    ),
    UpdateTestCase(
        "combined_with_unset",
        setup_docs=[{"_id": 1, "score": 10, "extra": "remove"}],
        query={"_id": 1},
        update={"$max": {"score": 50}, "$unset": {"extra": ""}},
        expected={"_id": 1, "score": 50},
        msg="$max and $unset should both apply",
    ),
    UpdateTestCase(
        "combined_with_mul",
        setup_docs=[{"_id": 1, "score": 10, "factor": 3}],
        query={"_id": 1},
        update={"$max": {"score": 50}, "$mul": {"factor": 2}},
        expected={"_id": 1, "score": 50, "factor": 6},
        msg="$max combined with $mul on different fields should both apply",
    ),
    UpdateTestCase(
        "unicode_field_name",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$max": {"\U0001f389": 42}},
        expected={"_id": 1, "\U0001f389": 42},
        msg="$max with unicode emoji field name should create field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CHANGED_DOC_TESTS))
def test_max_combined_changed_doc(collection, test: UpdateTestCase):
    """Test $max combined with other operators produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


def test_max_combined_with_currentdate(collection):
    """Test $max combined with $currentDate on different fields."""
    collection.insert_one({"_id": 1, "score": 10})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$max": {"score": 50}, "$currentDate": {"lastModified": True}},
                }
            ],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": 1}, "projection": {"score": 1}}
    )
    assertSuccess(
        result, [{"_id": 1, "score": 50}], msg="$max with $currentDate should update score to 50"
    )
