"""Tests for unique index constraint enforcement — success cases.

Validates that unique indexes correctly allow distinct values across
BSON types, compound indexes, multikey indexes, sparse and partial
indexes, nested field paths, case-sensitive collation defaults, and
constraint removal after index drop.
"""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import FLOAT_INFINITY, FLOAT_NEGATIVE_INFINITY

pytestmark = pytest.mark.index


# `input` carries the doc inserted under test. `doc` holds any documents
# pre-inserted before the operation under test.

CONSTRAINT_SUCCESS_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="int_vs_string",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": 1},),
        input={"v": "1"},
        msg="Should treat int 1 and string '1' as distinct",
    ),
    IndexTestCase(
        id="null_vs_bool_false",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": None},),
        input={"v": False},
        msg="Should treat null and bool false as distinct",
    ),
    IndexTestCase(
        id="int_zero_vs_bool_false",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": 0},),
        input={"v": False},
        msg="Should treat int 0 and bool false as distinct",
    ),
    IndexTestCase(
        id="int_one_vs_bool_true",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": 1},),
        input={"v": True},
        msg="Should treat int 1 and bool true as distinct",
    ),
    IndexTestCase(
        id="empty_string_vs_null",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": ""},),
        input={"v": None},
        msg="Should treat empty string and null as distinct",
    ),
    IndexTestCase(
        id="empty_array_vs_null",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": []},),
        input={"v": None},
        msg="Should treat empty array and null as distinct",
    ),
    IndexTestCase(
        id="empty_object_vs_null",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": {}},),
        input={"v": None},
        msg="Should treat empty object and null as distinct",
    ),
    IndexTestCase(
        id="null_first",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        input={"v": None},
        msg="First document with null value should succeed",
    ),
    IndexTestCase(
        id="missing_field_first",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        input={"other": 1},
        msg="First document missing indexed field should succeed",
    ),
    IndexTestCase(
        id="compound_different_combination",
        indexes=({"key": {"a": 1, "b": 1}, "name": "idx_unique", "unique": True},),
        doc=({"a": 1, "b": 1},),
        input={"a": 1, "b": 2},
        msg="Compound unique should allow same value in one field if other differs",
    ),
    IndexTestCase(
        id="compound_null_in_one_field_different_other",
        indexes=({"key": {"a": 1, "b": 1}, "name": "idx_unique", "unique": True},),
        doc=({"a": None, "b": 1},),
        input={"a": None, "b": 2},
        msg="Compound unique should allow null in one field with different values in other",
    ),
    IndexTestCase(
        id="multikey_same_doc_duplicate_elements",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        input={"v": [1, 1, 2]},
        msg="Unique multikey should allow duplicate elements within same document",
    ),
    IndexTestCase(
        id="infinity_and_neg_infinity_distinct",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": FLOAT_INFINITY},),
        input={"v": FLOAT_NEGATIVE_INFINITY},
        msg="Should treat Infinity and -Infinity as distinct",
    ),
    IndexTestCase(
        id="sparse_unique_multiple_missing_field",
        indexes=({"key": {"v": 1}, "name": "idx_sparse_unique", "unique": True, "sparse": True},),
        doc=({"other": 1},),
        input={"other": 2},
        msg="Sparse unique should allow multiple documents missing the indexed field",
    ),
    IndexTestCase(
        id="partial_unique_non_matching_allows_duplicates",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_partial_unique",
                "unique": True,
                "partialFilterExpression": {"status": "active"},
            },
        ),
        doc=({"v": 1, "status": "inactive"},),
        input={"v": 1, "status": "inactive"},
        msg="Partial unique should allow duplicates for non-matching documents",
    ),
    IndexTestCase(
        id="partial_unique_one_matches_one_not",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_partial_unique",
                "unique": True,
                "partialFilterExpression": {"status": "active"},
            },
        ),
        doc=({"v": 1, "status": "active"},),
        input={"v": 1, "status": "inactive"},
        msg="Partial unique should allow same value when one doc matches filter and one doesn't",
    ),
    IndexTestCase(
        id="partial_unique_exists_filter_missing_exempt",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_partial_unique",
                "unique": True,
                "partialFilterExpression": {"v": {"$exists": True}},
            },
        ),
        doc=({"other": 1},),
        input={"other": 2},
        msg="Partial unique with $exists filter should exempt documents missing the field",
    ),
    IndexTestCase(
        id="partial_unique_gt_filter_below_threshold_exempt",
        indexes=(
            {
                "key": {"v": 1},
                "name": "idx_partial_unique",
                "unique": True,
                "partialFilterExpression": {"v": {"$gt": 5}},
            },
        ),
        doc=({"v": 3},),
        input={"v": 3},
        msg="Partial unique with $gt filter should exempt values below threshold",
    ),
    IndexTestCase(
        id="nested_different_values",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_unique", "unique": True},),
        doc=({"a": {"b": 1}},),
        input={"a": {"b": 2}},
        msg="Unique on 'a.b' should allow different nested values",
    ),
    IndexTestCase(
        id="no_collation_case_sensitive",
        indexes=({"key": {"v": 1}, "name": "idx_unique", "unique": True},),
        doc=({"v": "hello"},),
        input={"v": "HELLO"},
        msg="Unique without collation should treat 'hello' and 'HELLO' as distinct",
    ),
]


@pytest.mark.parametrize("test", pytest_params(CONSTRAINT_SUCCESS_TESTS))
def test_unique_constraint_success(collection, test):
    """Test unique index allows distinct insert."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    if test.doc:
        collection.insert_many(test.doc)
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [test.input]},
    )
    assertSuccessPartial(result, {"ok": 1.0, "n": 1}, msg=test.msg)


def test_unique_drop_allows_duplicates(collection):
    """Test dropping unique index removes constraint so duplicates can be inserted."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"v": 1}, "name": "idx_unique", "unique": True}],
        },
    )
    collection.insert_one({"v": 1})
    execute_command(collection, {"dropIndexes": collection.name, "index": "idx_unique"})
    result = execute_command(
        collection,
        {"insert": collection.name, "documents": [{"v": 1}]},
    )
    assertSuccessPartial(
        result, {"ok": 1.0, "n": 1}, msg="Should allow duplicate after dropping unique index"
    )
