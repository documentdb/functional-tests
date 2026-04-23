from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    Decimal128,
    Int64,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Ascending and Descending Sort]: sort order 1 sorts documents in
# ascending order and sort order -1 sorts documents in descending order by the
# specified field, for all BSON types that support ordering.
SORT_ASC_DESC_TESTS: list[StageTestCase] = [
    StageTestCase(
        "asc_int",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        msg="$sort with order 1 should sort int32 in ascending order",
    ),
    StageTestCase(
        "desc_int",
        docs=[{"_id": 1, "v": 10}, {"_id": 2, "v": 20}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": 20}, {"_id": 1, "v": 10}],
        msg="$sort with order -1 should sort int32 in descending order",
    ),
    StageTestCase(
        "asc_int64",
        docs=[{"_id": 1, "v": Int64(10)}, {"_id": 2, "v": Int64(20)}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": Int64(10)}, {"_id": 2, "v": Int64(20)}],
        msg="$sort with order 1 should sort Int64 in ascending order",
    ),
    StageTestCase(
        "desc_int64",
        docs=[{"_id": 1, "v": Int64(10)}, {"_id": 2, "v": Int64(20)}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": Int64(20)}, {"_id": 1, "v": Int64(10)}],
        msg="$sort with order -1 should sort Int64 in descending order",
    ),
    StageTestCase(
        "asc_double",
        docs=[{"_id": 1, "v": 1.5}, {"_id": 2, "v": 2.5}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": 1.5}, {"_id": 2, "v": 2.5}],
        msg="$sort with order 1 should sort doubles in ascending order",
    ),
    StageTestCase(
        "desc_double",
        docs=[{"_id": 1, "v": 1.5}, {"_id": 2, "v": 2.5}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": 2.5}, {"_id": 1, "v": 1.5}],
        msg="$sort with order -1 should sort doubles in descending order",
    ),
    StageTestCase(
        "asc_decimal128",
        docs=[{"_id": 1, "v": Decimal128("10")}, {"_id": 2, "v": Decimal128("20")}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": Decimal128("10")}, {"_id": 2, "v": Decimal128("20")}],
        msg="$sort with order 1 should sort Decimal128 in ascending order",
    ),
    StageTestCase(
        "desc_decimal128",
        docs=[{"_id": 1, "v": Decimal128("10")}, {"_id": 2, "v": Decimal128("20")}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": Decimal128("20")}, {"_id": 1, "v": Decimal128("10")}],
        msg="$sort with order -1 should sort Decimal128 in descending order",
    ),
    StageTestCase(
        "asc_string",
        docs=[{"_id": 1, "v": "apple"}, {"_id": 2, "v": "banana"}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": "apple"}, {"_id": 2, "v": "banana"}],
        msg="$sort with order 1 should sort strings in ascending order",
    ),
    StageTestCase(
        "desc_string",
        docs=[{"_id": 1, "v": "apple"}, {"_id": 2, "v": "banana"}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": "banana"}, {"_id": 1, "v": "apple"}],
        msg="$sort with order -1 should sort strings in descending order",
    ),
    StageTestCase(
        "asc_objectid",
        docs=[
            {"_id": 1, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 2, "v": ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 1, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 2, "v": ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")},
        ],
        msg="$sort with order 1 should sort ObjectId in ascending order",
    ),
    StageTestCase(
        "desc_objectid",
        docs=[
            {"_id": 1, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 2, "v": ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")},
        ],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[
            {"_id": 2, "v": ObjectId("bbbbbbbbbbbbbbbbbbbbbbbb")},
            {"_id": 1, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
        ],
        msg="$sort with order -1 should sort ObjectId in descending order",
    ),
    StageTestCase(
        "asc_boolean",
        docs=[{"_id": 1, "v": False}, {"_id": 2, "v": True}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": False}, {"_id": 2, "v": True}],
        msg="$sort with order 1 should sort booleans in ascending order",
    ),
    StageTestCase(
        "desc_boolean",
        docs=[{"_id": 1, "v": False}, {"_id": 2, "v": True}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": True}, {"_id": 1, "v": False}],
        msg="$sort with order -1 should sort booleans in descending order",
    ),
    StageTestCase(
        "asc_datetime",
        docs=[
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "v": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[
            {"_id": 1, "v": datetime(2024, 1, 1)},
            {"_id": 2, "v": datetime(2025, 1, 1)},
        ],
        msg="$sort with order 1 should sort datetimes in ascending order",
    ),
    StageTestCase(
        "desc_datetime",
        docs=[
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "v": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[
            {"_id": 2, "v": datetime(2025, 1, 1)},
            {"_id": 1, "v": datetime(2024, 1, 1)},
        ],
        msg="$sort with order -1 should sort datetimes in descending order",
    ),
    StageTestCase(
        "asc_timestamp",
        docs=[{"_id": 1, "v": Timestamp(100, 1)}, {"_id": 2, "v": Timestamp(200, 1)}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": Timestamp(100, 1)}, {"_id": 2, "v": Timestamp(200, 1)}],
        msg="$sort with order 1 should sort timestamps in ascending order",
    ),
    StageTestCase(
        "desc_timestamp",
        docs=[{"_id": 1, "v": Timestamp(100, 1)}, {"_id": 2, "v": Timestamp(200, 1)}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": Timestamp(200, 1)}, {"_id": 1, "v": Timestamp(100, 1)}],
        msg="$sort with order -1 should sort timestamps in descending order",
    ),
    StageTestCase(
        "asc_embedded_doc",
        docs=[{"_id": 1, "v": {"a": 1}}, {"_id": 2, "v": {"a": 2}}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": {"a": 1}}, {"_id": 2, "v": {"a": 2}}],
        msg="$sort with order 1 should sort embedded documents in ascending order",
    ),
    StageTestCase(
        "desc_embedded_doc",
        docs=[{"_id": 1, "v": {"a": 1}}, {"_id": 2, "v": {"a": 2}}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": {"a": 2}}, {"_id": 1, "v": {"a": 1}}],
        msg="$sort with order -1 should sort embedded documents in descending order",
    ),
    StageTestCase(
        "asc_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01")}, {"_id": 2, "v": Binary(b"\x02")}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": b"\x01"}, {"_id": 2, "v": b"\x02"}],
        msg="$sort with order 1 should sort binary in ascending order",
    ),
    StageTestCase(
        "desc_binary",
        docs=[{"_id": 1, "v": Binary(b"\x01")}, {"_id": 2, "v": Binary(b"\x02")}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": b"\x02"}, {"_id": 1, "v": b"\x01"}],
        msg="$sort with order -1 should sort binary in descending order",
    ),
    StageTestCase(
        "asc_regex",
        docs=[{"_id": 1, "v": Regex("a")}, {"_id": 2, "v": Regex("b")}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": Regex("a")}, {"_id": 2, "v": Regex("b")}],
        msg="$sort with order 1 should sort regex in ascending order",
    ),
    StageTestCase(
        "desc_regex",
        docs=[{"_id": 1, "v": Regex("a")}, {"_id": 2, "v": Regex("b")}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": Regex("b")}, {"_id": 1, "v": Regex("a")}],
        msg="$sort with order -1 should sort regex in descending order",
    ),
    StageTestCase(
        "asc_code",
        docs=[{"_id": 1, "v": Code("a")}, {"_id": 2, "v": Code("b")}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": Code("a")}, {"_id": 2, "v": Code("b")}],
        msg="$sort with order 1 should sort code in ascending order",
    ),
    StageTestCase(
        "desc_code",
        docs=[{"_id": 1, "v": Code("a")}, {"_id": 2, "v": Code("b")}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": Code("b")}, {"_id": 1, "v": Code("a")}],
        msg="$sort with order -1 should sort code in descending order",
    ),
    StageTestCase(
        "asc_codewithscope",
        docs=[{"_id": 1, "v": Code("a", {})}, {"_id": 2, "v": Code("b", {})}],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[{"_id": 1, "v": Code("a", {})}, {"_id": 2, "v": Code("b", {})}],
        msg="$sort with order 1 should sort code with scope in ascending order",
    ),
    StageTestCase(
        "desc_codewithscope",
        docs=[{"_id": 1, "v": Code("a", {})}, {"_id": 2, "v": Code("b", {})}],
        pipeline=[{"$sort": {"v": -1}}],
        expected=[{"_id": 2, "v": Code("b", {})}, {"_id": 1, "v": Code("a", {})}],
        msg="$sort with order -1 should sort code with scope in descending order",
    ),
]

# Property [Equal Value Sort]: sorting documents with identical sort-field
# values succeeds without error for every BSON type, with _id as tiebreaker.
SORT_EQUAL_VALUE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "equal_null",
        docs=[{"_id": 2, "v": None}, {"_id": 1, "v": None}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": None}, {"_id": 2, "v": None}],
        msg="$sort should handle equal null values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_int",
        docs=[{"_id": 2, "v": 5}, {"_id": 1, "v": 5}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": 5}, {"_id": 2, "v": 5}],
        msg="$sort should handle equal int32 values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_int64",
        docs=[{"_id": 2, "v": Int64(5)}, {"_id": 1, "v": Int64(5)}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": Int64(5)}, {"_id": 2, "v": Int64(5)}],
        msg="$sort should handle equal Int64 values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_double",
        docs=[{"_id": 2, "v": 1.5}, {"_id": 1, "v": 1.5}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": 1.5}, {"_id": 2, "v": 1.5}],
        msg="$sort should handle equal double values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_decimal128",
        docs=[{"_id": 2, "v": Decimal128("5")}, {"_id": 1, "v": Decimal128("5")}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": Decimal128("5")}, {"_id": 2, "v": Decimal128("5")}],
        msg="$sort should handle equal Decimal128 values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_string",
        docs=[{"_id": 2, "v": "abc"}, {"_id": 1, "v": "abc"}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": "abc"}, {"_id": 2, "v": "abc"}],
        msg="$sort should handle equal string values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_objectid",
        docs=[
            {"_id": 2, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 1, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
            {"_id": 2, "v": ObjectId("aaaaaaaaaaaaaaaaaaaaaaaa")},
        ],
        msg="$sort should handle equal ObjectId values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_boolean",
        docs=[{"_id": 2, "v": True}, {"_id": 1, "v": True}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": True}, {"_id": 2, "v": True}],
        msg="$sort should handle equal boolean values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_datetime",
        docs=[
            {"_id": 2, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": datetime(2024, 1, 1)},
            {"_id": 2, "v": datetime(2024, 1, 1)},
        ],
        msg="$sort should handle equal datetime values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_timestamp",
        docs=[{"_id": 2, "v": Timestamp(100, 1)}, {"_id": 1, "v": Timestamp(100, 1)}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": Timestamp(100, 1)}, {"_id": 2, "v": Timestamp(100, 1)}],
        msg="$sort should handle equal Timestamp values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_embedded_doc",
        docs=[{"_id": 2, "v": {"a": 1}}, {"_id": 1, "v": {"a": 1}}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": {"a": 1}}, {"_id": 2, "v": {"a": 1}}],
        msg="$sort should handle equal embedded document values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_binary",
        docs=[{"_id": 2, "v": Binary(b"\x01")}, {"_id": 1, "v": Binary(b"\x01")}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": b"\x01"}, {"_id": 2, "v": b"\x01"}],
        msg="$sort should handle equal Binary values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_regex",
        docs=[{"_id": 2, "v": Regex("a")}, {"_id": 1, "v": Regex("a")}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": Regex("a")}, {"_id": 2, "v": Regex("a")}],
        msg="$sort should handle equal Regex values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_code",
        docs=[{"_id": 2, "v": Code("f")}, {"_id": 1, "v": Code("f")}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": Code("f")}, {"_id": 2, "v": Code("f")}],
        msg="$sort should handle equal Code values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_codewithscope",
        docs=[{"_id": 2, "v": Code("f", {})}, {"_id": 1, "v": Code("f", {})}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": Code("f", {})}, {"_id": 2, "v": Code("f", {})}],
        msg="$sort should handle equal CodeWithScope values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_minkey",
        docs=[{"_id": 2, "v": MinKey()}, {"_id": 1, "v": MinKey()}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": MinKey()}, {"_id": 2, "v": MinKey()}],
        msg="$sort should handle equal MinKey values with _id tiebreaker",
    ),
    StageTestCase(
        "equal_maxkey",
        docs=[{"_id": 2, "v": MaxKey()}, {"_id": 1, "v": MaxKey()}],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[{"_id": 1, "v": MaxKey()}, {"_id": 2, "v": MaxKey()}],
        msg="$sort should handle equal MaxKey values with _id tiebreaker",
    ),
]

# Property [Non-Existent Collection]: sorting a collection that does not exist
# returns an empty result set without error.
SORT_NONEXISTENT_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nonexistent_collection",
        docs=None,
        pipeline=[{"$sort": {"v": 1}}],
        expected=[],
        msg="$sort on a non-existent collection should return empty result",
    ),
]

# Property [Empty Collection]: sorting a collection with no documents returns
# an empty result set without error.
SORT_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "empty_collection",
        docs=[],
        pipeline=[{"$sort": {"v": 1}}],
        expected=[],
        msg="$sort on an empty collection should return empty result",
    ),
]

SORT_BASIC_ORDERING_TESTS = (
    SORT_ASC_DESC_TESTS
    + SORT_EQUAL_VALUE_TESTS
    + SORT_NONEXISTENT_COLLECTION_TESTS
    + SORT_EMPTY_COLLECTION_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(SORT_BASIC_ORDERING_TESTS))
def test_sort_basic_ordering(collection, test_case: StageTestCase):
    """Test $sort ascending, descending, and equal-value ordering."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
