"""
Update method and upsert tests for $max update field operator.

Tests $max update result metadata and upsert behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "update_one_no_match",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 999},
        update={"$max": {"val": 20}},
        expected={"n": 0, "nModified": 0},
        msg="updateOne $max where no match: n=0, nModified=0",
    ),
    UpdateTestCase(
        "update_many_partial_update",
        setup_docs=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 50},
            {"_id": 3, "val": 30},
        ],
        query={},
        update={"$max": {"val": 25}},
        multi=True,
        expected={"n": 3, "nModified": 1},
        msg="updateMany $max should modify 1 of 3 docs (only val=10 < 25)",
    ),
]

UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_creates_doc_no_match",
        setup_docs=None,
        query={"_id": 1},
        update={"$max": {"val": 100}},
        upsert=True,
        expected={"_id": 1, "val": 100},
        msg="$max with upsert:true and no match should create doc",
    ),
    UpdateTestCase(
        "upsert_match_greater_updates",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 1},
        update={"$max": {"val": 50}},
        upsert=True,
        expected={"_id": 1, "val": 50},
        msg="$max with upsert:true and match, value greater should update",
    ),
    UpdateTestCase(
        "upsert_match_less_unchanged",
        setup_docs=[{"_id": 1, "val": 100}],
        query={"_id": 1},
        update={"$max": {"val": 5}},
        upsert=True,
        expected={"_id": 1, "val": 100},
        msg="$max with upsert:true, match exists, value less should not update",
    ),
    UpdateTestCase(
        "upsert_with_filter_equality",
        setup_docs=None,
        query={"_id": 1, "category": "A"},
        update={"$max": {"score": 80}},
        upsert=True,
        expected={"_id": 1, "category": "A", "score": 80},
        msg="$max upsert with filter equality should create doc with filter fields",
    ),
    UpdateTestCase(
        "upsert_combined_with_set_on_insert",
        setup_docs=None,
        query={"_id": 1},
        update={"$max": {"score": 50}, "$setOnInsert": {"created": True}},
        upsert=True,
        expected={"_id": 1, "created": True, "score": 50},
        msg="$max with $setOnInsert on upsert insert should apply both",
    ),
    UpdateTestCase(
        "upsert_combined_with_set_on_insert_existing",
        setup_docs=[{"_id": 1, "score": 10}],
        query={"_id": 1},
        update={"$max": {"score": 50}, "$setOnInsert": {"created": True}},
        upsert=True,
        expected={"_id": 1, "score": 50},
        msg="$max with $setOnInsert on existing doc should only apply $max",
    ),
    UpdateTestCase(
        "upsert_with_multiple_operators",
        setup_docs=None,
        query={"_id": 1},
        update={"$max": {"high": 100}, "$min": {"low": 5}, "$set": {"name": "test"}},
        upsert=True,
        expected={"_id": 1, "high": 100, "low": 5, "name": "test"},
        msg="$max combined with other operators via upsert should apply all",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESULT_TESTS))
def test_max_update_result(collection, test: UpdateTestCase):
    """Test $max update result metadata (n, nModified)."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True

    result = execute_command(collection, {"update": collection.name, "updates": [update_doc]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(UPSERT_TESTS))
def test_max_upsert(collection, test: UpdateTestCase):
    """Test $max with upsert produces expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.upsert:
        update_doc["upsert"] = True

    execute_command(collection, {"update": collection.name, "updates": [update_doc]})

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
