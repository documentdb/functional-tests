"""
Update method and context tests for $currentDate update field operator.

Tests $currentDate in updateMany and upsert contexts.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Exists, IsType

# ---------------------------------------------------------------------------
# Property [Update Contexts]: $currentDate works in updateMany
# ---------------------------------------------------------------------------

UPDATE_CONTEXT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "updateMany_sets_date_on_all",
        setup_docs=[{"_id": 1, "val": "a"}, {"_id": 2, "val": "b"}, {"_id": 3, "val": "c"}],
        query={},
        update={"$currentDate": {"modified": True}},
        multi=True,
        expected={"modified": IsType("date")},
        msg="$currentDate in updateMany should set Date on all matched docs",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPDATE_CONTEXT_TESTS))
def test_currentDate_update_contexts(collection, test: UpdateTestCase):
    """Test $currentDate in updateMany sets the expected type on matched docs."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True
    if test.upsert:
        update_doc["upsert"] = True

    execute_command(collection, {"update": collection.name, "updates": [update_doc]})

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)


# ---------------------------------------------------------------------------
# Property [Upsert]: $currentDate with upsert creates field on new document
# ---------------------------------------------------------------------------

UPSERT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "upsert_creates_doc_with_date",
        query={"_id": 1},
        update={"$currentDate": {"created": True}},
        upsert=True,
        expected={"created": IsType("date")},
        msg="Upserted doc should have Date field",
    ),
    UpdateTestCase(
        "upsert_creates_doc_with_timestamp",
        query={"_id": 1},
        update={"$currentDate": {"ts": {"$type": "timestamp"}}},
        upsert=True,
        expected={"ts": IsType("timestamp")},
        msg="Upserted doc should have Timestamp field",
    ),
    UpdateTestCase(
        "upsert_includes_filter_fields",
        query={"_id": 1, "category": "A"},
        update={"$currentDate": {"ts": True}},
        upsert=True,
        expected={"category": Exists(), "ts": IsType("date")},
        msg="Upserted doc should include filter fields and Date field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPSERT_TESTS))
def test_currentDate_upsert(collection, test: UpdateTestCase):
    """Test $currentDate with upsert produces the expected document."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    update_doc = {"q": test.query, "u": test.update}
    if test.multi:
        update_doc["multi"] = True
    if test.upsert:
        update_doc["upsert"] = True

    execute_command(collection, {"update": collection.name, "updates": [update_doc]})

    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertProperties(result, test.expected, msg=test.msg)
