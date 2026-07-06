"""
Update method and upsert tests for $inc update field operator.

Tests $inc update result metadata and upsert behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Result Metadata]: $inc result metadata reflects match and modification counts.
RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "no_match",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 999},
        update={"$inc": {"val": 5}},
        expected={"n": 0, "nModified": 0},
        msg="$inc should report n=0, nModified=0 when no document matches",
    ),
    UpdateTestCase(
        "zero_increment_noop",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$inc": {"val": 0}},
        expected={"n": 1, "nModified": 0},
        msg="$inc should report nModified=0 when increment is zero",
    ),
    UpdateTestCase(
        "update_many_all_modified",
        setup_docs=[
            {"_id": 1, "count": 10},
            {"_id": 2, "count": 20},
            {"_id": 3, "count": 30},
        ],
        query={},
        update={"$inc": {"count": 1}},
        multi=True,
        expected={"n": 3, "nModified": 3},
        msg="$inc should modify all matching documents with multi:true",
    ),
]

# Property [Upsert Behavior]: $inc with upsert creates doc with field set to increment value.
UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_no_match_creates",
        setup_docs=None,
        query={"_id": 1},
        update={"$inc": {"count": 5}},
        upsert=True,
        expected={"_id": 1, "count": 5},
        msg="$inc should create doc with field=increment when upsert has no match",
    ),
    UpdateTestCase(
        "upsert_with_filter_equality",
        setup_docs=None,
        query={"_id": 1, "x": 10},
        update={"$inc": {"x": 5}},
        upsert=True,
        expected={"_id": 1, "x": 15},
        msg="$inc should add increment to filter equality value on upsert",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESULT_TESTS))
def test_inc_update_result(collection, test: UpdateTestCase):
    """Test $inc update result metadata (n, nModified)."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True

    result = execute_command(collection, {"update": collection.name, "updates": [update_doc]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(UPSERT_TESTS))
def test_inc_upsert(collection, test: UpdateTestCase):
    """Test $inc with upsert produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update, "upsert": True}
    execute_command(collection, {"update": collection.name, "updates": [update_doc]})

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
