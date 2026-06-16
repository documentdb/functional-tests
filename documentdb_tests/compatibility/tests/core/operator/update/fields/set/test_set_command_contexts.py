"""
Tests for $set update operator - command contexts.

Covers positional operators ($, $[], $[identifier] with arrayFilters),
upsert, multi-update, nModified semantics, and cross-type same-value behavior.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

SET_COMMAND_CONTEXT_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="with_all_positional",
        setup_docs=[{"_id": 1, "arr": [{"v": 1}, {"v": 2}, {"v": 3}]}],
        query={"_id": 1},
        update={"$set": {"arr.$[].v": 0}},
        expected=[{"_id": 1, "arr": [{"v": 0}, {"v": 0}, {"v": 0}]}],
        msg="$[] should update all elements",
    ),
    UpdateTestCase(
        id="with_matched_positional",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1, "arr": 2},
        update={"$set": {"arr.$": 99}},
        expected=[{"_id": 1, "arr": [1, 99, 3]}],
        msg="$ should update matched array element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_COMMAND_CONTEXT_TESTS))
def test_set_command_contexts(collection, test):
    """Test $set in various command contexts."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update, "upsert": test.upsert}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)


def test_set_with_filtered_positional(collection):
    """Test $set with $[identifier] and declared arrayFilters updates matching elements."""
    collection.insert_one({"_id": 1, "grades": [50, 80, 90, 40, 70]})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {
                    "q": {"_id": 1},
                    "u": {"$set": {"grades.$[elem]": 100}},
                    "arrayFilters": [{"elem": {"$gte": 80}}],
                }
            ],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(
        result,
        [{"_id": 1, "grades": [50, 100, 100, 40, 70]}],
        msg="$[identifier] with arrayFilters should update only matching elements",
    )


SET_CROSS_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="int32_to_int64",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"a": Int64(1)}},
        msg="int32 → int64 same numeric value",
    ),
    UpdateTestCase(
        id="int32_to_double",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"a": 1.0}},
        msg="int32 → double same numeric value",
    ),
    UpdateTestCase(
        id="int32_to_decimal128",
        setup_docs=[{"_id": 1, "a": 1}],
        query={"_id": 1},
        update={"$set": {"a": Decimal128("1")}},
        msg="int32 → decimal128 same numeric value",
    ),
    UpdateTestCase(
        id="int64_to_int32",
        setup_docs=[{"_id": 1, "a": Int64(1)}],
        query={"_id": 1},
        update={"$set": {"a": 1}},
        msg="int64 → int32 same numeric value",
    ),
    UpdateTestCase(
        id="double_to_int32",
        setup_docs=[{"_id": 1, "a": 1.0}],
        query={"_id": 1},
        update={"$set": {"a": 1}},
        msg="double → int32 same numeric value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SET_CROSS_TYPE_TESTS))
def test_set_cross_type_same_value(collection, test):
    """Test $set with numerically equivalent but type-distinct value reports nModified:1."""
    collection.insert_many(test.setup_docs)
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "nModified": 1, "ok": 1.0}, msg=test.msg)


def test_set_upsert_new(collection):
    """Test $set with upsert creates doc from query when no match."""
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}, "upsert": True}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": 1}], msg="Should create doc on upsert with no match")


def test_set_update_many(collection):
    """Test $set with multi:true updates all matching documents."""
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 1}, {"_id": 3, "a": 2}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 1}, "u": {"$set": {"b": 99}}, "multi": True}],
        },
    )
    assertSuccessPartial(
        result, {"n": 2, "nModified": 2, "ok": 1.0}, msg="Should update all matching"
    )


def test_set_same_value_no_modification(collection):
    """Test $set field to its current value results in nModified:0."""
    collection.insert_one({"_id": 1, "a": 1})
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$set": {"a": 1}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 0, "ok": 1.0}, msg="Setting same value should not modify"
    )
