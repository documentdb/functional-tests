"""Tests for multikey index query behavior.

Validates array edge cases, embedded documents, query operators, null array
elements, and sort behavior.
"""

import pytest
from bson import Int64

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

ARRAY_EDGE_CASE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="query_empty_array",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": []}, {"_id": 2, "arr": [1]}),
        filter={"arr": []},  # exact match — only matches docs where arr is exactly []
        expected=[{"_id": 1, "arr": []}],
        msg="Should find doc with empty array",
    ),
    IndexQueryTestCase(
        id="query_single_element",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [42]},),
        filter={"arr": 42},
        expected=[{"_id": 1, "arr": [42]}],
        msg="Should match single element array",
    ),
    IndexQueryTestCase(
        id="query_duplicate_values",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [1, 1, 1]},),
        filter={"arr": 1},
        expected=[{"_id": 1, "arr": [1, 1, 1]}],
        msg="Should match despite duplicates",
    ),
    IndexQueryTestCase(
        id="query_exact_array_match",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=(
            {"_id": 1, "arr": [1, 2, 3]},
            {"_id": 2, "arr": [1, 2]},
            {"_id": 3, "arr": [1, 2, 3, 4]},
        ),
        filter={"arr": [1, 2, 3]},
        expected=[{"_id": 1, "arr": [1, 2, 3]}],
        msg="Exact array match only",
    ),
    IndexQueryTestCase(
        id="query_nested_array_of_arrays",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [[1, 2], [3, 4]]}, {"_id": 2, "arr": [[5, 6]]}),
        filter={"arr": [1, 2]},
        expected=[{"_id": 1, "arr": [[1, 2], [3, 4]]}],
        msg="Multikey index treats inner arrays as elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ARRAY_EDGE_CASE_TESTS))
def test_multikey_array_edge_cases(collection, test):
    """Verify multikey index handles empty arrays, single elements, and exact matches."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": "arr_1"}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


EMBEDDED_FIELD_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="query_embedded_field",
        indexes=({"key": {"arr.x": 1}, "name": "arr.x_1"},),
        doc=({"_id": 1, "arr": [{"x": 1}, {"x": 2}]}, {"_id": 2, "arr": [{"x": 3}, {"x": 4}]}),
        filter={"arr.x": 2},
        expected=[{"_id": 1, "arr": [{"x": 1}, {"x": 2}]}],
        msg="Should match embedded field in array",
    ),
    IndexQueryTestCase(
        id="query_embedded_range",
        indexes=({"key": {"arr.x": 1}, "name": "arr.x_1"},),
        doc=({"_id": 1, "arr": [{"x": 1}, {"x": 5}]}, {"_id": 2, "arr": [{"x": 10}]}),
        filter={"arr.x": {"$gt": 4}},
        sort={"_id": 1},
        expected=[{"_id": 1, "arr": [{"x": 1}, {"x": 5}]}, {"_id": 2, "arr": [{"x": 10}]}],
        msg="Range query on embedded array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EMBEDDED_FIELD_TESTS))
def test_multikey_embedded_field(collection, test):
    """Verify dotted-path multikey index matches elements within embedded documents in arrays."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": "arr.x_1"}
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


OPERATOR_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="query_in_operator",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [1, 2]}, {"_id": 2, "arr": [3, 4]}, {"_id": 3, "arr": [5, 6]}),
        filter={"arr": {"$in": [2, 5]}},
        sort={"_id": 1},
        expected=[{"_id": 1, "arr": [1, 2]}, {"_id": 3, "arr": [5, 6]}],
        msg="$in should match docs with any matching element",
    ),
    IndexQueryTestCase(
        id="query_all_operator",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [1, 2]}, {"_id": 3, "arr": [2, 3]}),
        filter={"arr": {"$all": [1, 2]}},
        sort={"_id": 1},
        expected=[{"_id": 1, "arr": [1, 2, 3]}, {"_id": 2, "arr": [1, 2]}],
        msg="$all should match docs containing all elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATOR_TESTS))
def test_multikey_query_operators(collection, test):
    """Verify $in and $all operators work correctly against multikey indexed array elements."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": "arr_1", "sort": test.sort}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


NULL_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="null_matches_array_element",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [1, None, 3]}, {"_id": 2, "arr": [None, None]}),
        filter={"arr": None},
        expected=[{"_id": 1, "arr": [1, None, 3]}, {"_id": 2, "arr": [None, None]}],
        msg="Should find docs with null array element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_TESTS))
def test_multikey_null(collection, test):
    """Verify multikey index finds documents containing null as an array element."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter, "hint": "arr_1"}
    )
    assertSuccess(result, test.expected, msg=test.msg, ignore_doc_order=True)


NUMERIC_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="numeric_int_matches_long",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [Int64(1), 2]},),
        filter={"arr": 1},
        expected=[{"_id": 1, "arr": [Int64(1), 2]}],
        msg="int query matches long in array",
    ),
    IndexQueryTestCase(
        id="numeric_double_matches_int",
        indexes=({"key": {"arr": 1}, "name": "arr_1"},),
        doc=({"_id": 1, "arr": [1]},),
        filter={"arr": 1.0},
        expected=[{"_id": 1, "arr": [1]}],
        msg="double 1.0 matches int 1 in array",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NUMERIC_QUERY_TESTS))
def test_multikey_numeric_query(collection, test):
    """Verify int/long/double are treated as equivalent when querying multikey array elements."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter, "hint": "arr_1"}
    )
    assertSuccess(result, test.expected, msg=test.msg)


def test_multikey_elemmatch_query(collection):
    """Test $elemMatch query on multikey indexed field."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr.x": 1}, "name": "arr.x_1"}]},
    )
    collection.insert_many(
        [
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 5, "y": "b"}]},
            {"_id": 2, "arr": [{"x": 10, "y": "c"}]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$elemMatch": {"x": {"$gt": 3}}}},
            "hint": "arr.x_1",
        },
    )
    assertSuccess(
        result,
        [
            {"_id": 1, "arr": [{"x": 1, "y": "a"}, {"x": 5, "y": "b"}]},
            {"_id": 2, "arr": [{"x": 10, "y": "c"}]},
        ],
        msg="$elemMatch should match docs with qualifying element",
        ignore_doc_order=True,
    )


def test_multikey_elemmatch_multi_condition(collection):
    """Test $elemMatch requires one element to satisfy all conditions."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr.x": 1}, "name": "arr.x_1"}]},
    )
    collection.insert_many(
        [
            {"_id": 1, "arr": [{"x": 5, "y": "a"}, {"x": 1, "y": "b"}]},
            {"_id": 2, "arr": [{"x": 5, "y": "b"}]},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"arr": {"$elemMatch": {"x": {"$gt": 3}, "y": "b"}}},
            "hint": "arr.x_1",
        },
    )
    assertSuccess(
        result,
        [{"_id": 2, "arr": [{"x": 5, "y": "b"}]}],
        msg="$elemMatch must match both conditions in the same element",
    )


def test_multikey_compound_query_on_array_element(collection):
    """Test querying compound multikey index on array element."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"tags": 1, "status": 1}, "name": "tags_status"}],
        },
    )
    collection.insert_many(
        [
            {"_id": 1, "tags": ["a", "b"], "status": "active"},
            {"_id": 2, "tags": ["c", "d"], "status": "inactive"},
        ]
    )
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"tags": "b", "status": "active"},
            "hint": "tags_status",
        },
    )
    assertSuccess(
        result,
        [{"_id": 1, "tags": ["a", "b"], "status": "active"}],
        msg="Should find by array element and scalar in compound",
    )


def test_multikey_sort_returns_results(collection):
    """Test sort on multikey indexed field returns results."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"arr": 1}, "name": "arr_1"}]},
    )
    collection.insert_many(
        [
            {"_id": 1, "arr": [3, 1]},
            {"_id": 2, "arr": [2, 5]},
            {"_id": 3, "arr": [0, 4]},
        ]
    )
    result = execute_command(
        collection, {"find": collection.name, "sort": {"arr": 1}, "hint": "arr_1"}
    )
    # Ascending sort uses the minimum array element
    assertSuccess(
        result,
        [{"_id": 3, "arr": [0, 4]}, {"_id": 1, "arr": [3, 1]}, {"_id": 2, "arr": [2, 5]}],
        msg="Sort on multikey field uses min value for ascending",
    )
