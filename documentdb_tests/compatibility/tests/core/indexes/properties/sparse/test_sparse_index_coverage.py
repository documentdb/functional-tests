"""Tests for sparse index coverage — document inclusion/exclusion."""

import pytest
from bson import Binary

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

SPARSE_COVERAGE_COUNT_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="excludes_missing_field",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": None}, {"_id": 3}),
        expected={"n": 2, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Sparse index excludes documents where indexed field is missing",
    ),
    IndexTestCase(
        id="null_is_indexed",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=({"_id": 1, "a": None}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Document with field set to null IS indexed (field exists)",
    ),
    IndexTestCase(
        id="nonsparse_includes_all",
        indexes=({"key": {"a": 1}, "name": "idx_nonsparse"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2}, {"_id": 3, "a": None}),
        expected={"n": 3, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Non-sparse index includes ALL documents including missing field",
    ),
    IndexTestCase(
        id="nested_empty_parent_excluded",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_sparse", "sparse": True},),
        doc=({"_id": 1, "a": {}}, {"_id": 2, "a": {"b": 1}}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a.b": 1}},
        msg="Sparse index on 'a.b' — document {a: {}} is missing 'a.b' → excluded",
    ),
    IndexTestCase(
        id="nested_null_value_included",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_sparse", "sparse": True},),
        doc=({"_id": 1, "a": {"b": None}}, {"_id": 2, "a": {}}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a.b": 1}},
        msg="Sparse index on 'a.b' — document {a: {b: null}} → included",
    ),
    IndexTestCase(
        id="nested_parent_null_excluded",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_sparse", "sparse": True},),
        doc=({"_id": 1, "a": None}, {"_id": 2, "a": {"b": 1}}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a.b": 1}},
        msg="Sparse index on 'a.b' — document {a: null} → excluded (can't traverse)",
    ),
    IndexTestCase(
        id="nested_array_multikey",
        indexes=({"key": {"a.b": 1}, "name": "idx_nested_sparse", "sparse": True},),
        doc=({"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a.b": 1}},
        msg="Sparse index on 'a.b' — document {a: [{b: 1}, {b: 2}]} → multikey behavior",
    ),
    IndexTestCase(
        id="array_empty_indexed",
        indexes=({"key": {"a": 1}, "name": "idx_arr_sparse", "sparse": True},),
        doc=({"_id": 1, "a": []}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Sparse index on array field — document with empty array [] — field exists, so indexed",
    ),
    IndexTestCase(
        id="compound_missing_all_fields_excluded",
        indexes=({"key": {"a": 1, "b": -1}, "name": "idx_compound_sparse", "sparse": True},),
        doc=({"_id": 1, "a": 1, "b": 2}, {"_id": 2, "c": 3}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a": 1, "b": -1}},
        msg="Sparse compound index — document missing all indexed fields is NOT indexed",
    ),
    IndexTestCase(
        id="compound_one_field_present_included",
        indexes=({"key": {"a": 1, "b": -1}, "name": "idx_compound_sparse", "sparse": True},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "b": 2}, {"_id": 3}),
        expected={"n": 2, "ok": 1.0},
        command_options={"hint": {"a": 1, "b": -1}},
        msg="Sparse compound index — document with one field present IS indexed",
    ),
    IndexTestCase(
        id="compound_geospatial",
        indexes=(
            {
                "key": {"loc": "2dsphere", "name": 1},
                "name": "idx_geo_compound_sparse",
                "sparse": True,
            },
        ),
        doc=(
            {"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}, "name": "A"},
            {"_id": 2, "name": "B"},
        ),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": "idx_geo_compound_sparse"},
        msg="Sparse compound index with geospatial field — only indexes docs with geo field",
    ),
    IndexTestCase(
        id="2dsphere_skips_missing_geo",
        indexes=({"key": {"loc": "2dsphere"}, "name": "idx_2dsphere"},),
        doc=({"_id": 1, "loc": {"type": "Point", "coordinates": [0, 0]}}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"loc": "2dsphere"}},
        msg="2dsphere index is always sparse — skips docs without geo field",
    ),
    IndexTestCase(
        id="2d_skips_missing_geo",
        indexes=({"key": {"loc": "2d"}, "name": "idx_2d"},),
        doc=({"_id": 1, "loc": [1, 2]}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"loc": "2d"}},
        msg="2d index is always sparse — skips docs without geo field",
    ),
    IndexTestCase(
        id="bson_object_indexed",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=({"_id": 1, "a": {"x": 1}}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Sparse index includes document with embedded object value",
    ),
    IndexTestCase(
        id="bson_array_indexed",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=({"_id": 1, "a": [1, 2, 3]}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Sparse index includes document with array value",
    ),
    IndexTestCase(
        id="bson_bindata_indexed",
        indexes=({"key": {"a": 1}, "name": "idx_sparse", "sparse": True},),
        doc=({"_id": 1, "a": Binary(b"\x01\x02\x03")}, {"_id": 2}),
        expected={"n": 1, "ok": 1.0},
        command_options={"hint": {"a": 1}},
        msg="Sparse index includes document with binary data value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPARSE_COVERAGE_COUNT_TESTS))
def test_sparse_coverage_count(collection, test):
    """Test sparse index document inclusion/exclusion via count."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"count": collection.name, "query": {}, "hint": test.command_options["hint"]},
    )
    assertSuccess(result, test.expected, raw_res=True)


def test_sparse_text_skips_missing_text(collection):
    """Test text index is always sparse — skips docs without text field."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"content": "text"}, "name": "idx_text"}],
        },
    )
    collection.insert_many(
        [
            {"_id": 1, "content": "hello world"},
            {"_id": 2},
            {"_id": 3, "content": "test"},
        ]
    )
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"$text": {"$search": "hello"}}, "sort": {"_id": 1}},
    )
    assertSuccess(result, [{"_id": 1, "content": "hello world"}])


def test_sparse_exists_false_not_affected(collection):
    """Test $exists:false returns correct count even with sparse index present."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_sparse", "sparse": True}],
        },
    )
    collection.insert_many(
        [{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3}, {"_id": 4, "a": None}]
    )
    result = execute_command(
        collection, {"count": collection.name, "query": {"a": {"$exists": False}}}
    )
    assertSuccess(result, {"n": 1, "ok": 1.0}, raw_res=True)


def test_sparse_agg_sort_returns_all_docs(collection):
    """Test $sort in aggregation returns all documents regardless of sparse index."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"a": 1}, "name": "idx_sparse", "sparse": True}],
        },
    )
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3}, {"_id": 4, "a": 3}])
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$sort": {"a": 1}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
    )
    assertSuccess(result, [{"_id": 3}, {"_id": 1}, {"_id": 2}, {"_id": 4}])
