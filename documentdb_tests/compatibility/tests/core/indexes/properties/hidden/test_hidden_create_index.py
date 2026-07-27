"""Tests for hidden index creation, toggling, and listing."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.compatibility.tests.core.indexes.properties.hidden.utils.helpers import (
    get_index_spec,
    hidden_field,
)
from documentdb_tests.framework.assertions import (
    assertNotError,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


CREATE_HIDDEN_FIELD_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hidden_false_not_stored",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": False},),
        expected="__ABSENT__",
        msg="hidden:false should not be stored (field absent in getIndexes)",
    ),
    IndexTestCase(
        id="no_hidden_option_not_stored",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        expected="__ABSENT__",
        msg="Index without hidden option should default to non-hidden",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CREATE_HIDDEN_FIELD_TESTS))
def test_create_index_hidden_field_value(collection, test):
    """Test hidden option stores the correct value in listIndexes."""
    execute_command(collection, {"createIndexes": collection.name, "indexes": [test.indexes[0]]})
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        test.expected,
        raw_res=True,
        transform=lambda r: hidden_field(r, "a_1"),
        msg=test.msg,
    )


HIDE_UNHIDE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hide_by_key_pattern",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"keyPattern": {"a": 1}, "hidden": True},
        expected=True,
        msg="Hiding by key pattern should set hidden:true",
    ),
    IndexTestCase(
        id="hide_compound_by_full_key",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        input={"keyPattern": {"a": 1, "b": 1}, "hidden": True},
        expected=True,
        msg="Full compound key pattern should hide the compound index",
    ),
    IndexTestCase(
        id="unhide_by_key_pattern",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"keyPattern": {"a": 1}, "hidden": False},
        expected="__ABSENT__",
        msg="Unhiding by key pattern should remove the hidden field",
    ),
    IndexTestCase(
        id="hide_then_list_shows_true",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"name": "a_1", "hidden": True},
        expected=True,
        msg="Hiding should make listIndexes report hidden:true",
    ),
    IndexTestCase(
        id="unhide_removes_field_not_false",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"name": "a_1", "hidden": False},
        expected="__ABSENT__",
        msg="Unhiding should remove the hidden field, not set it to false",
    ),
]


@pytest.mark.parametrize("test", pytest_params(HIDE_UNHIDE_TESTS))
def test_collmod_hide_unhide(collection, test):
    """Test collMod hide/unhide sets the correct hidden field value."""
    execute_command(collection, {"createIndexes": collection.name, "indexes": [test.indexes[0]]})
    execute_command(collection, {"collMod": collection.name, "index": test.input})
    result = execute_command(collection, {"listIndexes": collection.name})
    idx_name = test.indexes[0].get("name", "a_1")
    assertSuccess(
        result,
        test.expected,
        raw_res=True,
        transform=lambda r: hidden_field(r, idx_name),
        msg=test.msg,
    )


IDEMPOTENT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="hide_already_hidden",
        indexes=({"key": {"a": 1}, "name": "a_1", "hidden": True},),
        input={"name": "a_1", "hidden": True},
        msg="Hiding an already-hidden index should be idempotent",
    ),
    IndexTestCase(
        id="unhide_already_unhidden",
        indexes=({"key": {"a": 1}, "name": "a_1"},),
        input={"name": "a_1", "hidden": False},
        msg="Unhiding an already-unhidden index should be idempotent",
    ),
]


@pytest.mark.parametrize("test", pytest_params(IDEMPOTENT_TESTS))
def test_collmod_idempotent(collection, test):
    """Test collMod hide/unhide is idempotent."""
    execute_command(collection, {"createIndexes": collection.name, "indexes": [test.indexes[0]]})
    result = execute_command(collection, {"collMod": collection.name, "index": test.input})
    assertNotError(result, msg=test.msg)


MULTIPLE_INDEX_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="multiple_hidden_coexist",
        indexes=(
            {"key": {"a": 1}, "name": "a_1", "hidden": True},
            {"key": {"b": 1}, "name": "b_1", "hidden": True},
        ),
        expected=(True, True),
        msg="Both indexes should be hidden simultaneously",
    ),
    IndexTestCase(
        id="mixed_hidden_and_non_hidden",
        indexes=(
            {"key": {"a": 1}, "name": "a_1", "hidden": True},
            {"key": {"b": 1}, "name": "b_1"},
        ),
        expected=(True, "__ABSENT__"),
        msg="Hidden index shows hidden:true; non-hidden index omits the field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(MULTIPLE_INDEX_TESTS))
def test_multiple_hidden_indexes(collection, test):
    """Test multiple hidden indexes listing behavior."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        test.expected,
        raw_res=True,
        transform=lambda r: (hidden_field(r, "a_1"), hidden_field(r, "b_1")),
        msg=test.msg,
    )


def test_create_hidden_index_response_structure(collection):
    """Test hidden:true returns numIndexesBefore/After and ok."""
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    assertSuccessPartial(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 2, "ok": 1.0},
        msg="createIndexes hidden:true should return expected response fields",
    )


def test_hide_null_index_arg_is_noop(collection):
    """Test collMod with null index argument is a no-op."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(collection, {"collMod": collection.name, "index": None})
    assertNotError(result, msg="collMod with a null index argument should be a no-op success")


def test_collmod_modifies_ttl_and_hidden_together(collection):
    """Test collMod can change expireAfterSeconds and hidden together."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"d": 1}, "name": "d_1", "expireAfterSeconds": 100}],
        },
    )
    execute_command(
        collection,
        {
            "collMod": collection.name,
            "index": {"name": "d_1", "expireAfterSeconds": 200, "hidden": True},
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        {"hidden": True, "expireAfterSeconds": 200},
        raw_res=True,
        transform=lambda r: {
            "hidden": get_index_spec(r, "d_1").get("hidden"),
            "expireAfterSeconds": get_index_spec(r, "d_1").get("expireAfterSeconds"),
        },
        msg="collMod should apply both expireAfterSeconds and hidden changes",
    )


def test_collmod_hidden_response_ok(collection):
    """Test collMod hiding returns ok:1."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]},
    )
    result = execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    assertSuccessPartial(result, {"ok": 1.0}, msg="collMod hiding an index should return ok:1")


def test_hidden_field_is_bson_boolean_true(collection):
    """Test hidden field is BSON boolean true."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        (True, "bool"),
        raw_res=True,
        transform=lambda r: (hidden_field(r, "a_1"), type(hidden_field(r, "a_1")).__name__),
        msg="hidden field must be BSON boolean true (not int or string)",
    )


def test_collstats_includes_hidden_index(collection):
    """Test $collStats includes hidden index in indexSizes."""
    collection.insert_many([{"a": i} for i in range(10)])
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "a_1", "hidden": True}],
        },
    )
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$collStats": {"storageStats": {}}}],
            "cursor": {},
        },
    )
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: any(
            "a_1" in doc.get("storageStats", {}).get("indexSizes", {})
            for doc in r["cursor"]["firstBatch"]
        ),
        msg="$collStats should account for the hidden index in indexSizes",
    )


def test_hiding_one_does_not_affect_others(collection):
    """Test hiding one index doesn't affect others."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"a": 1}, "name": "a_1"},
                {"key": {"b": 1}, "name": "b_1"},
            ],
        },
    )
    execute_command(
        collection, {"collMod": collection.name, "index": {"name": "a_1", "hidden": True}}
    )
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        (True, "__ABSENT__"),
        raw_res=True,
        transform=lambda r: (hidden_field(r, "a_1"), hidden_field(r, "b_1")),
        msg="Hiding a_1 should not change b_1's hidden state",
    )


@pytest.mark.no_parallel
def test_capped_hide_shows_hidden_true(collection, database_client):
    """Test hiding an index on a capped collection reports hidden:true."""
    capped_name = f"{collection.name}_capped"
    coll = database_client[capped_name]
    execute_command(coll, {"create": capped_name, "capped": True, "size": 1_000_000})
    execute_command(coll, {"insert": capped_name, "documents": [{"a": i} for i in range(20)]})
    execute_command(
        coll, {"createIndexes": capped_name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]}
    )
    execute_command(coll, {"collMod": capped_name, "index": {"name": "a_1", "hidden": True}})
    result = execute_command(coll, {"listIndexes": capped_name})
    assertSuccess(
        result,
        True,
        raw_res=True,
        transform=lambda r: hidden_field(r, "a_1"),
        msg="Hiding an index on a capped collection should report hidden:true",
    )


@pytest.mark.no_parallel
def test_capped_unhide_removes_hidden_field(collection, database_client):
    """Test unhiding an index on a capped collection removes the hidden field."""
    capped_name = f"{collection.name}_capped"
    coll = database_client[capped_name]
    execute_command(coll, {"create": capped_name, "capped": True, "size": 1_000_000})
    execute_command(coll, {"insert": capped_name, "documents": [{"a": i} for i in range(20)]})
    execute_command(
        coll, {"createIndexes": capped_name, "indexes": [{"key": {"a": 1}, "name": "a_1"}]}
    )
    execute_command(coll, {"collMod": capped_name, "index": {"name": "a_1", "hidden": True}})
    execute_command(coll, {"collMod": capped_name, "index": {"name": "a_1", "hidden": False}})
    result = execute_command(coll, {"listIndexes": capped_name})
    assertSuccess(
        result,
        "__ABSENT__",
        raw_res=True,
        transform=lambda r: hidden_field(r, "a_1"),
        msg="Unhiding an index on a capped collection should remove the hidden field",
    )
