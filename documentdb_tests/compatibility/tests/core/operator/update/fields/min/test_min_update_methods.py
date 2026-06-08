"""
Update method and upsert tests for $min update field operator.

Tests $min update result metadata and upsert behavior.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Result Metadata]: $min comparison logic determines n and nModified in result.
RESULT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "update_one_no_match",
        setup_docs=[{"_id": 1, "val": 10}],
        query={"_id": 999},
        update={"$min": {"val": 5}},
        expected={"n": 0, "nModified": 0},
        msg="$min should report n=0, nModified=0 when no match",
    ),
    UpdateTestCase(
        "idempotent_equal_no_modification",
        setup_docs=[{"_id": 1, "val": 50}],
        query={"_id": 1},
        update={"$min": {"val": 50}},
        expected={"n": 1, "nModified": 0},
        msg="$min should report nModified=0 when specified equals current",
    ),
    UpdateTestCase(
        "update_many_partial_update",
        setup_docs=[
            {"_id": 1, "val": 10},
            {"_id": 2, "val": 50},
            {"_id": 3, "val": 30},
        ],
        query={},
        update={"$min": {"val": 25}},
        multi=True,
        expected={"n": 3, "nModified": 2},
        msg="$min should modify 2 of 3 docs (val=50 and val=30 > 25)",
    ),
]

# Property [Upsert Behavior]: $min with upsert creates fields on insert and compares on match.
UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_creates_doc_no_match",
        setup_docs=None,
        query={"_id": 1},
        update={"$min": {"val": 100}},
        upsert=True,
        expected={"_id": 1, "val": 100},
        msg="$min with upsert:true and no match should create doc",
    ),
    UpdateTestCase(
        "upsert_match_less_updates",
        setup_docs=[{"_id": 1, "val": 100}],
        query={"_id": 1},
        update={"$min": {"val": 50}},
        upsert=True,
        expected={"_id": 1, "val": 50},
        msg="$min with upsert:true and match, value less should update",
    ),
    UpdateTestCase(
        "upsert_match_greater_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$min": {"val": 100}},
        upsert=True,
        expected={"_id": 1, "val": 5},
        msg="$min with upsert:true, match exists, value greater should not update",
    ),
    UpdateTestCase(
        "upsert_with_filter_equality",
        setup_docs=None,
        query={"_id": 1, "category": "A"},
        update={"$min": {"score": 80}},
        upsert=True,
        expected={"_id": 1, "category": "A", "score": 80},
        msg="$min with upsert and no match should create doc with filter fields",
    ),
    UpdateTestCase(
        "upsert_combined_with_set_on_insert",
        setup_docs=None,
        query={"_id": 1},
        update={"$min": {"score": 50}, "$setOnInsert": {"created": True}},
        upsert=True,
        expected={"_id": 1, "created": True, "score": 50},
        msg="$min with $setOnInsert on upsert insert should apply both",
    ),
    UpdateTestCase(
        "upsert_combined_with_set_on_insert_existing",
        setup_docs=[{"_id": 1, "score": 100}],
        query={"_id": 1},
        update={"$min": {"score": 50}, "$setOnInsert": {"created": True}},
        upsert=True,
        expected={"_id": 1, "score": 50},
        msg="$min with $setOnInsert on existing doc should only apply $min",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RESULT_TESTS))
def test_min_update_result(collection, test: UpdateTestCase):
    """Test $min update result metadata (n, nModified)."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True

    result = execute_command(collection, {"update": collection.name, "updates": [update_doc]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(UPSERT_TESTS))
def test_min_upsert(collection, test: UpdateTestCase):
    """Test $min with upsert produces expected document."""
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
