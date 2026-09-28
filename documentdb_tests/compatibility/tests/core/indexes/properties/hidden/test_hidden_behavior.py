"""Tests for hidden index runtime behavior — stats, writes, and TTL."""

import time
from datetime import datetime, timedelta, timezone

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_admin_command, execute_command
from documentdb_tests.framework.parametrize import pytest_params

from .utils.helpers import get_index_doc, get_index_ops

pytestmark = pytest.mark.index


@pytest.fixture
def fast_ttl_monitor(collection):
    """Set ttlMonitorSleepSecs to 1 for the test, restore afterward."""
    original = execute_admin_command(collection, {"getParameter": 1, "ttlMonitorSleepSecs": 1})
    set_result = execute_admin_command(collection, {"setParameter": 1, "ttlMonitorSleepSecs": 1})
    if isinstance(set_result, Exception):
        pytest.skip("engine does not support setParameter ttlMonitorSleepSecs")
    yield
    if isinstance(original, dict) and "ttlMonitorSleepSecs" in original:
        execute_admin_command(
            collection,
            {"setParameter": 1, "ttlMonitorSleepSecs": original["ttlMonitorSleepSecs"]},
        )


INDEXSTATS_COUNTER_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="reset_on_hide",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"pre_use": True, "toggle_sequence": [True]},
        expected=False,
        msg="Hiding an index should reset its $indexStats accesses to zero",
    ),
    IndexTestCase(
        id="unhide_stays_zero",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"pre_use": False, "toggle_sequence": [False]},
        expected=False,
        msg="Unhiding an index alone should not increment its accesses counter",
    ),
    IndexTestCase(
        id="find_after_unhide_increments",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"pre_use": False, "toggle_sequence": [False], "post_use": True},
        expected=True,
        msg="A query after unhide should increment the accesses counter",
    ),
    IndexTestCase(
        id="unhide_resets_counter",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"pre_use": True, "toggle_sequence": [True, False]},
        expected=False,
        msg="Unhiding a hidden index should leave the accesses counter at zero",
    ),
    IndexTestCase(
        id="idempotent_unhide_no_reset",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"pre_use": True, "toggle_sequence": [False]},
        expected=True,
        msg="An idempotent unhide should not reset the accesses counter",
    ),
    IndexTestCase(
        id="multiple_reset_cycle",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"pre_use": True, "toggle_sequence": [True, False, True]},
        expected=False,
        msg="Repeated hide/unhide toggles should each reset the counter to zero",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INDEXSTATS_COUNTER_TESTS))
def test_indexstats_counter(collection, test):
    """Test $indexStats accesses counter behavior on hide/unhide."""
    collection.insert_many([{"a": i} for i in range(10)])
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [test.indexes[0]]},
    )
    if test.input.get("pre_use"):
        execute_command(
            collection, {"find": collection.name, "filter": {"a": {"$gte": 0}}, "hint": "a_1"}
        )
    for hidden_value in test.input["toggle_sequence"]:
        execute_command(
            collection,
            {"collMod": collection.name, "index": {"name": "a_1", "hidden": hidden_value}},
        )
    if test.input.get("post_use"):
        execute_command(
            collection, {"find": collection.name, "filter": {"a": {"$gte": 0}}, "hint": "a_1"}
        )
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$indexStats": {}}], "cursor": {}}
    )
    assertSuccess(
        result,
        test.expected,
        raw_res=True,
        transform=lambda r: next(
            (
                doc["accesses"]["ops"] > 0
                for doc in r["cursor"]["firstBatch"]
                if doc.get("name") == "a_1"
            ),
            None,
        ),
        msg=test.msg,
    )


WRITE_BEHAVIOR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="insert_maintained",
        input={"insert_docs": [{"a": i} for i in range(20)], "query_filter": {"a": 5}},
        expected=[5],
        msg="Inserts while hidden should be reflected in the index (found via hint)",
    ),
    IndexTestCase(
        id="update_adds_new_entry",
        input={
            "insert_docs": [{"_id": 1, "a": 1}],
            "update": {"q": {"a": 1}, "u": {"$set": {"a": 2}}},
            "query_filter": {"a": 2},
        },
        expected=[2],
        msg="Update while hidden should create the new index entry",
    ),
    IndexTestCase(
        id="update_removes_old_entry",
        input={
            "insert_docs": [{"_id": 1, "a": 1}],
            "update": {"q": {"a": 1}, "u": {"$set": {"a": 2}}},
            "query_filter": {"a": 1},
        },
        expected=[],
        msg="Update while hidden should remove the old index entry",
    ),
    IndexTestCase(
        id="delete_removes_entry",
        input={
            "insert_docs": [{"a": 1}, {"a": 2}],
            "delete": {"q": {"a": 1}, "limit": 0},
            "query_filter": {"a": 1},
        },
        expected=[],
        msg="Delete while hidden should remove the corresponding index entry",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_BEHAVIOR_TESTS))
def test_write_maintained_in_hidden_index(collection, test):
    """Test writes while hidden are reflected after unhide."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    execute_command(collection, {"insert": collection.name, "documents": test.input["insert_docs"]})
    if "update" in test.input:
        execute_command(
            collection,
            {"update": collection.name, "updates": [test.input["update"]]},
        )
    if "delete" in test.input:
        execute_command(
            collection,
            {"delete": collection.name, "deletes": [test.input["delete"]]},
        )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": False}}
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.input["query_filter"], "hint": "a_1"},
    )
    assertSuccess(
        result,
        test.expected,
        transform=lambda docs: [d["a"] for d in docs],
        msg=test.msg,
    )


WRITE_SPECIAL_INDEX_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="multikey_maintained",
        indexes=({"key": {"tags": 1}, "name": "idx", "hidden": True},),
        input={
            "insert_docs": [{"_id": 1, "tags": ["a", "b", "c"]}, {"_id": 2, "tags": ["d"]}],
            "query_filter": {"tags": "b"},
        },
        expected=[1],
        msg="Array (multikey) writes while hidden should be indexed per element",
    ),
    IndexTestCase(
        id="partial_maintained",
        indexes=(
            {
                "key": {"a": 1},
                "name": "idx",
                "partialFilterExpression": {"a": {"$gte": 10}},
                "hidden": True,
            },
        ),
        input={
            "insert_docs": [{"_id": 1, "a": 5}, {"_id": 2, "a": 15}, {"_id": 3, "a": 20}],
            "query_filter": {"a": {"$gte": 10}},
        },
        expected=[2, 3],
        msg="Partial index while hidden should index only matching documents",
    ),
    IndexTestCase(
        id="compound_maintained",
        indexes=({"key": {"a": 1, "b": 1}, "name": "idx", "hidden": True},),
        input={
            "insert_docs": [{"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 1, "b": 3}],
            "query_filter": {"a": 1, "b": 3},
        },
        expected=[2],
        msg="Compound index writes while hidden should be maintained across both keys",
    ),
    IndexTestCase(
        id="sparse_maintained",
        indexes=({"key": {"a": 1}, "name": "idx", "sparse": True, "hidden": True},),
        input={
            "insert_docs": [{"_id": 1, "a": 1}, {"_id": 2}, {"_id": 3, "a": 3}],
            "query_filter": {},
        },
        expected=[1, 3],
        msg="Sparse index while hidden should skip documents missing the field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WRITE_SPECIAL_INDEX_TESTS))
def test_special_index_writes_maintained_while_hidden(collection, test):
    """Test writes to special-type hidden indexes are maintained after unhide."""
    execute_command(collection, {"createIndexes": collection.name, "indexes": [test.indexes[0]]})
    execute_command(collection, {"insert": collection.name, "documents": test.input["insert_docs"]})
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "idx", "hidden": False}}
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.input["query_filter"], "hint": "idx"},
    )
    assertSuccess(
        result,
        test.expected,
        transform=lambda docs: sorted(d["_id"] for d in docs),
        msg=test.msg,
    )


def test_indexstats_no_increment_while_hidden_zero_ops(collection):
    """Test queries on a hidden index don't increment its accesses counter."""
    collection.insert_many([{"a": i} for i in range(10)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    execute_command(collection, {"find": collection.name, "filter": {"a": 5}})
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$indexStats": {}}], "cursor": {}}
    )
    ops = get_index_ops(result, "a_1")
    assertSuccess(
        ops,
        Int64(0),
        raw_res=True,
        msg="A query while hidden should not increment the index accesses counter",
    )


def test_indexstats_shows_hidden_index_spec_hidden_true(collection):
    """Test $indexStats reports spec.hidden=true for hidden index."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$indexStats": {}}], "cursor": {}}
    )
    index_doc = get_index_doc(result, "a_1")
    hidden_val = index_doc.get("spec", {}).get("hidden", "__ABSENT__")
    assertSuccess(
        hidden_val,
        True,
        raw_res=True,
        msg="$indexStats should show the hidden index with spec.hidden=true",
    )


def test_indexstats_filter_on_spec_hidden(collection):
    """Test $indexStats can be filtered on spec.hidden to find hidden indexes."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1", "hidden": True},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$indexStats": {}}, {"$match": {"spec.hidden": True}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        ["a_1"],
        transform=lambda docs: sorted(d["name"] for d in docs),
        msg="Filtering $indexStats on spec.hidden should return only hidden indexes",
    )


def test_indexstats_nonhidden_accesses_increment_nonzero(collection):
    """Test $indexStats reports non-zero usage after querying a non-hidden index."""
    collection.insert_many([{"a": i} for i in range(10)])
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$gte": 0}}, "hint": "a_1"}
    )
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$indexStats": {}}], "cursor": {}}
    )
    ops = get_index_ops(result, "a_1")
    assertSuccess(
        ops >= 1,
        True,
        raw_res=True,
        msg="Using a non-hidden index should increment its $indexStats accesses",
    )


def test_indexstats_reset_only_affects_toggled_index_b_unchanged(collection):
    """Test hiding a_1 does not affect b_1's counter."""
    collection.insert_many([{"a": i, "b": i} for i in range(10)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1"}, {"key": {"b": 1}, "name": "b_1"}],
        },
    )
    execute_command(
        collection, {"find": collection.name, "filter": {"a": {"$gte": 0}}, "hint": "a_1"}
    )
    execute_command(
        collection, {"find": collection.name, "filter": {"b": {"$gte": 0}}, "hint": "b_1"}
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    result = execute_command(
        collection, {"aggregate": collection.name, "pipeline": [{"$indexStats": {}}], "cursor": {}}
    )
    b_ops = get_index_ops(result, "b_1")
    assertSuccess(
        b_ops >= 1,
        True,
        raw_res=True,
        msg="Hiding a_1 should not affect b_1's counter",
    )


@pytest.mark.slow
@pytest.mark.ttl
@pytest.mark.no_parallel
def test_ttl_expiry_while_hidden(collection, fast_ttl_monitor):
    """Test documents expire via a hidden TTL index."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"createdAt": 1}, "name": "ttl_1", "expireAfterSeconds": 0, "hidden": True}
            ],
        },
    )
    past = datetime.now(timezone.utc) - timedelta(days=1)
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"createdAt": past} for _ in range(5)]},
    )
    deadline = time.time() + 90
    count = None
    while time.time() < deadline:
        res = execute_command(collection, {"count": collection.name})
        count = res.get("n") if isinstance(res, dict) else None
        if count == 0:
            break
        time.sleep(2)
    assertSuccess(
        count,
        0,
        raw_res=True,
        msg="A hidden TTL index should still expire documents in the background",
    )


@pytest.mark.slow
@pytest.mark.ttl
@pytest.mark.no_parallel
def test_ttl_expiry_after_hiding_existing_ttl_index(collection, fast_ttl_monitor):
    """Test a TTL index continues expiring documents after being hidden."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"createdAt": 1}, "name": "ttl_1", "expireAfterSeconds": 0}],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "ttl_1", "hidden": True}}
    )
    past = datetime.now(timezone.utc) - timedelta(days=1)
    execute_command(
        collection,
        {"insert": collection.name, "documents": [{"createdAt": past} for _ in range(5)]},
    )
    deadline = time.time() + 90
    count = None
    while time.time() < deadline:
        res = execute_command(collection, {"count": collection.name})
        count = res.get("n") if isinstance(res, dict) else None
        if count == 0:
            break
        time.sleep(2)
    assertSuccess(
        count,
        0,
        raw_res=True,
        msg="Hiding a TTL index should not stop background expiry",
    )
