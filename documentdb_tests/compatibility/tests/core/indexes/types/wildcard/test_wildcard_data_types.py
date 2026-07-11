"""Tests for wildcard index document structure, null/missing semantics, and write operations."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


STRUCTURE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="embedded_grandchild_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": {"c": 10}}}, {"_id": 2, "a": {"b": {"c": 20}}}),
        filter={"a.b.c": 20},
        hint="wc_all",
        expected=[{"_id": 2, "a": {"b": {"c": 20}}}],
        msg="Grandchild scalar (two levels deep) matched via wildcard",
    ),
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
        id="array_element_match",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [4, 5]}),
        filter={"a": 2},
        hint="wc_all",
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="Array element match via wildcard",
    ),
    IndexQueryTestCase(
        id="array_of_objects_scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [{"b": 1}, {"b": 2}]}, {"_id": 2, "a": [{"b": 3}]}),
        filter={"a.b": 2},
        hint="wc_all",
        expected=[{"_id": 1, "a": [{"b": 1}, {"b": 2}]}],
        msg="Scalar within array of objects",
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
