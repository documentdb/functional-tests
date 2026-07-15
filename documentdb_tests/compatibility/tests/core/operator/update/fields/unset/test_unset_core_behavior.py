"""
Tests for $unset update operator - core behavior.

Covers BSON type coverage (unset field of each type), field removal verification
with $exists, no-op on non-existent fields, idempotent re-unset, and the
distinction between $unset and $set: null.
"""

import pytest
from bson import Binary, Code, MaxKey, MinKey, Regex

from documentdb_tests.compatibility.tests.core.operator.update.utils.update_test_case import (
    UpdateTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_EPOCH,
    DECIMAL128_HALF,
    INT32_MAX,
    INT64_MAX,
    OID_EPOCH,
    TS_EPOCH,
)

UNSET_BSON_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        id="double",
        setup_docs=[{"_id": 1, "field": 3.14}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing double",
    ),
    UpdateTestCase(
        id="string",
        setup_docs=[{"_id": 1, "field": "hello"}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing string",
    ),
    UpdateTestCase(
        id="object",
        setup_docs=[{"_id": 1, "field": {"k": "v"}}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing object",
    ),
    UpdateTestCase(
        id="array",
        setup_docs=[{"_id": 1, "field": [1, 2, 3]}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing array",
    ),
    UpdateTestCase(
        id="binData",
        setup_docs=[{"_id": 1, "field": Binary(b"\x01\x02")}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing binary",
    ),
    UpdateTestCase(
        id="objectId",
        setup_docs=[{"_id": 1, "field": OID_EPOCH}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing objectId",
    ),
    UpdateTestCase(
        id="bool",
        setup_docs=[{"_id": 1, "field": True}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing bool",
    ),
    UpdateTestCase(
        id="date",
        setup_docs=[{"_id": 1, "field": DATE_EPOCH}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing date",
    ),
    UpdateTestCase(
        id="null",
        setup_docs=[{"_id": 1, "field": None}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing null",
    ),
    UpdateTestCase(
        id="regex",
        setup_docs=[{"_id": 1, "field": Regex("^abc", "i")}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing regex",
    ),
    UpdateTestCase(
        id="javascript",
        setup_docs=[{"_id": 1, "field": Code("function(){}")}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing code",
    ),
    UpdateTestCase(
        id="int32",
        setup_docs=[{"_id": 1, "field": INT32_MAX}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing int32",
    ),
    UpdateTestCase(
        id="timestamp",
        setup_docs=[{"_id": 1, "field": TS_EPOCH}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing timestamp",
    ),
    UpdateTestCase(
        id="int64",
        setup_docs=[{"_id": 1, "field": INT64_MAX}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing int64",
    ),
    UpdateTestCase(
        id="decimal128",
        setup_docs=[{"_id": 1, "field": DECIMAL128_HALF}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing decimal128",
    ),
    UpdateTestCase(
        id="minKey",
        setup_docs=[{"_id": 1, "field": MinKey()}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing minKey",
    ),
    UpdateTestCase(
        id="maxKey",
        setup_docs=[{"_id": 1, "field": MaxKey()}],
        query={"_id": 1},
        update={"$unset": {"field": ""}},
        expected=[{"_id": 1}],
        msg="Should unset field containing maxKey",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNSET_BSON_TYPE_TESTS))
def test_unset_field_containing_bson_type(collection, test):
    """Test $unset removes field regardless of its BSON type."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, test.expected, msg=test.msg)


def test_unset_removes_field_entirely(collection):
    """Test $unset removes field (not findable with $exists:true)."""
    collection.insert_one({"_id": 1, "field": "data"})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"field": ""}}}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"field": {"$exists": True}}}
    )
    assertSuccess(result, [], msg="Unset field should not match $exists:true")


def test_unset_non_existent_field_noop(collection):
    """Test $unset on non-existent field is a no-op."""
    collection.insert_one({"_id": 1, "a": 1})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"missing": ""}}}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"_id": 1}})
    assertSuccess(result, [{"_id": 1, "a": 1}], msg="Unset on non-existent field should be no-op")


def test_re_unset_already_removed_field(collection):
    """Test $unset on a field that was already unset is a no-op."""
    collection.insert_one({"_id": 1, "a": 1, "b": 2})
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"a": ""}}}],
        },
    )
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"_id": 1}, "u": {"$unset": {"a": ""}}}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 0, "ok": 1.0}, msg="Re-unset should be no-op"
    )


def test_unset_distinct_from_set_null(collection):
    """$unset removes the key; $set: null keeps the key with null value."""
    collection.insert_many([{"_id": 1, "f": "x"}, {"_id": 2, "f": "x"}])
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [
                {"q": {"_id": 1}, "u": {"$unset": {"f": ""}}},
                {"q": {"_id": 2}, "u": {"$set": {"f": None}}},
            ],
        },
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"f": {"$exists": True}}, "sort": {"_id": 1}},
    )
    assertSuccess(
        result, [{"_id": 2, "f": None}], msg="$unset removes key, $set:null keeps key with null"
    )
