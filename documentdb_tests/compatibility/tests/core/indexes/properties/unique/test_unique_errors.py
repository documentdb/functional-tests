"""Tests for unique index error cases.

Validates DuplicateKey error responses when inserting documents that
violate unique index constraints across various BSON types, numeric
equivalences, null/missing fields, compound/multikey indexes, sparse
and partial indexes, nested paths, collation settings, batch insert
behavior, and index rebuild failures.
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertFailureCode, assertSuccessPartial
from documentdb_tests.framework.error_codes import DUPLICATE_KEY_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DECIMAL128_NAN,
    DECIMAL128_NEGATIVE_ZERO,
    DOUBLE_NEGATIVE_ZERO,
    FLOAT_NAN,
)

pytestmark = pytest.mark.index


_BASIC_UNIQUE_INDEX = ({"key": {"v": 1}, "name": "idx_unique", "unique": True},)


CONSTRAINT_ERROR_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="dup_int",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 1},),
        invalid_input={"v": 1},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_int",
    ),
    IndexTestCase(
        id="dup_long",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": Int64(1)},),
        invalid_input={"v": Int64(1)},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_long",
    ),
    IndexTestCase(
        id="dup_double",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 1.5},),
        invalid_input={"v": 1.5},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_double",
    ),
    IndexTestCase(
        id="dup_decimal128",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": Decimal128("2.5")},),
        invalid_input={"v": Decimal128("2.5")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_decimal128",
    ),
    IndexTestCase(
        id="dup_string",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": "hello"},),
        invalid_input={"v": "hello"},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_string",
    ),
    IndexTestCase(
        id="dup_bool_true",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": True},),
        invalid_input={"v": True},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_bool_true",
    ),
    IndexTestCase(
        id="dup_bool_false",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": False},),
        invalid_input={"v": False},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_bool_false",
    ),
    IndexTestCase(
        id="dup_date",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},),
        invalid_input={"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_date",
    ),
    IndexTestCase(
        id="dup_objectid",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": ObjectId("000000000000000000000001")},),
        invalid_input={"v": ObjectId("000000000000000000000001")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_objectid",
    ),
    IndexTestCase(
        id="dup_array",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": [1, 2]},),
        invalid_input={"v": [1, 2]},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_array",
    ),
    IndexTestCase(
        id="dup_object",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": {"a": 1}},),
        invalid_input={"v": {"a": 1}},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_object",
    ),
    IndexTestCase(
        id="dup_bindata",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": Binary(b"\x01\x02")},),
        invalid_input={"v": Binary(b"\x01\x02")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_bindata",
    ),
    IndexTestCase(
        id="dup_regex",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": Regex("^abc", "i")},),
        invalid_input={"v": Regex("^abc", "i")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_regex",
    ),
    IndexTestCase(
        id="dup_timestamp",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": Timestamp(1, 1)},),
        invalid_input={"v": Timestamp(1, 1)},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_timestamp",
    ),
    IndexTestCase(
        id="dup_minkey",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": MinKey()},),
        invalid_input={"v": MinKey()},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_minkey",
    ),
    IndexTestCase(
        id="dup_maxkey",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": MaxKey()},),
        invalid_input={"v": MaxKey()},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate dup_maxkey",
    ),
    IndexTestCase(
        id="one_int_eq_long",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 1},),
        invalid_input={"v": Int64(1)},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Int64(1) as duplicate of 1",
    ),
    IndexTestCase(
        id="one_int_eq_double",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 1},),
        invalid_input={"v": 1.0},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat 1.0 as duplicate of 1",
    ),
    IndexTestCase(
        id="one_int_eq_decimal128",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 1},),
        invalid_input={"v": Decimal128("1")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Decimal128('1') as duplicate of 1",
    ),
    IndexTestCase(
        id="zero_int_eq_long",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 0},),
        invalid_input={"v": Int64(0)},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Int64(0) as duplicate of 0",
    ),
    IndexTestCase(
        id="zero_int_eq_double",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 0},),
        invalid_input={"v": 0.0},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat 0.0 as duplicate of 0",
    ),
    IndexTestCase(
        id="zero_int_eq_decimal128",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": 0},),
        invalid_input={"v": Decimal128("0")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Decimal128('0') as duplicate of 0",
    ),
    IndexTestCase(
        id="negative_zero_vs_positive_zero",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": 0.0},),
        invalid_input={"v": DOUBLE_NEGATIVE_ZERO},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat -0.0 as duplicate of 0.0",
    ),
    IndexTestCase(
        id="decimal128_negative_zero_vs_zero",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": Decimal128("0")},),
        invalid_input={"v": DECIMAL128_NEGATIVE_ZERO},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Decimal128(-0) as duplicate of Decimal128(0)",
    ),
    IndexTestCase(
        id="decimal128_trailing_zeros",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": Decimal128("1.0")},),
        invalid_input={"v": Decimal128("1.00")},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Decimal128 1.0 and 1.00 as same",
    ),
    IndexTestCase(
        id="nan_duplicate",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": FLOAT_NAN},),
        invalid_input={"v": FLOAT_NAN},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat NaN as duplicate of NaN",
    ),
    IndexTestCase(
        id="decimal128_nan_duplicate",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": DECIMAL128_NAN},),
        invalid_input={"v": DECIMAL128_NAN},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat Decimal128 NaN as duplicate",
    ),
    IndexTestCase(
        id="null_and_missing_are_same",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": None},),
        invalid_input={"other": 1},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat missing field as duplicate of null",
    ),
    IndexTestCase(
        id="compound_same_combination",
        indexes=({"key": {"a": 1, "b": 1}, "name": "idx_unique", "unique": True},),
        doc=({"a": 1, "b": 1},),
        invalid_input={"a": 1, "b": 1},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject same combination",
    ),
    IndexTestCase(
        id="multikey_overlapping_arrays",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": [1, 2, 3]},),
        invalid_input={"v": [3, 4, 5]},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject overlapping array elements",
    ),
    IndexTestCase(
        id="multikey_array_vs_scalar",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": [1, 2, 3]},),
        invalid_input={"v": 2},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject scalar matching array element",
    ),
    IndexTestCase(
        id="empty_string_duplicate",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": ""},),
        invalid_input={"v": ""},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate empty string",
    ),
    IndexTestCase(
        id="empty_object_duplicate",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": {}},),
        invalid_input={"v": {}},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate empty object",
    ),
    IndexTestCase(
        id="dup_empty_array",
        indexes=_BASIC_UNIQUE_INDEX,
        doc=({"v": []},),
        invalid_input={"v": []},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate empty array",
    ),
    IndexTestCase(
        id="sparse_unique_rejects_duplicate",
        indexes=({"key": {"v": 1}, "name": "idx_sparse_unique", "unique": True, "sparse": True},),
        doc=({"v": 1},),
        invalid_input={"v": 1},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate in sparse unique",
    ),
    IndexTestCase(
        id="sparse_unique_null_only_one",
        indexes=({"key": {"v": 1}, "name": "idx_sparse_unique", "unique": True, "sparse": True},),
        doc=({"v": None},),
        invalid_input={"v": None},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject second null in sparse unique",
    ),
    IndexTestCase(
        id="partial_unique_matching_rejects",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_partial_unique",
                "unique": True,
                "partialFilterExpression": {"status": "active"},
            },
        ),
        doc=({"v": 1, "status": "active"},),
        invalid_input={"v": 1, "status": "active"},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate among matching docs",
    ),
    IndexTestCase(
        id="nested_duplicate",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_unique", "unique": True},),
        doc=({"a": {"b": 1}},),
        invalid_input={"a": {"b": 1}},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate nested value",
    ),
    IndexTestCase(
        id="nested_multikey_array_of_objects",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_unique", "unique": True},),
        doc=({"a": [{"b": 1}, {"b": 2}]},),
        invalid_input={"a": {"b": 1}},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject value matching multikey entry",
    ),
    IndexTestCase(
        id="nested_missing_parent_null_vs_empty",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_unique", "unique": True},),
        doc=({"a": None},),
        invalid_input={"a": {}},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat both as missing a.b (null)",
    ),
    IndexTestCase(
        id="deep_nested_path",
        indexes=({"key": {"a.b.c": 1}, "name": "idx_nested_unique", "unique": True},),
        doc=({"a": {"b": {"c": 1}}},),
        invalid_input={"a": {"b": {"c": 1}}},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should reject duplicate deep nested value",
    ),
    IndexTestCase(
        id="collation_strength2_case_insensitive",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_coll",
                "unique": True,
                "collation": {"locale": "en", "strength": 2},
            },
        ),
        doc=({"v": "hello"},),
        invalid_input={"v": "HELLO"},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat case-different strings as duplicates with strength:2",
    ),
    IndexTestCase(
        id="collation_strength1_accent_insensitive",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_coll",
                "unique": True,
                "collation": {"locale": "en", "strength": 1},
            },
        ),
        doc=({"v": "cafe"},),
        invalid_input={"v": "café"},
        error_code=DUPLICATE_KEY_ERROR,
        msg="Should treat accent-different strings as duplicates with strength:1",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONSTRAINT_ERROR_TESTS))
def test_unique_constraint_violation(collection, test):
    """Test unique index rejects duplicate insert."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [test.invalid_input]},
    )
    assertFailureCode(result, test.error_code, msg=test.msg)


def test_unique_ordered_batch_stops_at_first_duplicate(collection):
    """Test ordered batch insert stops at first duplicate key violation."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"v": 2}, {"v": 1}, {"v": 3}], "ordered": True},
    )
    assertSuccessPartial(
        result,
        {"ok": 1.0, "n": 1},
        msg="Ordered batch should insert only first doc before duplicate",
    )


def test_unique_ordered_batch_single_write_error(collection):
    """Test ordered batch returns one writeError at index of first duplicate."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"v": 2}, {"v": 1}, {"v": 3}], "ordered": True},
    )
    assertSuccessPartial(
        result,
        {"writeErrors": [{"index": 1, "code": DUPLICATE_KEY_ERROR}]},
    )


def test_unique_unordered_batch_continues_past_duplicates(collection):
    """Test unordered batch insert continues past duplicate key violations."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"v": 2}, {"v": 1}, {"v": 1}], "ordered": False},
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "n": 1}, msg="Unordered batch should insert non-duplicate docs"
    )


def test_unique_unordered_batch_reports_all_duplicates(collection):
    """Test unordered batch returns writeErrors for all duplicate violations."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"v": 2}, {"v": 1}, {"v": 1}], "ordered": False},
    )
    assertSuccessPartial(
        result,
        {
            "writeErrors": [
                {"index": 1, "code": DUPLICATE_KEY_ERROR},
                {"index": 2, "code": DUPLICATE_KEY_ERROR},
            ],
        },
        msg="Unordered batch should report writeErrors at indices 1 and 2",
    )


def test_unique_recreate_with_existing_duplicates_fails(collection):
    """Test recreating unique index fails when collection has duplicates."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    collection.insert_one({"v": 1})
    execute_command(collection, {"dropIndexes": collection.name, "index": "idx_unique"})
    collection.insert_one({"v": 1})
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    assertFailureCode(
        result,
        DUPLICATE_KEY_ERROR,
        msg="Should fail to create unique index with existing duplicates",
    )
