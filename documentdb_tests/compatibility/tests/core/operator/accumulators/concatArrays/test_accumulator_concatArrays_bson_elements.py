"""Tests for $concatArrays accumulator: BSON type preservation, missing field, and $$REMOVE."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Regex

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils.accumulator_test_case import (  # noqa: E501
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Element Preservation]: $concatArrays preserves all BSON types
# when they appear as array elements.
CONCATARRAYS_BSON_ELEMENT_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_int64_elements",
        docs=[
            {"_id": 1, "v": [Int64(100)]},
            {"_id": 2, "v": [Int64(200)]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Int64(100), Int64(200)]}],
        msg="$concatArrays should preserve Int64 elements",
    ),
    AccumulatorTestCase(
        "bson_double_elements",
        docs=[
            {"_id": 1, "v": [1.5]},
            {"_id": 2, "v": [2.5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1.5, 2.5]}],
        msg="$concatArrays should preserve double elements",
    ),
    AccumulatorTestCase(
        "bson_decimal128_elements",
        docs=[
            {"_id": 1, "v": [Decimal128("1.1")]},
            {"_id": 2, "v": [Decimal128("2.2")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Decimal128("1.1"), Decimal128("2.2")]}],
        msg="$concatArrays should preserve Decimal128 elements",
    ),
    AccumulatorTestCase(
        "bson_string_elements",
        docs=[
            {"_id": 1, "v": ["hello"]},
            {"_id": 2, "v": ["world"]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": ["hello", "world"]}],
        msg="$concatArrays should preserve string elements",
    ),
    AccumulatorTestCase(
        "bson_boolean_elements",
        docs=[
            {"_id": 1, "v": [True]},
            {"_id": 2, "v": [False]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [True, False]}],
        msg="$concatArrays should preserve boolean elements",
    ),
    AccumulatorTestCase(
        "bson_datetime_elements",
        docs=[
            {"_id": 1, "v": [datetime(2023, 1, 1, tzinfo=timezone.utc)]},
            {"_id": 2, "v": [datetime(2024, 6, 15, tzinfo=timezone.utc)]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    datetime(2023, 1, 1, tzinfo=timezone.utc),
                    datetime(2024, 6, 15, tzinfo=timezone.utc),
                ],
            }
        ],
        msg="$concatArrays should preserve datetime elements",
    ),
    AccumulatorTestCase(
        "bson_objectid_elements",
        docs=[
            {"_id": 1, "v": [ObjectId("000000000000000000000001")]},
            {"_id": 2, "v": [ObjectId("000000000000000000000002")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[
            {
                "_id": None,
                "result": [
                    ObjectId("000000000000000000000001"),
                    ObjectId("000000000000000000000002"),
                ],
            }
        ],
        msg="$concatArrays should preserve ObjectId elements",
    ),
    AccumulatorTestCase(
        "bson_embedded_document_elements",
        docs=[
            {"_id": 1, "v": [{"a": 1}]},
            {"_id": 2, "v": [{"b": 2}]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [{"a": 1}, {"b": 2}]}],
        msg="$concatArrays should preserve embedded document elements",
    ),
    AccumulatorTestCase(
        "bson_null_elements",
        docs=[
            {"_id": 1, "v": [None]},
            {"_id": 2, "v": [None]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [None, None]}],
        msg="$concatArrays should preserve null as array element (not error)",
    ),
    AccumulatorTestCase(
        "bson_binary_elements",
        docs=[
            {"_id": 1, "v": [Binary(b"\x01")]},
            {"_id": 2, "v": [Binary(b"\x02")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [b"\x01", b"\x02"]}],
        msg="$concatArrays should preserve Binary elements",
    ),
    AccumulatorTestCase(
        "bson_regex_elements",
        docs=[
            {"_id": 1, "v": [Regex("abc", "i")]},
            {"_id": 2, "v": [Regex("def", "")]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [Regex("abc", "i"), Regex("def", "")]}],
        msg="$concatArrays should preserve Regex elements",
    ),
    AccumulatorTestCase(
        "bson_mixed_type_elements",
        docs=[
            {"_id": 1, "v": [1, "hello", True]},
            {"_id": 2, "v": [None, 3.14]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, "hello", True, None, 3.14]}],
        msg="$concatArrays should preserve mixed BSON types in order",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_BSON_ELEMENT_TESTS))
def test_accumulator_concatArrays_bson_elements(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays BSON element type preservation."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)


# Property [Missing Field Handling]: missing fields are silently excluded from
# concatenation; when all inputs are missing, the result is an empty array.
CONCATARRAYS_MISSING_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "missing_all",
        docs=[{"_id": 1, "x": 1}, {"_id": 2, "x": 2}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when all fields are missing",
    ),
    AccumulatorTestCase(
        "missing_single",
        docs=[{"_id": 1, "x": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$concatArrays": "$v"}}}],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when the single document has missing field",
    ),
    AccumulatorTestCase(
        "missing_some_with_arrays",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "v": [3, 4]},
            {"_id": 3, "v": [5]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [3, 4, 5]}],
        msg="$concatArrays should exclude missing fields and concatenate remaining arrays",
    ),
    AccumulatorTestCase(
        "missing_among_arrays",
        docs=[
            {"_id": 1, "v": [1]},
            {"_id": 2, "x": 1},
            {"_id": 3, "v": [2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [1, 2]}],
        msg="$concatArrays should skip missing field in middle and concatenate surrounding arrays",
    ),
    AccumulatorTestCase(
        "missing_first_doc",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "v": [10, 20]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$concatArrays should handle first document having missing field",
    ),
    AccumulatorTestCase(
        "missing_last_doc",
        docs=[
            {"_id": 1, "v": [10, 20]},
            {"_id": 2, "x": 1},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [10, 20]}],
        msg="$concatArrays should handle last document having missing field",
    ),
    AccumulatorTestCase(
        "missing_many_one_array",
        docs=[
            {"_id": 1, "x": 1},
            {"_id": 2, "x": 2},
            {"_id": 3, "x": 3},
            {"_id": 4, "v": [42]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {"$group": {"_id": None, "result": {"$concatArrays": "$v"}}},
        ],
        expected=[{"_id": None, "result": [42]}],
        msg="$concatArrays should return the single array when most documents have missing field",
    ),
]

# Property [$$REMOVE Handling]: $$REMOVE via $cond is treated as missing and
# excluded from concatenation.
CONCATARRAYS_REMOVE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "remove_all",
        docs=[{"_id": 1, "v": [1]}, {"_id": 2, "v": [2]}],
        pipeline=[
            {
                "$group": {
                    "_id": None,
                    "result": {"$concatArrays": {"$cond": [False, "$v", "$$REMOVE"]}},
                }
            }
        ],
        expected=[{"_id": None, "result": []}],
        msg="$concatArrays should return empty array when all inputs are $$REMOVE",
    ),
    AccumulatorTestCase(
        "remove_some_with_arrays",
        docs=[
            {"_id": 1, "qty": 0, "v": [1, 2]},
            {"_id": 2, "qty": 5, "v": [3, 4]},
            {"_id": 3, "qty": 0, "v": [5, 6]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$concatArrays": {"$cond": [{"$gt": ["$qty", 0]}, "$v", "$$REMOVE"]}
                    },
                }
            },
        ],
        expected=[{"_id": None, "result": [3, 4]}],
        msg="$concatArrays should exclude $$REMOVE and concatenate remaining arrays",
    ),
    AccumulatorTestCase(
        "remove_preserves_duplicates",
        docs=[
            {"_id": 1, "qty": 1, "v": [1, 2]},
            {"_id": 2, "qty": 0, "v": [3, 4]},
            {"_id": 3, "qty": 1, "v": [1, 2]},
        ],
        pipeline=[
            {"$sort": {"_id": 1}},
            {
                "$group": {
                    "_id": None,
                    "result": {
                        "$concatArrays": {"$cond": [{"$gt": ["$qty", 0]}, "$v", "$$REMOVE"]}
                    },
                }
            },
        ],
        expected=[{"_id": None, "result": [1, 2, 1, 2]}],
        msg="$concatArrays should preserve duplicates when using $$REMOVE conditionally",
    ),
]

CONCATARRAYS_MISSING_AND_REMOVE_TESTS = CONCATARRAYS_MISSING_TESTS + CONCATARRAYS_REMOVE_TESTS


@pytest.mark.parametrize("test_case", pytest_params(CONCATARRAYS_MISSING_AND_REMOVE_TESTS))
def test_accumulator_concatArrays_missing(collection, test_case: AccumulatorTestCase):
    """Test $concatArrays missing field and $$REMOVE handling."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline or [], "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
