"""
Basic functionality tests for positional ($) projection operator.

Tests core matching behavior, array position selection, null/missing handling,
and BSON type preservation.
"""

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.projection.utils.projection_test_case import (  # noqa: E501
    ProjectionTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import DATE_EPOCH, DATE_MS_EPOCH

BASIC_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "first_matching_scalar",
        doc=[
            {"_id": 1, "grades": [70, 85, 90]},
            {"_id": 2, "grades": [60, 75, 95]},
        ],
        filter={"grades": {"$gte": 85}},
        projection={"grades.$": 1},
        expected=[{"_id": 1, "grades": [85]}, {"_id": 2, "grades": [95]}],
        msg="Returns first matching element from array of scalars",
    ),
    ProjectionTestCase(
        "first_matching_embedded_doc",
        doc=[
            {
                "_id": 1,
                "students": [
                    {"name": "Alice", "score": 70},
                    {"name": "Bob", "score": 85},
                    {"name": "Carol", "score": 90},
                ],
            },
        ],
        filter={"students.score": {"$gte": 85}},
        projection={"students.$": 1},
        expected=[{"_id": 1, "students": [{"name": "Bob", "score": 85}]}],
        msg="Returns first matching element from array of embedded documents",
    ),
    ProjectionTestCase(
        "no_element_matches",
        doc=[{"_id": 1, "grades": [80, 85, 90]}],
        filter={"_id": 1, "grades": {"$gt": 100}},
        projection={"grades.$": 1},
        expected=[],
        msg="No array element matches query returns empty result",
    ),
    ProjectionTestCase(
        "preserves_all_embedded_fields",
        doc=[
            {
                "_id": 1,
                "items": [
                    {"name": "a", "qty": 5, "price": 1.0},
                    {"name": "b", "qty": 15, "price": 2.5},
                ],
            },
        ],
        filter={"items.qty": {"$gt": 10}},
        projection={"items.$": 1},
        expected=[{"_id": 1, "items": [{"name": "b", "qty": 15, "price": 2.5}]}],
        msg="Preserves entire embedded document (all fields)",
    ),
    ProjectionTestCase(
        # The positional $ operator is only documented for array fields. Its behavior on a
        # scalar field is unspecified; this asserts the observed behavior (field unchanged).
        "non_array_field",
        doc=[{"_id": 1, "name": "test"}],
        filter={"name": "test"},
        projection={"name.$": 1},
        expected=[{"_id": 1, "name": "test"}],
        msg="Non-array field returns field unchanged",
    ),
    ProjectionTestCase(
        "mixed_type_array",
        doc=[{"_id": 1, "arr": ["hello", 42, True, None, 3.14]}],
        filter={"arr": 42},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [42]}],
        msg="Picks correct element from mixed BSON type array",
    ),
    ProjectionTestCase(
        "nested_array_elements",
        doc=[{"_id": 1, "arr": [[1, 2], [3, 4], [5, 6]]}],
        filter={"arr": [3, 4]},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [[3, 4]]}],
        msg="Array containing arrays — $ applies to outer level",
    ),
    ProjectionTestCase(
        "empty_array_no_match",
        doc=[{"_id": 1, "arr": []}],
        filter={"arr": 1},
        projection={"arr.$": 1},
        expected=[],
        msg="Empty array with non-matching filter returns empty result",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BASIC_TESTS))
def test_positional_basic(collection, test):
    """Test $ projection basic matching behavior."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


POSITION_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "first_element",
        doc=[{"_id": 1, "arr": [5, 10, 15]}],
        filter={"arr": {"$gte": 5}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [5]}],
        msg="First element matches returns first element",
    ),
    ProjectionTestCase(
        "last_element",
        doc=[{"_id": 1, "arr": [1, 2, 100]}],
        filter={"arr": {"$gt": 50}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [100]}],
        msg="Last element matches returns last element",
    ),
    ProjectionTestCase(
        "multiple_returns_first",
        doc=[{"_id": 1, "arr": [10, 20, 30, 40]}],
        filter={"arr": {"$gte": 20}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [20]}],
        msg="Multiple matches returns first",
    ),
    ProjectionTestCase(
        "single_element",
        doc=[{"_id": 1, "arr": [42]}],
        filter={"arr": 42},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [42]}],
        msg="Single element array returns that element",
    ),
    ProjectionTestCase(
        "all_match",
        doc=[{"_id": 1, "arr": [10, 20, 30]}],
        filter={"arr": {"$gte": 1}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [10]}],
        msg="All elements match returns first",
    ),
]


@pytest.mark.parametrize("test", pytest_params(POSITION_TESTS))
def test_positional_array_position(collection, test):
    """Test $ projection returns correct element based on match position."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


NULL_MISSING_TESTS: list[ProjectionTestCase] = [
    # The array-condition rule is validated per-document at execution time, not at
    # parse time. When the projected field doesn't exist, no error is raised — the field
    # is simply omitted. Compare with no_array_condition in test_positional_errors.py where
    # the array exists but the filter has no condition on it (errors at plan time).
    ProjectionTestCase(
        "missing_field",
        doc=[{"_id": 1, "other": "value"}],
        filter={"other": "value"},
        projection={"arr.$": 1},
        expected=[{"_id": 1}],
        msg="Missing projected field returns document without that field",
    ),
    ProjectionTestCase(
        "null_field",
        doc=[{"_id": 1, "arr": None}],
        filter={"arr": None},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": None}],
        msg="Null field returns null",
    ),
    ProjectionTestCase(
        "null_element_in_array",
        doc=[{"_id": 1, "arr": [1, None, 3]}],
        filter={"arr": None},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [None]}],
        msg="Null element in array matches null query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_TESTS))
def test_positional_null_missing(collection, test):
    """Test $ projection behavior with null/missing fields."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


# Each BSON_TYPE_TESTS case puts the target value at index 1 (after PLACEHOLDER) so the
# assertion proves $ returns the matched index, not just the first element.
PLACEHOLDER = {"placeholder": "skip"}

BSON_TYPE_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "int",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, 42]}],
        filter={"arr": 42},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [42]}],
        msg="$ matches and preserves int",
    ),
    ProjectionTestCase(
        "long",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, Int64(9223372036854775807)]}],
        filter={"arr": Int64(9223372036854775807)},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [Int64(9223372036854775807)]}],
        msg="$ matches and preserves long",
    ),
    ProjectionTestCase(
        "double",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, 3.14]}],
        filter={"arr": 3.14},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [3.14]}],
        msg="$ matches and preserves double",
    ),
    ProjectionTestCase(
        "decimal",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, Decimal128("0.5")]}],
        filter={"arr": Decimal128("0.5")},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [Decimal128("0.5")]}],
        msg="$ matches and preserves decimal128",
    ),
    ProjectionTestCase(
        "string",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, "hello"]}],
        filter={"arr": "hello"},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": ["hello"]}],
        msg="$ matches and preserves string",
    ),
    ProjectionTestCase(
        "bool",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, True]}],
        filter={"arr": True},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [True]}],
        msg="$ matches and preserves bool",
    ),
    ProjectionTestCase(
        "date",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, DATE_MS_EPOCH]}],
        filter={"arr": DATE_MS_EPOCH},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [DATE_EPOCH]}],
        msg="$ matches and preserves date",
    ),
    ProjectionTestCase(
        "null",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, None]}],
        filter={"arr": None},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [None]}],
        msg="$ matches and preserves null",
    ),
    ProjectionTestCase(
        "object",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, {"key": "value"}]}],
        filter={"arr": {"key": "value"}},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [{"key": "value"}]}],
        msg="$ matches and preserves embedded object",
    ),
    ProjectionTestCase(
        "array",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, ["a", "b", "c"]]}],
        filter={"arr": ["a", "b", "c"]},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [["a", "b", "c"]]}],
        msg="$ matches and preserves nested array",
    ),
    ProjectionTestCase(
        "bin_data",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, Binary(b"\x00\x01\x02")]}],
        filter={"arr": Binary(b"\x00\x01\x02")},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [b"\x00\x01\x02"]}],
        msg="$ matches and preserves binary data",
    ),
    ProjectionTestCase(
        "object_id",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, ObjectId("000000000000000000000000")]}],
        filter={"arr": ObjectId("000000000000000000000000")},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [ObjectId("000000000000000000000000")]}],
        msg="$ matches and preserves ObjectId",
    ),
    ProjectionTestCase(
        "timestamp",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, Timestamp(0, 1)]}],
        filter={"arr": Timestamp(0, 1)},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [Timestamp(0, 1)]}],
        msg="$ matches and preserves Timestamp",
    ),
    ProjectionTestCase(
        "min_key",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, MinKey()]}],
        filter={"arr": MinKey()},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [MinKey()]}],
        msg="$ matches and preserves MinKey",
    ),
    ProjectionTestCase(
        "max_key",
        doc=[{"_id": 1, "arr": [PLACEHOLDER, MaxKey()]}],
        filter={"arr": MaxKey()},
        projection={"arr.$": 1},
        expected=[{"_id": 1, "arr": [MaxKey()]}],
        msg="$ matches and preserves MaxKey",
    ),
]


@pytest.mark.parametrize("test", pytest_params(BSON_TYPE_TESTS))
def test_positional_bson_type(collection, test):
    """Test $ projection matches and preserves each BSON type."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)


NO_MATCH_TESTS: list[ProjectionTestCase] = [
    ProjectionTestCase(
        "regex_no_match",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        filter={"arr": Regex("^abc", "i")},
        projection={"arr.$": 1},
        expected=[],
        msg="$ with Regex filter that matches no element returns empty",
    ),
    ProjectionTestCase(
        "javascript",
        doc=[{"_id": 1, "arr": [1, 2, 3]}],
        filter={"arr": Code("function(){}")},
        projection={"arr.$": 1},
        expected=[],
        msg="$ with JavaScript filter that matches no element returns empty",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NO_MATCH_TESTS))
def test_positional_bson_type_no_match(collection, test):
    """Test $ projection with non-matchable BSON types returns empty result."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": test.filter,
            "projection": test.projection,
        },
    )
    assertSuccess(result, test.expected, msg=test.msg)
