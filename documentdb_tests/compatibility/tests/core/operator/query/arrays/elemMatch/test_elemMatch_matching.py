"""
Tests for $elemMatch query matching behavior.

Covers valid arguments, single-element vs implicit matching, data type coverage,
empty/non-array fields, multikey, large arrays, duplicate keys,
and mixed array types with nested array values.
"""

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)
from bson.codec_options import CodecOptions

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

VALID_ARGUMENT_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_condition",
        filter={"a": {"$elemMatch": {"$gt": 5}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [3, 7]}],
        msg="Should match with single condition",
    ),
    QueryTestCase(
        id="multiple_conditions",
        filter={"a": {"$elemMatch": {"$gt": 5, "$lt": 10}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [1, 12]}],
        expected=[{"_id": 1, "a": [3, 7]}],
        msg="Should match with multiple conditions",
    ),
    QueryTestCase(
        id="empty_object",
        filter={"a": {"$elemMatch": {}}},
        doc=[{"_id": 1, "a": [1, 2]}, {"_id": 2, "a": []}],
        expected=[],
        msg="Empty object matches no documents",
    ),
    QueryTestCase(
        id="implicit_equality",
        filter={"a": {"$elemMatch": {"x": 1}}},
        doc=[
            {"_id": 1, "a": [{"x": 1}, {"x": 2}]},
            {"_id": 2, "a": [{"x": 3}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1}, {"x": 2}]}],
        msg="Implicit equality without operator should work",
    ),
]

MATCHING_BEHAVIOR_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="single_element_satisfies_both",
        filter={"a": {"$elemMatch": {"$gt": 5, "$lt": 10}}},
        doc=[
            {"_id": 1, "a": [3, 7, 12]},
            {"_id": 2, "a": [3, 12]},
        ],
        expected=[{"_id": 1, "a": [3, 7, 12]}],
        msg="7 satisfies both $gt:5 and $lt:10",
    ),
    QueryTestCase(
        id="no_single_element_satisfies_both",
        filter={"a": {"$elemMatch": {"$gt": 5, "$lt": 10}}},
        doc=[{"_id": 1, "a": [3, 12]}],
        expected=[],
        msg="No single element satisfies both conditions",
    ),
    QueryTestCase(
        id="implicit_matching_different_elements",
        filter={"a": {"$gt": 5, "$lt": 10}},
        doc=[{"_id": 1, "a": [3, 12]}],
        expected=[{"_id": 1, "a": [3, 12]}],
        msg="Implicit matching: 12>5 and 3<10 from different elements",
    ),
    QueryTestCase(
        id="impossible_range_elemMatch",
        filter={"a": {"$elemMatch": {"$lt": 5, "$gt": 10}}},
        doc=[{"_id": 1, "a": [3, 12]}],
        expected=[],
        msg="No single element can be both <5 and >10",
    ),
    QueryTestCase(
        id="impossible_range_implicit_matches",
        filter={"a": {"$lt": 5, "$gt": 10}},
        doc=[{"_id": 1, "a": [3, 12]}],
        expected=[{"_id": 1, "a": [3, 12]}],
        msg="Implicit: 3<5 and 12>10 from different elements",
    ),
]

DATA_TYPE_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="strings",
        filter={"a": {"$elemMatch": {"$eq": "hello"}}},
        doc=[
            {"_id": 1, "a": ["hello", "world"]},
            {"_id": 2, "a": ["foo"]},
        ],
        expected=[{"_id": 1, "a": ["hello", "world"]}],
        msg="Should match string element",
    ),
    QueryTestCase(
        id="integers",
        filter={"a": {"$elemMatch": {"$gt": 5}}},
        doc=[{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [1, 2]}],
        expected=[{"_id": 1, "a": [3, 7]}],
        msg="Should match integer element",
    ),
    QueryTestCase(
        id="longs",
        filter={"a": {"$elemMatch": {"$eq": Int64(100)}}},
        doc=[
            {"_id": 1, "a": [Int64(100), Int64(200)]},
            {"_id": 2, "a": [Int64(50)]},
        ],
        expected=[{"_id": 1, "a": [Int64(100), Int64(200)]}],
        msg="Should match long element",
    ),
    QueryTestCase(
        id="doubles",
        filter={"a": {"$elemMatch": {"$gte": 1.5}}},
        doc=[{"_id": 1, "a": [1.5, 2.5]}, {"_id": 2, "a": [0.5]}],
        expected=[{"_id": 1, "a": [1.5, 2.5]}],
        msg="Should match double element",
    ),
    QueryTestCase(
        id="decimal128",
        filter={"a": {"$elemMatch": {"$eq": Decimal128("1.5")}}},
        doc=[
            {"_id": 1, "a": [Decimal128("1.5")]},
            {"_id": 2, "a": [Decimal128("2.5")]},
        ],
        expected=[{"_id": 1, "a": [Decimal128("1.5")]}],
        msg="Should match decimal128 element",
    ),
    QueryTestCase(
        id="booleans",
        filter={"a": {"$elemMatch": {"$eq": True}}},
        doc=[
            {"_id": 1, "a": [True, False]},
            {"_id": 2, "a": [False]},
        ],
        expected=[{"_id": 1, "a": [True, False]}],
        msg="Should match boolean element",
    ),
    QueryTestCase(
        id="dates",
        filter={"a": {"$elemMatch": {"$gt": datetime(2024, 1, 1, tzinfo=timezone.utc)}}},
        doc=[
            {"_id": 1, "a": [datetime(2024, 6, 1, tzinfo=timezone.utc)]},
            {"_id": 2, "a": [datetime(2023, 1, 1, tzinfo=timezone.utc)]},
        ],
        expected=[{"_id": 1, "a": [datetime(2024, 6, 1, tzinfo=timezone.utc)]}],
        msg="Should match date element",
    ),
    QueryTestCase(
        id="objectids",
        filter={"a": {"$elemMatch": {"$eq": ObjectId("507f1f77bcf86cd799439011")}}},
        doc=[
            {"_id": 1, "a": [ObjectId("507f1f77bcf86cd799439011")]},
            {"_id": 2, "a": [ObjectId("507f1f77bcf86cd799439012")]},
        ],
        expected=[{"_id": 1, "a": [ObjectId("507f1f77bcf86cd799439011")]}],
        msg="Should match objectId element",
    ),
    QueryTestCase(
        id="null_element",
        filter={"a": {"$elemMatch": {"$eq": None}}},
        doc=[
            {"_id": 1, "a": [1, None, 3]},
            {"_id": 2, "a": [1, 2]},
        ],
        expected=[{"_id": 1, "a": [1, None, 3]}],
        msg="Should match null element",
    ),
    QueryTestCase(
        id="embedded_documents",
        filter={"a": {"$elemMatch": {"x": 1, "y": 2}}},
        doc=[
            {"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]},
            {"_id": 2, "a": [{"x": 1, "y": 3}]},
        ],
        expected=[{"_id": 1, "a": [{"x": 1, "y": 2}, {"x": 3}]}],
        msg="Should match embedded document element",
    ),
    QueryTestCase(
        id="nested_arrays",
        filter={"a": {"$elemMatch": {"$eq": [1, 2]}}},
        doc=[
            {"_id": 1, "a": [[1, 2], [3, 4]]},
            {"_id": 2, "a": [[5, 6]]},
        ],
        expected=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        msg="Should match nested array element",
    ),
    QueryTestCase(
        id="binary",
        filter={"a": {"$elemMatch": {"$eq": Binary(b"\x01\x02")}}},
        doc=[
            {"_id": 1, "a": [Binary(b"\x01\x02")]},
            {"_id": 2, "a": [Binary(b"\x03")]},
        ],
        expected=[{"_id": 1, "a": [b"\x01\x02"]}],
        msg="Should match binary element",
    ),
    QueryTestCase(
        id="timestamps",
        filter={"a": {"$elemMatch": {"$eq": Timestamp(1, 1)}}},
        doc=[
            {"_id": 1, "a": [Timestamp(1, 1)]},
            {"_id": 2, "a": [Timestamp(2, 1)]},
        ],
        expected=[{"_id": 1, "a": [Timestamp(1, 1)]}],
        msg="Should match timestamp element",
    ),
    QueryTestCase(
        id="regex",
        filter={"a": {"$elemMatch": {"$eq": Regex("^abc", "i")}}},
        doc=[
            {"_id": 1, "a": [Regex("^abc", "i")]},
            {"_id": 2, "a": [Regex("^def")]},
        ],
        expected=[{"_id": 1, "a": [Regex("^abc", "i")]}],
        msg="Should match regex element",
    ),
    QueryTestCase(
        id="minkey",
        filter={"a": {"$elemMatch": {"$eq": MinKey()}}},
        doc=[{"_id": 1, "a": [MinKey()]}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": [MinKey()]}],
        msg="Should match MinKey element",
    ),
    QueryTestCase(
        id="maxkey",
        filter={"a": {"$elemMatch": {"$eq": MaxKey()}}},
        doc=[{"_id": 1, "a": [MaxKey()]}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 1, "a": [MaxKey()]}],
        msg="Should match MaxKey element",
    ),
    QueryTestCase(
        id="mixed_types",
        filter={"a": {"$elemMatch": {"$eq": True}}},
        doc=[
            {"_id": 1, "a": [1, "a", True, None]},
            {"_id": 2, "a": [1, "a", None]},
        ],
        expected=[{"_id": 1, "a": [1, "a", True, None]}],
        msg="Should match in mixed-type array",
    ),
    QueryTestCase(
        id="mixed_types_with_nested_array",
        filter={"a": {"$elemMatch": {"$eq": [1, 2]}}},
        doc=[
            {"_id": 1, "a": [1, "a", [1, 2], None]},
            {"_id": 2, "a": [1, "a", [3, 4]]},
        ],
        expected=[{"_id": 1, "a": [1, "a", [1, 2], None]}],
        msg="Should match nested array element in mixed-type array",
    ),
]

NON_ARRAY_FIELD_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="scalar_string",
        filter={"a": {"$elemMatch": {"$eq": "hello"}}},
        doc=[{"_id": 1, "a": "hello"}],
        expected=[],
        msg="$elemMatch on string field returns no match",
    ),
    QueryTestCase(
        id="scalar_integer",
        filter={"a": {"$elemMatch": {"$gt": 0}}},
        doc=[{"_id": 1, "a": 10}],
        expected=[],
        msg="$elemMatch on integer field returns no match",
    ),
    QueryTestCase(
        id="object_field",
        filter={"a": {"$elemMatch": {"$gt": 0}}},
        doc=[{"_id": 1, "a": {"x": 1}}],
        expected=[],
        msg="$elemMatch on object field returns no match",
    ),
    QueryTestCase(
        id="boolean_field",
        filter={"a": {"$elemMatch": {"$eq": True}}},
        doc=[{"_id": 1, "a": True}],
        expected=[],
        msg="$elemMatch on boolean field returns no match",
    ),
    QueryTestCase(
        id="date_field",
        filter={"a": {"$elemMatch": {"$gt": datetime(2020, 1, 1, tzinfo=timezone.utc)}}},
        doc=[{"_id": 1, "a": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        expected=[],
        msg="$elemMatch on date field returns no match",
    ),
    QueryTestCase(
        id="null_field",
        filter={"a": {"$elemMatch": {"$eq": None}}},
        doc=[{"_id": 1, "a": None}],
        expected=[],
        msg="$elemMatch on null field returns no match",
    ),
]

EMPTY_ARRAY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="empty_array_gt",
        filter={"a": {"$elemMatch": {"$gt": 0}}},
        doc=[{"_id": 1, "a": []}, {"_id": 2, "a": [1]}],
        expected=[{"_id": 2, "a": [1]}],
        msg="$elemMatch on empty array returns no match",
    ),
]

MULTIKEY_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="multikey_gt_lt",
        filter={"a": {"$elemMatch": {"$gt": 3, "$lt": 8}}},
        doc=[
            {"_id": 1, "a": [1, 5, 10]},
            {"_id": 2, "a": [1, 2, 10]},
        ],
        expected=[{"_id": 1, "a": [1, 5, 10]}],
        msg="$elemMatch with $gt and $lt on multikey array",
    ),
    QueryTestCase(
        id="in_with_null_and_empty_array",
        filter={"a": {"$elemMatch": {"$in": [None, []]}}},
        doc=[
            {"_id": 1, "a": [1, None, 3]},
            {"_id": 2, "a": [1, 2, 3]},
            {"_id": 3, "a": [[], 1]},
        ],
        expected=[
            {"_id": 1, "a": [1, None, 3]},
            {"_id": 3, "a": [[], 1]},
        ],
        msg="$elemMatch with $in containing null and empty array",
    ),
    QueryTestCase(
        id="in_with_deeply_nested_arrays",
        filter={"a": {"$elemMatch": {"$in": [[1, 2]]}}},
        doc=[
            {"_id": 1, "a": [[1, 2], [3, 4]]},
            {"_id": 2, "a": [[5, 6]]},
        ],
        expected=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        msg="$elemMatch with $in on deeply nested arrays",
    ),
]

ALL_MATCHING_TESTS = (
    VALID_ARGUMENT_TESTS
    + MATCHING_BEHAVIOR_TESTS
    + DATA_TYPE_TESTS
    + NON_ARRAY_FIELD_TESTS
    + EMPTY_ARRAY_TESTS
    + MULTIKEY_TESTS
)


UTC_CODEC = CodecOptions(tz_aware=True, tzinfo=timezone.utc)


@pytest.mark.parametrize("test", pytest_params(ALL_MATCHING_TESTS))
def test_elemMatch_matching(collection, test):
    """Test $elemMatch query matching behavior."""
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter},
        codec_options=UTC_CODEC,
    )
    assertSuccess(result, test.expected, ignore_doc_order=True)


def test_elemMatch_large_array_match_at_end(collection):
    """Test $elemMatch on 10000-element array where match is at end."""
    arr = list(range(10000))
    collection.insert_one({"_id": 1, "a": arr})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": {"$elemMatch": {"$eq": 9999}}},
        },
    )
    assertSuccess(result, [{"_id": 1, "a": arr}])


def test_elemMatch_large_array_no_match(collection):
    """Test $elemMatch on 10000-element array where no match exists."""
    arr = list(range(10000))
    collection.insert_one({"_id": 1, "a": arr})
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": {"$elemMatch": {"$eq": 99999}}},
        },
    )
    assertSuccess(result, [])


def test_elemMatch_duplicate_key_last_wins(collection):
    """Test that duplicate $elemMatch keys in Python dict — last key wins."""
    collection.insert_many([{"_id": 1, "a": [3, 7]}, {"_id": 2, "a": [6, 8]}])
    result = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {
                "a": {
                    "$elemMatch": {"$gt": 1},  # noqa: F601
                    "$elemMatch": {"$lt": 5},  # noqa: F601
                }
            },
        },
    )
    assertSuccess(result, [{"_id": 1, "a": [3, 7]}])
