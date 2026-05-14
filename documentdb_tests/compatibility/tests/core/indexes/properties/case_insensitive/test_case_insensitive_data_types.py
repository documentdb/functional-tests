"""Tests for case-insensitive index data type handling.

Validates all major BSON types (int, double, bool, date, array, object,
Decimal128, ObjectId, Int64, Binary, Regex, Timestamp, MinKey, MaxKey),
null/missing field handling, BSON type distinction, compound index behavior,
and queries with multiple indexes of different collation strengths.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index
_BASIC_CI_INDEX = (
    {"key": {"v": 1}, "name": "idx_ci", "collation": {"locale": "en", "strength": 2}},
)

DATA_TYPE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="int_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": 42}, {"_id": 2, "v": 100}),
        filter={"v": 42},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": 42}],
        msg="Should query int values in case-insensitive index",
    ),
    IndexQueryTestCase(
        id="double_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": 3.14}, {"_id": 2, "v": 2.71}),
        filter={"v": 3.14},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": 3.14}],
        msg="Should query double values",
    ),
    IndexQueryTestCase(
        id="bool_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": True}, {"_id": 2, "v": False}),
        filter={"v": True},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": True}],
        msg="Should query boolean values",
    ),
    IndexQueryTestCase(
        id="date_values",
        indexes=_BASIC_CI_INDEX,
        doc=(
            {"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "v": datetime(2025, 1, 1, tzinfo=timezone.utc)},
        ),
        filter={"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        msg="Should query date values",
    ),
    IndexQueryTestCase(
        id="array_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": [1, 2]}, {"_id": 2, "v": [3, 4]}),
        filter={"v": 1},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": [1, 2]}],
        msg="Should query array element values",
    ),
    IndexQueryTestCase(
        id="object_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": {"a": 1}}, {"_id": 2, "v": {"a": 2}}),
        filter={"v": {"a": 1}},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": {"a": 1}}],
        msg="Should query embedded object values",
    ),
    IndexQueryTestCase(
        id="decimal128_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": Decimal128("1.5")}, {"_id": 2, "v": Decimal128("2.5")}),
        filter={"v": Decimal128("1.5")},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": Decimal128("1.5")}],
        msg="Should query Decimal128 values",
    ),
    IndexQueryTestCase(
        id="objectid_values",
        indexes=_BASIC_CI_INDEX,
        doc=(
            {"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "v": ObjectId("507f1f77bcf86cd799439012")},
        ),
        filter={"v": ObjectId("507f1f77bcf86cd799439011")},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        msg="Should query ObjectId values",
    ),
    IndexQueryTestCase(
        id="int64_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": Int64(2**53)}, {"_id": 2, "v": Int64(2**53 + 1)}),
        filter={"v": Int64(2**53)},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": Int64(2**53)}],
        msg="Should query Int64 values",
    ),
    IndexQueryTestCase(
        id="binary_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": Binary(b"\x01\x02")}, {"_id": 2, "v": Binary(b"\x03\x04")}),
        filter={"v": Binary(b"\x01\x02")},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": b"\x01\x02"}],
        msg="Should query Binary values",
    ),
    IndexQueryTestCase(
        id="regex_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": Regex("^hello")}, {"_id": 2, "v": Regex("^world")}),
        filter={"v": Regex("^hello")},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": Regex("^hello")}],
        msg="Should query Regex values",
    ),
    IndexQueryTestCase(
        id="timestamp_values",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": Timestamp(1000, 1)}, {"_id": 2, "v": Timestamp(2000, 1)}),
        filter={"v": Timestamp(1000, 1)},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": Timestamp(1000, 1)}],
        msg="Should query Timestamp values",
    ),
    IndexQueryTestCase(
        id="minkey_value",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": MinKey()}, {"_id": 2, "v": "hello"}),
        filter={"v": MinKey()},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": MinKey()}],
        msg="Should query MinKey values",
    ),
    IndexQueryTestCase(
        id="maxkey_value",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": MaxKey()}, {"_id": 2, "v": "hello"}),
        filter={"v": MaxKey()},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": MaxKey()}],
        msg="Should query MaxKey values",
    ),
    IndexQueryTestCase(
        id="null_value",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": None}, {"_id": 2, "v": "hello"}),
        filter={"v": None},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": None}],
        msg="Should query null values",
    ),
    IndexQueryTestCase(
        id="missing_field",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "other": 1}, {"_id": 2, "v": "hello"}),
        filter={"v": None},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "other": 1}],
        msg="Should match documents with missing field as null",
    ),
    IndexQueryTestCase(
        id="null_and_missing_equivalent",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": None}, {"_id": 2, "other": 1}, {"_id": 3, "v": "x"}),
        filter={"v": None},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[{"_id": 1, "v": None}, {"_id": 2, "other": 1}],
        msg="Should treat null and missing as equivalent",
    ),
    IndexQueryTestCase(
        id="string_null_vs_bson_null",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": "null"}, {"_id": 2, "v": None}),
        filter={"v": "null"},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": "null"}],
        msg="String 'null' should be distinct from BSON null",
    ),
    IndexQueryTestCase(
        id="string_true_vs_bool_true",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": "true"}, {"_id": 2, "v": True}),
        filter={"v": "true"},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": "true"}],
        msg="String 'true' should be distinct from boolean true",
    ),
    IndexQueryTestCase(
        id="string_1_vs_int_1",
        indexes=_BASIC_CI_INDEX,
        doc=({"_id": 1, "v": "1"}, {"_id": 2, "v": 1}),
        filter={"v": "1"},
        collation={"locale": "en", "strength": 2},
        expected=[{"_id": 1, "v": "1"}],
        msg="String '1' should be distinct from integer 1",
    ),
    IndexQueryTestCase(
        id="compound_both_fields",
        indexes=(
            {
                "key": {"a": 1, "b": 1},
                "name": "idx_ci_compound",
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        doc=(
            {"_id": 1, "a": "Hello", "b": "World"},
            {"_id": 2, "a": "hello", "b": "world"},
            {"_id": 3, "a": "Hello", "b": "other"},
        ),
        filter={"a": "HELLO", "b": "WORLD"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "a": "Hello", "b": "World"},
            {"_id": 2, "a": "hello", "b": "world"},
        ],
        msg="Should match both fields case-insensitively",
    ),
    IndexQueryTestCase(
        id="compound_sort",
        indexes=(
            {
                "key": {"a": 1, "b": 1},
                "name": "idx_ci_compound",
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        doc=(
            {"_id": 1, "a": "Banana", "b": "x"},
            {"_id": 2, "a": "apple", "b": "y"},
            {"_id": 3, "a": "Cherry", "b": "z"},
        ),
        filter={},
        collation={"locale": "en", "strength": 2},
        sort={"a": 1, "b": 1},
        expected=[
            {"_id": 2, "a": "apple", "b": "y"},
            {"_id": 1, "a": "Banana", "b": "x"},
            {"_id": 3, "a": "Cherry", "b": "z"},
        ],
        msg="Should sort compound fields case-insensitively",
    ),
    IndexQueryTestCase(
        id="compound_prefix_only",
        indexes=(
            {
                "key": {"a": 1, "b": 1},
                "name": "idx_ci_compound",
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        doc=(
            {"_id": 1, "a": "Hello", "b": "x"},
            {"_id": 2, "a": "hello", "b": "y"},
            {"_id": 3, "a": "other", "b": "z"},
        ),
        filter={"a": "HELLO"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "a": "Hello", "b": "x"},
            {"_id": 2, "a": "hello", "b": "y"},
        ],
        msg="Should use compound index for prefix field query",
    ),
    IndexQueryTestCase(
        id="multi_index_strength_1_matches_all",
        indexes=(
            {"key": {"v": 1}, "name": "idx_s1", "collation": {"locale": "en", "strength": 1}},
            {"key": {"v": 1}, "name": "idx_s2", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "café"},
            {"_id": 3, "v": "CAFE"},
        ),
        filter={"v": "cafe"},
        collation={"locale": "en", "strength": 1},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "café"},
            {"_id": 3, "v": "CAFE"},
        ],
        msg="Strength 1 query should match all variants",
    ),
    IndexQueryTestCase(
        id="multi_index_strength_2_matches_case_only",
        indexes=(
            {"key": {"v": 1}, "name": "idx_s1", "collation": {"locale": "en", "strength": 1}},
            {"key": {"v": 1}, "name": "idx_s2", "collation": {"locale": "en", "strength": 2}},
        ),
        doc=(
            {"_id": 1, "v": "cafe"},
            {"_id": 2, "v": "café"},
            {"_id": 3, "v": "CAFE"},
        ),
        filter={"v": "cafe"},
        collation={"locale": "en", "strength": 2},
        sort={"_id": 1},
        expected=[
            {"_id": 1, "v": "cafe"},
            {"_id": 3, "v": "CAFE"},
        ],
        msg="Strength 2 query should match case variants but not accented",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DATA_TYPE_TESTS))
def test_case_insensitive_data_types(collection, test):
    """Test data type handling with case-insensitive indexes."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter, "collation": test.collation}
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


def test_case_insensitive_two_indexes_different_strengths(collection):
    """Test two indexes on same key with different collation strengths coexist."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"v": 1}, "name": "idx_s1", "collation": {"locale": "en", "strength": 1}}
            ],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"v": 1}, "name": "idx_s2", "collation": {"locale": "en", "strength": 2}}
            ],
        },
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "numIndexesAfter": 3},
        msg="Should create second index with different strength",
    )
