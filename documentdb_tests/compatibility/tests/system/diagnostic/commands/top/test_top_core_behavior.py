"""Tests for top command core behavior.

Validates that counters reflect operations and cross-lock consistency invariants hold.
"""

import pytest

from documentdb_tests.compatibility.tests.system.diagnostic.utils.diagnostic_test_case import (
    DiagnosticTestCase,
)
from documentdb_tests.framework.assertions import assertProperties
from documentdb_tests.framework.executor import execute_admin_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Gt, Gte

pytestmark = pytest.mark.admin


# Property [Counter Behavior - Insert]: insert operations populate insert, writeLock, and time.
INSERT_COUNTER_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "insert_count_gte_1",
        command={"top": 1},
        checks={"insert.count": Gte(1)},
        msg="insert.count should be >= 1 after inserts",
    ),
    DiagnosticTestCase(
        "insert_writeLock_count_gte_1",
        command={"top": 1},
        checks={"writeLock.count": Gte(1)},
        msg="writeLock.count should be >= 1 after inserts",
    ),
    DiagnosticTestCase(
        "insert_time_gt_0",
        command={"top": 1},
        checks={"insert.time": Gt(0)},
        msg="insert.time should be > 0 after inserts",
    ),
]


@pytest.mark.parametrize("test", pytest_params(INSERT_COUNTER_TESTS))
def test_top_after_inserts(collection, test):
    """Test counters after insert operations."""
    collection.insert_many([{"_id": i} for i in range(10)])
    result = execute_admin_command(collection, test.command)
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(ns_data, test.checks, msg=test.msg, raw_res=True)


# Property [Counter Behavior - Query]: find operations populate queries, readLock, and time.
QUERY_COUNTER_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "queries_count_gte_1",
        command={"top": 1},
        checks={"queries.count": Gte(1)},
        msg="queries.count should be >= 1 after query",
    ),
    DiagnosticTestCase(
        "query_readLock_count_gte_1",
        command={"top": 1},
        checks={"readLock.count": Gte(1)},
        msg="readLock.count should be >= 1 after query",
    ),
    DiagnosticTestCase(
        "queries_time_gt_0",
        command={"top": 1},
        checks={"queries.time": Gt(0)},
        msg="queries.time should be > 0 after query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(QUERY_COUNTER_TESTS))
def test_top_after_query(collection, test):
    """Test counters after find operations."""
    collection.insert_one({"_id": 1})
    list(collection.find())
    result = execute_admin_command(collection, test.command)
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(ns_data, test.checks, msg=test.msg, raw_res=True)


# Property [Counter Behavior - Update]: update operations populate the update counter.
UPDATE_COUNTER_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "update_count_gte_1",
        command={"top": 1},
        checks={"update.count": Gte(1)},
        msg="update.count should be >= 1 after update",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UPDATE_COUNTER_TESTS))
def test_top_after_update(collection, test):
    """Test counters after update operations."""
    collection.insert_one({"_id": 1, "a": 1})
    collection.update_one({"_id": 1}, {"$set": {"a": 2}})
    result = execute_admin_command(collection, test.command)
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(ns_data, test.checks, msg=test.msg, raw_res=True)


# Property [Counter Behavior - Remove]: delete operations populate the remove counter.
REMOVE_COUNTER_TESTS: list[DiagnosticTestCase] = [
    DiagnosticTestCase(
        "remove_count_gte_1",
        command={"top": 1},
        checks={"remove.count": Gte(1)},
        msg="remove.count should be >= 1 after delete",
    ),
]


@pytest.mark.parametrize("test", pytest_params(REMOVE_COUNTER_TESTS))
def test_top_after_remove(collection, test):
    """Test counters after delete operations."""
    collection.insert_one({"_id": 1})
    collection.delete_one({"_id": 1})
    result = execute_admin_command(collection, test.command)
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(ns_data, test.checks, msg=test.msg, raw_res=True)


# Property [Cross-Lock Invariants]: aggregate lock counters are >= the sum of their components.


def test_top_readLock_count_gte_queries_count(collection):
    """Test that readLock.count >= queries.count."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    list(collection.find())
    collection.update_one({"_id": 0}, {"$set": {"a": 99}})
    collection.delete_one({"_id": 4})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(
        ns_data,
        {"readLock.count": Gte(ns_data["queries"]["count"])},
        msg="readLock.count should be >= queries.count",
        raw_res=True,
    )


def test_top_readLock_time_gte_queries_time(collection):
    """Test that readLock.time >= queries.time."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    list(collection.find())
    collection.update_one({"_id": 0}, {"$set": {"a": 99}})
    collection.delete_one({"_id": 4})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    assertProperties(
        ns_data,
        {"readLock.time": Gte(ns_data["queries"]["time"])},
        msg="readLock.time should be >= queries.time",
        raw_res=True,
    )


def test_top_writeLock_count_gte_insert_update_remove(collection):
    """Test that writeLock.count >= insert.count + update.count + remove.count."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    list(collection.find())
    collection.update_one({"_id": 0}, {"$set": {"a": 99}})
    collection.delete_one({"_id": 4})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    write_sum = ns_data["insert"]["count"] + ns_data["update"]["count"] + ns_data["remove"]["count"]
    assertProperties(
        ns_data,
        {"writeLock.count": Gte(write_sum)},
        msg="writeLock.count should be >= insert+update+remove count",
        raw_res=True,
    )


def test_top_writeLock_time_gte_insert_update_remove(collection):
    """Test that writeLock.time >= insert.time + update.time + remove.time."""
    collection.insert_many([{"_id": i, "a": i} for i in range(5)])
    list(collection.find())
    collection.update_one({"_id": 0}, {"$set": {"a": 99}})
    collection.delete_one({"_id": 4})
    result = execute_admin_command(collection, {"top": 1})
    ns = f"{collection.database.name}.{collection.name}"
    ns_data = result["totals"].get(ns)
    if ns_data is None:
        raise AssertionError(f"Namespace {ns} not found in top totals")
    write_sum = ns_data["insert"]["time"] + ns_data["update"]["time"] + ns_data["remove"]["time"]
    assertProperties(
        ns_data,
        {"writeLock.time": Gte(write_sum)},
        msg="writeLock.time should be >= insert+update+remove time",
        raw_res=True,
    )
