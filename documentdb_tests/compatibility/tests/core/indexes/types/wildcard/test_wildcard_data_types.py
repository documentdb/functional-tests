"""Tests for wildcard index data type handling: document structure, BSON scalar and special types,
objects, arrays, null/missing semantics, and write operations."""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


STRUCTURE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="embedded_doc_equality_unhinted",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}),
        # Whole-document equality is not served by the wildcard index; run unhinted.
        filter={"a": {"b": 1}},
        expected=[{"_id": 1, "a": {"b": 1}}],
        msg="Whole-document equality correctness",
    ),
    IndexQueryTestCase(
        id="array_equality_unhinted",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [1, 2, 3]}),
        # Whole-array equality is not served by the wildcard index; run unhinted.
        filter={"a": [1, 2]},
        expected=[{"_id": 1, "a": [1, 2]}],
        msg="Whole-array equality correctness",
    ),
    IndexQueryTestCase(
        id="empty_array_equality",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": []}, {"_id": 2, "a": [1]}, {"_id": 3, "a": 5}),
        filter={"a": []},
        hint="wc_all",
        expected=[{"_id": 1, "a": []}],
        msg="Empty array equality via wildcard",
    ),
    IndexQueryTestCase(
        id="empty_array_nested_in_object",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": []}}, {"_id": 2, "a": {"b": [1]}}),
        filter={"a.b": []},
        hint="wc_all",
        expected=[{"_id": 1, "a": {"b": []}}],
        msg="Empty array nested in object",
    ),
    IndexQueryTestCase(
        id="empty_document_equality_hinted",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {}}, {"_id": 2, "a": {"b": 1}}, {"_id": 3, "a": 5}),
        filter={"a": {}},
        hint="wc_all",
        expected=[{"_id": 1, "a": {}}],
        msg="Empty-document equality served by wildcard (documented exception)",
    ),
    IndexQueryTestCase(
        id="dedup_exists_on_embedded_object",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"x": 1, "y": 2, "z": 3}},),
        filter={"a": {"$exists": True}},
        hint="wc_all",
        expected=[{"_id": 1, "a": {"x": 1, "y": 2, "z": 3}}],
        msg="$exists on multi-leaf embedded object returns doc once (dedup)",
    ),
    IndexQueryTestCase(
        id="dedup_range_on_array_of_subdocs",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "items": [{"q": 5}, {"q": 10}, {"q": 15}]},
            {"_id": 2, "items": [{"q": 1}]},
        ),
        filter={"items.q": {"$gte": 5}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "items": [{"q": 5}, {"q": 10}, {"q": 15}]}],
        msg="Range on array-of-subdocuments returns each matching doc once (multikey dedup)",
    ),
    IndexQueryTestCase(
        id="dedup_exists_on_array_of_subdocs",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "items": [{"q": 5}, {"q": 10}, {"q": 15}]},
            {"_id": 2, "items": [{"q": 1}]},
        ),
        filter={"items.q": {"$exists": True}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[
            {"_id": 1, "items": [{"q": 5}, {"q": 10}, {"q": 15}]},
            {"_id": 2, "items": [{"q": 1}]},
        ],
        msg="$exists on array-of-subdocuments returns each matching doc once (multikey dedup)",
    ),
    IndexQueryTestCase(
        id="numeric_string_field_name",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "obj": {"0": "zero"}}, {"_id": 2, "obj": {"0": "other"}}),
        filter={"obj.0": "zero"},
        hint="wc_all",
        expected=[{"_id": 1, "obj": {"0": "zero"}}],
        msg="Numeric-string field name is queryable",
    ),
    IndexQueryTestCase(
        id="polymorphic_scalar_match",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "x": 5}, {"_id": 2, "x": {"y": 1}}, {"_id": 3, "x": [7, 8]}),
        filter={"x": 5},
        hint="wc_all",
        expected=[{"_id": 1, "x": 5}],
        msg="Scalar match on polymorphic field",
    ),
    IndexQueryTestCase(
        id="polymorphic_array_element_match",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "x": 5}, {"_id": 2, "x": {"y": 1}}, {"_id": 3, "x": [7, 8]}),
        filter={"x": 7},
        hint="wc_all",
        expected=[{"_id": 3, "x": [7, 8]}],
        msg="Array-element match on polymorphic field",
    ),
    IndexQueryTestCase(
        id="polymorphic_nested_match",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "x": 5}, {"_id": 2, "x": {"y": 1}}, {"_id": 3, "x": [7, 8]}),
        filter={"x.y": 1},
        hint="wc_all",
        expected=[{"_id": 2, "x": {"y": 1}}],
        msg="Nested match on polymorphic field",
    ),
    IndexQueryTestCase(
        id="explicit_array_index_element",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [10, 20]}, {"_id": 2, "a": [30, 40]}),
        filter={"a.0": 10},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": [10, 20]}],
        msg="Explicit array index element match",
    ),
    IndexQueryTestCase(
        id="explicit_array_index_into_object",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}),
        filter={"a.0.b": 1},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="Explicit array index into object",
    ),
    IndexQueryTestCase(
        id="numeric_prefix_path",
        indexes=({"key": {"a.0.$**": 1}, "name": "wc_a0"},),
        doc=({"_id": 1, "a": [{"b": 1}]}, {"_id": 2, "a": [{"b": 2}]}),
        filter={"a.0.b": 2},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": [{"b": 2}]}],
        msg="Numeric prefix path query correctness (scoped wildcard on a.0)",
    ),
    IndexQueryTestCase(
        id="leading_zero_index_path",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [10, 20]}, {"_id": 2, "a": [30]}),
        filter={"a.01": 10},
        expected=[],
        msg="Leading-zero index path matches no array positions",
    ),
    IndexQueryTestCase(
        id="object_inequality",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}),
        filter={"a": {"$ne": {"b": 1}}},
        sort={"_id": 1},
        expected=[{"_id": 2, "a": {"b": 2}}],
        msg="Document inequality correctness",
    ),
    IndexQueryTestCase(
        id="in_with_object_member",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}),
        filter={"a": {"$in": [{"b": 1}, 2]}},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": 2}],
        msg="$in with object member correctness",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STRUCTURE_TESTS))
def test_wildcard_document_structure(collection, test):
    """Verify wildcard index queries on embedded documents, arrays, and mixed-type fields."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter}
    if test.hint:
        cmd["hint"] = test.hint
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


NULL_MISSING_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="null_matches_null_and_missing",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 5}),
        filter={"a": None},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": None}, {"_id": 2}],
        msg="{a: null} matches null value and missing field",
    ),
    IndexQueryTestCase(
        id="exists_false_returns_missing",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 5}),
        filter={"a": {"$exists": False}},
        sort={"_id": 1},
        expected=[{"_id": 2}],
        msg="$exists:false returns docs missing the field",
    ),
    IndexQueryTestCase(
        id="exists_true_hinted",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 5}),
        filter={"a": {"$exists": True}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "a": None}, {"_id": 3, "a": 5}],
        msg="$exists:true via wildcard returns docs where field exists (incl. null)",
    ),
    IndexQueryTestCase(
        id="ne_null_hinted",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": None}, {"_id": 2}, {"_id": 3, "a": 5}),
        filter={"a": {"$ne": None}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 3, "a": 5}],
        msg="$ne null returns non-null existing values",
    ),
    IndexQueryTestCase(
        id="ne_null_on_array_field",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [1, 2]}, {"_id": 2}, {"_id": 3, "a": 5}),
        filter={"a": {"$ne": None}},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": [1, 2]}, {"_id": 3, "a": 5}],
        msg="$ne null on array field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NULL_MISSING_TESTS))
def test_wildcard_null_and_missing(collection, test):
    """Verify null and missing-field semantics with a wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "sort": test.sort}
    if test.hint:
        cmd["hint"] = test.hint
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


def test_wildcard_missing_field_not_indexed_count(collection):
    """A document missing the indexed field is not indexed; $exists:true count excludes it."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many(
        [{"_id": 1, "a": 1}, {"_id": 2, "a": None}, {"_id": 3}, {"_id": 4, "a": 3}]
    )
    result = execute_command(
        collection,
        {"count": collection.name, "query": {"a": {"$exists": True}}, "hint": "wc_all"},
    )
    assertSuccessPartial(result, {"n": 3, "ok": 1.0}, msg="Missing field not indexed")


def test_wildcard_update_hinted(collection):
    """An update hinted to the wildcard index modifies the targeted document."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    result = execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 2}, "u": {"$set": {"a": 99}}, "hint": "wc_all"}],
        },
    )
    assertSuccessPartial(
        result, {"n": 1, "nModified": 1, "ok": 1.0}, msg="Hinted update via wildcard"
    )


def test_wildcard_findandmodify_hinted(collection):
    """A findAndModify hinted to the wildcard index updates and returns the modified document."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    result = execute_command(
        collection,
        {
            "findAndModify": collection.name,
            "query": {"a": 2},
            "update": {"$set": {"a": 99}},
            "new": True,
            "hint": "wc_all",
        },
    )
    assertSuccessPartial(
        result, {"value": {"_id": 2, "a": 99}, "ok": 1.0}, msg="Hinted findAndModify via wildcard"
    )


def test_wildcard_delete_hinted(collection):
    """A delete hinted to the wildcard index removes the targeted document."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    result = execute_command(
        collection,
        {
            "delete": collection.name,
            "deletes": [{"q": {"a": 2}, "limit": 1, "hint": "wc_all"}],
        },
    )
    assertSuccessPartial(result, {"n": 1, "ok": 1.0}, msg="Hinted delete via wildcard")


def test_wildcard_dynamic_field_indexed_after_update(collection):
    """A field added by $set becomes immediately queryable via the wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_one({"_id": 1})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"newf": 7}}}]},
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"newf": 7}, "hint": "wc_all"}
    )
    assertSuccess(
        result, [{"_id": 1, "newf": 7}], msg="Newly added field is queryable via wildcard index"
    )


def test_wildcard_overwritten_nested_field_reindexed_after_update(collection):
    """Overwriting an existing nested field via $set re-indexes it under the new value: the new
    value is queryable via the wildcard index while the old value no longer matches."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_one({"_id": 1, "a": {"b": 1}})
    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": {"_id": 1}, "u": {"$set": {"a.b": 99}}}]},
    )
    # A single hinted query on the range [1, 99] proves both facts at once: only the new value
    # (99) matches and the old value (1) does not.
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"a.b": {"$in": [1, 99]}}, "hint": "wc_all"},
    )
    assertSuccess(
        result,
        [{"_id": 1, "a": {"b": 99}}],
        msg="Overwritten nested field is re-indexed: new value matches, old value does not",
    )


def test_wildcard_upsert_indexed(collection):
    """A document inserted via upsert is queryable via the wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    execute_command(
        collection,
        {
            "update": collection.name,
            "updates": [{"q": {"a": 42}, "u": {"$set": {"a": 42}}, "upsert": True}],
        },
    )
    result = execute_command(
        collection, {"find": collection.name, "filter": {"a": 42}, "hint": "wc_all"}
    )
    assertSuccess(
        result,
        [{"a": 42}],
        transform=lambda batch: [{"a": d["a"]} for d in batch],
        msg="Upserted document is queryable via wildcard index",
    )


def test_wildcard_type_undefined_not_null(collection):
    """$type 'undefined' does not match a null-valued field."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "v": None}, {"_id": 2, "v": 5}])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"v": {"$type": "undefined"}}, "hint": "wc_all"},
    )
    assertSuccess(result, [], msg="$type 'undefined' does not match null")


def test_wildcard_type_array_matches_nested_array(collection):
    """$type 'array' matches a field whose element is itself an array (nested array)."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "v": [[1, 2]]}, {"_id": 2, "v": 5}])
    result = execute_command(
        collection,
        {"find": collection.name, "filter": {"v": {"$type": "array"}}, "hint": "wc_all"},
    )
    assertSuccess(result, [{"_id": 1, "v": [[1, 2]]}], msg="$type 'array' matches nested array")


SCALAR_TYPE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="int64_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": Int64(2**53)}, {"_id": 2, "v": Int64(100)}),
        filter={"v": Int64(2**53)},
        hint="wc_all",
        expected=[{"_id": 1, "v": Int64(2**53)}],
        msg="int64 scalar is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="double_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": 3.14}, {"_id": 2, "v": 2.71}),
        filter={"v": 3.14},
        hint="wc_all",
        expected=[{"_id": 1, "v": 3.14}],
        msg="double scalar is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="decimal128_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": Decimal128("1.5")}, {"_id": 2, "v": Decimal128("2.5")}),
        filter={"v": Decimal128("1.5")},
        hint="wc_all",
        expected=[{"_id": 1, "v": Decimal128("1.5")}],
        msg="Decimal128 scalar is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="bool_true_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": True}, {"_id": 2, "v": False}),
        filter={"v": True},
        hint="wc_all",
        expected=[{"_id": 1, "v": True}],
        msg="boolean true is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="bool_false_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": True}, {"_id": 2, "v": False}),
        filter={"v": False},
        hint="wc_all",
        expected=[{"_id": 2, "v": False}],
        msg="boolean false is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="date_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
            {"_id": 2, "v": datetime(2021, 6, 15, tzinfo=timezone.utc)},
        ),
        filter={"v": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        hint="wc_all",
        expected=[{"_id": 1, "v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        msg="date scalar is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="objectid_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")},
            {"_id": 2, "v": ObjectId("507f1f77bcf86cd799439012")},
        ),
        filter={"v": ObjectId("507f1f77bcf86cd799439011")},
        hint="wc_all",
        expected=[{"_id": 1, "v": ObjectId("507f1f77bcf86cd799439011")}],
        msg="ObjectId scalar is queryable via wildcard",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SCALAR_TYPE_TESTS))
def test_wildcard_scalar_types(collection, test):
    """Verify wildcard index correctly indexes and retrieves scalar BSON types."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter, "hint": test.hint}
    )
    assertSuccess(result, test.expected, msg=test.msg)


SPECIAL_TYPE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="binary_type",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "v": Binary(b"\x01\x02\x03")},
            {"_id": 2, "v": Binary(b"\x04\x05\x06")},
        ),
        filter={"v": Binary(b"\x01\x02\x03")},
        hint="wc_all",
        expected=[{"_id": 1, "v": Binary(b"\x01\x02\x03")}],
        msg="Binary data is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="timestamp_type",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "v": Timestamp(1000, 1)},
            {"_id": 2, "v": Timestamp(2000, 1)},
        ),
        filter={"v": Timestamp(1000, 1)},
        hint="wc_all",
        expected=[{"_id": 1, "v": Timestamp(1000, 1)}],
        msg="Timestamp is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="minkey_type",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": MinKey()}, {"_id": 2, "v": 5}),
        filter={"v": MinKey()},
        hint="wc_all",
        expected=[{"_id": 1, "v": MinKey()}],
        msg="MinKey is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="maxkey_type",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "v": MaxKey()}, {"_id": 2, "v": 5}),
        filter={"v": MaxKey()},
        hint="wc_all",
        expected=[{"_id": 1, "v": MaxKey()}],
        msg="MaxKey is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="javascript_code_type",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "v": Code("function(){return 1;}")},
            {"_id": 2, "v": Code("function(){return 2;}")},
        ),
        filter={"v": Code("function(){return 1;}")},
        hint="wc_all",
        expected=[{"_id": 1, "v": Code("function(){return 1;}")}],
        msg="JavaScript Code is queryable via wildcard",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SPECIAL_TYPE_TESTS))
def test_wildcard_special_types(collection, test):
    """Verify wildcard index correctly indexes and retrieves special BSON types."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"find": collection.name, "filter": test.filter, "hint": test.hint}
    )
    assertSuccess(result, test.expected, msg=test.msg)


OBJECT_ARRAY_TYPE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="nested_object_leaf_query",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "obj": {"x": 1, "y": 2}},
            {"_id": 2, "obj": {"x": 3, "y": 4}},
        ),
        filter={"obj.x": 1},
        hint="wc_all",
        expected=[{"_id": 1, "obj": {"x": 1, "y": 2}}],
        msg="Nested object leaf field is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="deeply_nested_object",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": {"b": {"c": {"d": 10}}}},
            {"_id": 2, "a": {"b": {"c": {"d": 20}}}},
        ),
        filter={"a.b.c.d": 10},
        hint="wc_all",
        expected=[{"_id": 1, "a": {"b": {"c": {"d": 10}}}}],
        msg="Deeply nested object leaf (3+ levels) is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="array_scalar_elements",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "tags": ["red", "blue"]},
            {"_id": 2, "tags": ["green", "yellow"]},
        ),
        filter={"tags": "blue"},
        hint="wc_all",
        expected=[{"_id": 1, "tags": ["red", "blue"]}],
        msg="Array scalar element match via wildcard",
    ),
    IndexQueryTestCase(
        id="array_numeric_elements_range",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "scores": [10, 20, 30]},
            {"_id": 2, "scores": [40, 50]},
        ),
        filter={"scores": {"$gte": 25}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "scores": [10, 20, 30]}, {"_id": 2, "scores": [40, 50]}],
        msg="Array numeric elements with range query via wildcard",
    ),
    IndexQueryTestCase(
        id="array_of_objects_nested_field",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "items": [{"name": "a", "qty": 5}, {"name": "b", "qty": 10}]},
            {"_id": 2, "items": [{"name": "c", "qty": 15}]},
        ),
        filter={"items.qty": 10},
        hint="wc_all",
        expected=[{"_id": 1, "items": [{"name": "a", "qty": 5}, {"name": "b", "qty": 10}]}],
        msg="Array of objects nested field is queryable via wildcard",
    ),
    IndexQueryTestCase(
        id="mixed_type_field_int_and_string",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "v": 42},
            {"_id": 2, "v": "42"},
            {"_id": 3, "v": 42.0},
        ),
        filter={"v": "42"},
        hint="wc_all",
        expected=[{"_id": 2, "v": "42"}],
        msg="String match does not return numeric equivalent",
    ),
    IndexQueryTestCase(
        id="object_with_array_value",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "meta": {"tags": ["x", "y"], "count": 2}},
            {"_id": 2, "meta": {"tags": ["z"], "count": 1}},
        ),
        filter={"meta.tags": "x"},
        hint="wc_all",
        expected=[{"_id": 1, "meta": {"tags": ["x", "y"], "count": 2}}],
        msg="Array inside object is queryable via wildcard",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OBJECT_ARRAY_TYPE_TESTS))
def test_wildcard_object_and_array_types(collection, test):
    """Verify wildcard index correctly indexes and retrieves objects and arrays."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": test.hint}
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)
