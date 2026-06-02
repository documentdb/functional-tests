"""Tests for multikey index properties.

Validates unique constraints, compound inserts, numeric equivalence, BSON type
distinction, sparse, and write operations.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

COMPOUND_INSERT_SUCCESS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="multikey_one_array_succeeds",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        input={"_id": 1, "a": [1, 2], "b": "scalar"},
        expected={"n": 1},
        msg="One array field in compound should succeed",
    ),
    IndexTestCase(
        id="multikey_other_field_array",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1"},),
        input={"_id": 1, "a": "scalar", "b": [1, 2]},
        expected={"n": 1},
        msg="Second field as array should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOUND_INSERT_SUCCESS_TESTS))
def test_multikey_compound_insert(collection, test):
    """Verify compound index accepts insert when only one field is an array (no parallel arrays)."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


UNIQUE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="unique_repeating_same_doc",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        input={"_id": 1, "arr": [1, 1, 2]},
        expected={"n": 1},
        msg="Repeating elements in same doc allowed",
    ),
    IndexTestCase(
        id="unique_shared_element_fails",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [1, 2]},),
        input={"_id": 2, "arr": [2, 3]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="Shared element 2 should cause duplicate error",
    ),
    IndexTestCase(
        id="unique_no_overlap_succeeds",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [1, 2]},),
        input={"_id": 2, "arr": [3, 4]},
        expected={"n": 1},
        msg="Non-overlapping arrays should succeed",
    ),
    IndexTestCase(
        id="unique_compound_shared_key_fails",
        indexes=({"key": {"a": 1, "b": 1}, "name": "a_1_b_1", "unique": True},),
        doc=({"_id": 1, "a": [1, 2], "b": "x"},),
        input={"_id": 2, "a": [2, 3], "b": "x"},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="Shared expanded key (2,x) in compound multikey should fail",
    ),
    IndexTestCase(
        id="unique_nested_array_shared_element",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [[1, 2], [3, 4]]},),
        input={"_id": 2, "arr": [[1, 2], [5, 6]]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="Shared inner array [1,2] under unique multikey should fail",
    ),
]


@pytest.mark.parametrize("test", pytest_params(UNIQUE_TESTS))
def test_multikey_unique(collection, test):
    """Verify unique constraint on multikey index rejects overlapping array elements across docs."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(list(test.doc))
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


NUMERIC_DUPLICATE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="numeric_int_long_duplicate",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [1]},),
        input={"_id": 2, "arr": [Int64(1)]},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="int and long array elements are duplicates",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_DUPLICATE_TESTS))
def test_multikey_numeric_duplicate(collection, test):
    """Verify int and long are treated as duplicates under unique multikey constraint."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


NULL_KEY_EQUIVALENCE_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="unique_null_array_vs_missing_field_collides",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [None]},),
        input={"_id": 2, "other": "x"},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="[null] and missing field both map to null key — should collide",
    ),
    IndexTestCase(
        id="unique_null_scalar_vs_missing_field_collides",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [1, 2]}, {"_id": 2, "arr": None}),
        input={"_id": 3, "other": "x"},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="{arr: null} and missing field both map to null key — should collide",
    ),
    IndexTestCase(
        id="unique_empty_array_does_not_collide_with_null",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [None]},),
        input={"_id": 2, "arr": []},
        expected={"n": 1},
        msg="[] maps to undefined key, not null — should NOT collide",
    ),
    IndexTestCase(
        id="unique_two_empty_arrays_collide",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=(
            {"_id": 1, "arr": [10, 20]},
            {"_id": 2, "arr": []},
        ),
        input={"_id": 3, "arr": []},
        expected={"writeErrors": [{"code": DUPLICATE_KEY_ERROR}]},
        msg="Two docs with [] under unique — undefined key should collide",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_KEY_EQUIVALENCE_TESTS))
def test_multikey_null_key_equivalence(collection, test):
    """Test null/missing/empty-array key equivalence under unique multikey index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


BSON_TYPE_DISTINCT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="data_bool_false_and_int_zero_distinct",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [False]},),
        input={"_id": 2, "arr": [0]},
        expected={"n": 1},
        msg="false and 0 in arrays should be distinct",
    ),
    IndexTestCase(
        id="data_bool_true_and_int_one_distinct",
        indexes=({"key": {"arr": 1}, "name": "arr_1", "unique": True},),
        doc=({"_id": 1, "arr": [True]},),
        input={"_id": 2, "arr": [1]},
        expected={"n": 1},
        msg="true and 1 in arrays should be distinct",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_TYPE_DISTINCT_TESTS))
def test_multikey_bson_type_distinct(collection, test):
    """Verify boolean and numeric types are not treated as duplicates (false≠0, true≠1)."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(collection, {"insert": collection.name, "documents": [test.input]})
    assertSuccessPartial(result, test.expected, msg=test.msg)


def test_multikey_write_push_updates_index(collection):
    """Test $push updates multikey index so new element is findable."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": 1}, "name": "arr_1"}]},
    )
    collection.insert_one({"_id": 1, "arr": [1, 2]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$push": {"arr": 3}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"arr": 3}})
    assertSuccess(result, [{"_id": 1, "arr": [1, 2, 3]}], msg="Pushed element should be findable")


def test_multikey_write_pull_updates_index(collection):
    """Test $pull updates multikey index so removed element no longer matches."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": 1}, "name": "arr_1"}]},
    )
    collection.insert_one({"_id": 1, "arr": [1, 2, 3]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$pull": {"arr": 2}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"arr": 2}})
    assertSuccess(result, [], msg="Pulled element should no longer match")


def test_multikey_write_addtoset_updates_index(collection):
    """Test $addToSet updates multikey index so added element is findable."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": 1}, "name": "arr_1"}]},
    )
    collection.insert_one({"_id": 1, "arr": [1, 2]})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$addToSet": {"arr": 5}}}]},
    )
    result = execute_command(collection, {"find": collection.name, "filter": {"arr": 5}})
    assertSuccess(result, [{"_id": 1, "arr": [1, 2, 5]}], msg="addToSet element should be findable")


def test_multikey_sparse_empty_array_is_present(collection):
    """Test sparse multikey treats empty array as present (indexed), not absent."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"arr": 1}, "name": "arr_1", "sparse": True}],
        },
    )
    collection.insert_many(
        [
            {"_id": 1, "arr": [1, 2]},
            {"_id": 2, "arr": []},
            {"_id": 3, "other": "x"},
        ]
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"arr": {"$exists": True}}, "hint": "arr_1"}
    )
    assertSuccess(
        result,
        [{"_id": 1, "arr": [1, 2]}, {"_id": 2, "arr": []}],
        msg="Sparse multikey includes empty array but excludes missing field",
        ignore_doc_order=True,
    )


def test_multikey_mixed_types_in_array(collection):
    """Test multikey index on array containing mixed BSON types."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": 1}, "name": "arr_1"}]},
    )
    collection.insert_one({"_id": 1, "arr": [1, "hello", True, None]})
    result = execute_command(
        collection, {"find": collection.name, "filter": {"arr": "hello"}, "hint": "arr_1"}
    )
    assertSuccess(
        result,
        [{"_id": 1, "arr": [1, "hello", True, None]}],
        msg="Should match string element in mixed array",
    )


def test_multikey_compound_arrays_separate_docs(collection):
    """Test compound multikey with arrays in different docs (no parallel arrays) succeeds."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1, "b": 1}, "name": "a_1_b_1"}],
        },
    )
    result = execute_command(
        collection,
        {
            "insert": collection.name,
            "documents": [{"_id": 1, "a": [1, 2], "b": "x"}, {"_id": 2, "a": "y", "b": [3, 4]}],
        },
    )
    assertSuccessPartial(result, {"n": 2}, msg="Arrays in separate docs should both succeed")
