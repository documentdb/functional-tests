"""Tests for $addToSet $each modifier and nested field targeting.

Covers: adding multiple values, duplicate filtering with $each, empty $each,
in-list duplicates in $each list, $each on missing field, dot notation,
deeply nested paths, intermediate path creation, numeric path components.
"""

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

EACH_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "each_adds_multiple",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [2, 3, 4]}}},
        expected={"_id": 1, "arr": [1, 2, 3, 4]},
        msg="$each should add multiple values individually",
    ),
    UpdateTestCase(
        "each_skips_existing",
        setup_docs=[{"_id": 1, "arr": [1, 2, 3]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [2, 3, 4, 5]}}},
        expected={"_id": 1, "arr": [1, 2, 3, 4, 5]},
        msg="$each should skip values already present",
    ),
    UpdateTestCase(
        "each_empty_array_noop",
        setup_docs=[{"_id": 1, "arr": [1, 2]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": []}}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="$each with empty array should be no-op",
    ),
    UpdateTestCase(
        "each_single_element",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [2]}}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="$each with single element should work like plain $addToSet",
    ),
    UpdateTestCase(
        "each_in_list_duplicates",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [2, 2, 3, 3, 3]}}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="$each should add only one copy of duplicate values in list",
    ),
    UpdateTestCase(
        "each_all_same_value",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [5, 5, 5]}}},
        expected={"_id": 1, "arr": [5]},
        msg="$each with all same values should add only one",
    ),
    UpdateTestCase(
        "each_on_missing_field",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [1, 2, 3]}}},
        expected={"_id": 1, "arr": [1, 2, 3]},
        msg="$each on missing field should create array with all values",
    ),
    UpdateTestCase(
        "each_missing_field_with_dups",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [1, 1, 2, 2]}}},
        expected={"_id": 1, "arr": [1, 2]},
        msg="$each on missing field with in-list dups should create unique array",
    ),
    UpdateTestCase(
        "each_with_nested_arrays",
        setup_docs=[{"_id": 1, "arr": [[1, 2]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [[1, 2], [3, 4]]}}},
        expected={"_id": 1, "arr": [[1, 2], [3, 4]]},
        msg="$each with nested arrays should detect array dup and add new one",
    ),
    UpdateTestCase(
        "each_mixed_bson_types",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [1, "two", None, True]}}},
        expected={"_id": 1, "arr": [1, "two", None, True]},
        msg="$each should handle mixed BSON types",
    ),
    UpdateTestCase(
        "each_with_objects",
        setup_docs=[{"_id": 1, "arr": [{"a": 1}]}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [{"a": 1}, {"b": 2}]}}},
        expected={"_id": 1, "arr": [{"a": 1}, {"b": 2}]},
        msg="$each should check object duplicates and add only new ones",
    ),
    UpdateTestCase(
        "each_cross_type_numeric_dedup",
        setup_docs=[{"_id": 1, "arr": []}],
        query={"_id": 1},
        update={"$addToSet": {"arr": {"$each": [1, Int64(1), 1.0, Decimal128("1")]}}},
        expected={"_id": 1, "arr": [1]},
        msg="$each should deduplicate numerically equivalent values across types",
    ),
]


NESTED_FIELD_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "dot_notation_one_level",
        setup_docs=[{"_id": 1, "a": {"b": [1, 2]}}],
        query={"_id": 1},
        update={"$addToSet": {"a.b": 3}},
        expected={"_id": 1, "a": {"b": [1, 2, 3]}},
        msg="Should add to nested array via dot notation",
    ),
    UpdateTestCase(
        "dot_notation_deep",
        setup_docs=[{"_id": 1, "a": {"b": {"c": [10]}}}],
        query={"_id": 1},
        update={"$addToSet": {"a.b.c": 20}},
        expected={"_id": 1, "a": {"b": {"c": [10, 20]}}},
        msg="Should add to deeply nested array",
    ),
    UpdateTestCase(
        "dot_notation_creates_intermediate",
        setup_docs=[{"_id": 1}],
        query={"_id": 1},
        update={"$addToSet": {"a.b": 1}},
        expected={"_id": 1, "a": {"b": [1]}},
        msg="Should create intermediate path when it does not exist",
    ),
    UpdateTestCase(
        "each_on_nested_path",
        setup_docs=[{"_id": 1, "a": {"b": [1]}}],
        query={"_id": 1},
        update={"$addToSet": {"a.b": {"$each": [2, 3]}}},
        expected={"_id": 1, "a": {"b": [1, 2, 3]}},
        msg="$each should work with dot notation nested path",
    ),
    UpdateTestCase(
        "each_objects_on_nested_path",
        setup_docs=[{"_id": 1, "x": {"y": [{"k": 1}]}}],
        query={"_id": 1},
        update={"$addToSet": {"x.y": {"$each": [{"k": 1}, {"k": 2}]}}},
        expected={"_id": 1, "x": {"y": [{"k": 1}, {"k": 2}]}},
        msg="$each with objects on nested path should check duplicates",
    ),
    UpdateTestCase(
        "four_level_nesting",
        setup_docs=[{"_id": 1, "a": {"b": {"c": {"d": [1]}}}}],
        query={"_id": 1},
        update={"$addToSet": {"a.b.c.d": 2}},
        expected={"_id": 1, "a": {"b": {"c": {"d": [1, 2]}}}},
        msg="Should work with 4-level deep nesting",
    ),
    UpdateTestCase(
        "numeric_path_in_array",
        setup_docs=[{"_id": 1, "a": [{"b": [1]}, {"b": [2]}]}],
        query={"_id": 1},
        update={"$addToSet": {"a.0.b": 3}},
        expected={"_id": 1, "a": [{"b": [1, 3]}, {"b": [2]}]},
        msg="Numeric path component should target array element",
    ),
    UpdateTestCase(
        "numeric_path_in_nested_array",
        setup_docs=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        query={"_id": 1},
        update={"$addToSet": {"arr.0": 5}},
        expected={"_id": 1, "arr": [[1, 2, 5], [3, 4]]},
        msg="Numeric path should add to inner array when outer is array of arrays",
    ),
    UpdateTestCase(
        "different_key_creates_new_field",
        setup_docs=[{"_id": 1, "arr": [1]}],
        query={"_id": 1},
        update={"$addToSet": {"other": 5}},
        expected={"_id": 1, "arr": [1], "other": [5]},
        msg="$addToSet on different key should create new array field",
    ),
]


ALL_TESTS = EACH_TESTS + NESTED_FIELD_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_addToSet_each_and_nested(collection, test: UpdateTestCase):
    """Test $addToSet $each modifier and nested field targeting."""
    collection.insert_many(test.setup_docs)
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": test.query, "u": test.update}],
        },
    )
    result = execute_command(collection, {"find": collection.name, "filter": test.query})
    assertSuccess(result, [test.expected], msg=test.msg)
