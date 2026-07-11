"""Tests for wildcard index creation, management, and projection."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
    IndexTestCase,
)
from documentdb_tests.framework.assertions import (
    assertFailureCode,
    assertSuccess,
    assertSuccessPartial,
)
from documentdb_tests.framework.error_codes import INDEX_KEY_SPECS_CONFLICT_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index


VALID_PROJECTION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="include_single_field",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": 1}},),
        msg="Inclusion projection of one field should succeed",
    ),
    IndexTestCase(
        id="exclude_single_field",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": 0}},),
        msg="Exclusion projection of one field should succeed",
    ),
    IndexTestCase(
        id="include_multiple_fields",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": 1, "b": 1}},),
        msg="Inclusion projection of multiple fields should succeed",
    ),
    IndexTestCase(
        id="exclude_multiple_fields",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": 0, "b": 0}},),
        msg="Exclusion projection of multiple fields should succeed",
    ),
    IndexTestCase(
        id="exclude_id_in_inclusion",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"_id": 0, "a": 1}},),
        msg="Excluding _id in an inclusion projection should succeed (_id exception)",
    ),
    IndexTestCase(
        id="include_id_in_exclusion",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"_id": 1, "a": 0}},),
        msg="Including _id in an exclusion projection should succeed (_id exception)",
    ),
    IndexTestCase(
        id="include_dotted_path",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a.b": 1}},),
        msg="Inclusion projection of a dotted path should succeed",
    ),
    IndexTestCase(
        id="include_nested_object_form",
        indexes=({"key": {"$**": 1}, "name": "wc", "wildcardProjection": {"a": {"b": 1}}},),
        msg="Inclusion projection in nested-object form should succeed",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_PROJECTION_TESTS))
def test_wildcard_projection_valid(collection, test):
    """Verify valid wildcardProjection configurations are accepted."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, {"numIndexesAfter": 2, "ok": 1.0}, msg=test.msg)


VALID_CREATION_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="all_fields_ascending",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        msg="All-fields ascending wildcard index should be created",
    ),
    IndexTestCase(
        id="all_fields_descending",
        indexes=({"key": {"$**": -1}, "name": "wc_all_desc"},),
        msg="All-fields descending wildcard index should be created",
    ),
    IndexTestCase(
        id="single_field_ascending",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        msg="Single-field ascending wildcard index should be created",
    ),
    IndexTestCase(
        id="single_field_descending",
        indexes=({"key": {"sub.$**": -1}, "name": "wc_sub_desc"},),
        msg="Single-field descending wildcard index should be created",
    ),
    IndexTestCase(
        id="deeply_nested_path",
        indexes=({"key": {"a.b.c.$**": 1}, "name": "wc_deep"},),
        msg="Deeply nested scoped wildcard index should be created",
    ),
    IndexTestCase(
        id="background_option",
        indexes=({"key": {"$**": 1}, "name": "wc_bg", "background": True},),
        msg="Wildcard index with background:true (legacy no-op) should be created",
    ),
    IndexTestCase(
        id="partial_filter",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "wc_partial",
                "partialFilterExpression": {"a": {"$gt": 0}},
            },
        ),
        msg="Wildcard index with partialFilterExpression should be created",
    ),
    IndexTestCase(
        id="collation",
        indexes=({"key": {"$**": 1}, "name": "wc_collation", "collation": {"locale": "en"}},),
        msg="Wildcard index with collation should be created",
    ),
    IndexTestCase(
        id="rooted_at_id",
        indexes=({"key": {"_id.$**": 1}, "name": "wc_id_sub"},),
        msg="Scoped wildcard index rooted at _id should be created",
    ),
    IndexTestCase(
        id="key_infinity",
        indexes=({"key": {"$**": float("inf")}, "name": "wc_inf"},),
        msg="Wildcard key with Infinity direction should be created (any nonzero number is valid)",
    ),
    IndexTestCase(
        id="key_negative_infinity",
        indexes=({"key": {"$**": float("-inf")}, "name": "wc_neg_inf"},),
        msg="Wildcard key with -Infinity direction should be created (any nonzero number is valid)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(VALID_CREATION_TESTS))
def test_wildcard_create_valid_spec(collection, test):
    """Verify valid wildcard index key patterns and options are accepted."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 2, "ok": 1.0},
        msg=test.msg,
    )


COMPOUND_WILDCARD_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="nonwildcard_first",
        indexes=({"key": {"a": 1, "$**": 1}, "name": "cwi_a_wc", "wildcardProjection": {"a": 0}},),
        msg="Compound wildcard (non-wildcard first) should be created",
    ),
    IndexTestCase(
        id="wildcard_first",
        indexes=({"key": {"$**": 1, "a": 1}, "name": "cwi_wc_a", "wildcardProjection": {"a": 0}},),
        msg="Compound wildcard (wildcard first) should be created",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOUND_WILDCARD_TESTS))
def test_compound_wildcard_created(collection, test):
    """Verify compound wildcard indexes are created with the wildcard term in either position."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(result, {"numIndexesAfter": 2, "ok": 1.0}, msg=test.msg)


DROP_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="by_name",
        input="wc_all",
        msg="Drop wildcard index by name",
    ),
    IndexTestCase(
        id="by_key_pattern",
        input={"$**": 1},
        msg="Drop wildcard index by key pattern",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DROP_TESTS))
def test_wildcard_drop(collection, test):
    """Verify dropIndexes removes the wildcard index by name or key pattern."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    result = execute_command(collection, {"dropIndexes": collection.name, "index": test.input})
    assertSuccessPartial(result, {"nIndexesWas": 2, "ok": 1.0}, msg=test.msg)


COEXIST_TESTS: list[IndexTestCase] = [
    IndexTestCase(
        id="two_wildcard_indexes",
        indexes=(
            {"key": {"$**": 1}, "name": "wc_all"},
            {"key": {"sub.$**": 1}, "name": "wc_sub"},
        ),
        msg="Two wildcard indexes with different key patterns should coexist",
    ),
    IndexTestCase(
        id="wildcard_with_targeted_index",
        indexes=(
            {"key": {"$**": 1}, "name": "wc_all"},
            {"key": {"a": 1}, "name": "a_1"},
        ),
        msg="Wildcard index coexists with targeted index on an overlapping field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COEXIST_TESTS))
def test_wildcard_coexists(collection, test):
    """Verify a wildcard index can coexist with other indexes on the same collection."""
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    assertSuccessPartial(
        result,
        {"numIndexesBefore": 1, "numIndexesAfter": 3, "ok": 1.0},
        msg=test.msg,
    )


PROJECTION_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="inclusion_included_field",
        indexes=({"key": {"$**": 1}, "name": "wc_inc", "wildcardProjection": {"a": 1}},),
        doc=({"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 3, "b": 4}),
        filter={"a": 1},
        hint="wc_inc",
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Query on included field via wildcard",
    ),
    IndexQueryTestCase(
        id="exclusion_non_excluded_field",
        indexes=({"key": {"$**": 1}, "name": "wc_exc", "wildcardProjection": {"a": 0}},),
        doc=({"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 3, "b": 4}),
        filter={"b": 2},
        hint="wc_exc",
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Query on non-excluded field via wildcard",
    ),
    IndexQueryTestCase(
        id="excluded_field_unhinted",
        indexes=({"key": {"$**": 1}, "name": "wc_exc", "wildcardProjection": {"a": 0}},),
        doc=({"_id": 1, "a": 1, "b": 2}, {"_id": 2, "a": 5, "b": 4}),
        filter={"a": 5},
        expected=[{"_id": 2, "a": 5, "b": 4}],
        msg="Excluded-field query correctness (via collection scan)",
    ),
    IndexQueryTestCase(
        id="dotted_path_projection_served",
        indexes=({"key": {"$**": 1}, "name": "wc_dot", "wildcardProjection": {"a.b": 1}},),
        doc=({"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}),
        filter={"a.b": 2},
        hint="wc_dot",
        expected=[{"_id": 2, "a": {"b": 2}}],
        msg="Query on a dotted-path projected subtree is served by the wildcard index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROJECTION_QUERY_TESTS))
def test_wildcard_projection_query(collection, test):
    """Verify query correctness on fields included in, excluded from, or outside a
    wildcardProjection."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter}
    if test.hint:
        cmd["hint"] = test.hint
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


def test_wildcard_auto_generated_name(collection):
    """Creating a wildcard index without specifying a name yields the conventional
    auto-generated '$**_1' name. The name is generated client-side by the driver helper
    (the raw createIndexes command requires an explicit name)."""
    collection.create_index([("$**", 1)])
    result = execute_command(collection, {"listIndexes": collection.name})
    assertSuccess(
        result,
        ["$**_1", "_id_"],
        transform=lambda batch: sorted(idx["name"] for idx in batch),
        msg="Wildcard index without an explicit name should be auto-named '$**_1'",
    )


def test_wildcard_create_on_empty_collection(collection):
    """Creating a wildcard index on an existing empty collection succeeds."""
    execute_command(collection, {"insert": collection.name, "documents": [{"_id": 1}]})
    execute_command(collection, {"delete": collection.name, "deletes": [{"q": {}, "limit": 0}]})
    result = execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_empty"}]},
    )
    assertSuccessPartial(
        result,
        {"numIndexesAfter": 2, "ok": 1.0},
        msg="Wildcard index on empty collection should be created",
    )


def test_wildcard_create_idempotent(collection):
    """Re-creating an identical wildcard index is a no-op (same index count)."""
    spec = {"key": {"$**": 1}, "name": "wc_idem"}
    execute_command(collection, {"createIndexes": collection.name, "indexes": [spec]})
    result = execute_command(collection, {"createIndexes": collection.name, "indexes": [spec]})
    assertSuccessPartial(
        result,
        {"numIndexesBefore": 2, "numIndexesAfter": 2, "ok": 1.0},
        msg="Re-creating identical wildcard index should be a no-op",
    )


def test_wildcard_same_name_different_projection_conflicts(collection):
    """Re-creating a wildcard index with the same name but a different wildcardProjection
    fails with IndexKeySpecsConflict."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wc_conf", "wildcardProjection": {"a": 1}}],
        },
    )
    result = execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wc_conf", "wildcardProjection": {"b": 1}}],
        },
    )
    assertFailureCode(
        result,
        INDEX_KEY_SPECS_CONFLICT_ERROR,
        msg="Same name with a different wildcardProjection should fail with IndexKeySpecsConflict",
    )


def test_wildcard_index_on_clustered_collection(collection):
    """A wildcard index can be created on a clustered collection."""
    name = f"{collection.name}_clustered"
    execute_command(
        collection,
        {"create": name, "clusteredIndex": {"key": {"_id": 1}, "unique": True}},
    )
    result = execute_command(
        collection,
        {"createIndexes": name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    assertSuccessPartial(
        result,
        {"numIndexesBefore": 0, "numIndexesAfter": 1, "ok": 1.0},
        msg="Wildcard index on clustered collection should succeed",
    )


def test_wildcard_and_text_coexist_non_text_query(collection):
    """With both wildcard and text indexes, a non-$text query still uses the wildcard index."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"$**": 1}, "name": "wc_all"},
                {"key": {"t": "text"}, "name": "t_text"},
            ],
        },
    )
    collection.insert_many([{"_id": 1, "t": "hello", "n": 1}, {"_id": 2, "t": "world", "n": 2}])
    result = execute_command(
        collection, {"find": collection.name, "filter": {"n": 2}, "hint": "wc_all"}
    )
    assertSuccess(
        result, [{"_id": 2, "t": "world", "n": 2}], msg="Non-$text query uses wildcard index"
    )


def test_wildcard_drop_scoped_by_key_pattern(collection):
    """dropIndexes removes a scoped (subtree) wildcard index specified by its key pattern."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"sub.$**": 1}, "name": "wc_sub"}]},
    )
    result = execute_command(collection, {"dropIndexes": collection.name, "index": {"sub.$**": 1}})
    assertSuccessPartial(
        result,
        {"nIndexesWas": 2, "ok": 1.0},
        msg="Drop scoped wildcard index by key pattern",
    )


def test_wildcard_query_after_drop_correct(collection):
    """After dropping the wildcard index, queries on previously indexed fields still return
    results."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    collection.insert_many([{"_id": 1, "a": 1}, {"_id": 2, "a": 2}])
    execute_command(collection, {"dropIndexes": collection.name, "index": "wc_all"})
    result = execute_command(collection, {"find": collection.name, "filter": {"a": 2}})
    assertSuccess(result, [{"_id": 2, "a": 2}], msg="Query correctness after wildcard index drop")


def test_wildcard_listindexes_reflects_index(collection):
    """listIndexes reflects the wildcard index with its key and name."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    result = execute_command(collection, {"listIndexes": collection.name})

    def _wc_entry(batch):
        for idx in batch:
            if idx["name"] == "wc_all":
                return {"key": idx["key"], "name": idx["name"]}
        return None

    assertSuccess(
        result,
        {"key": {"$**": 1}, "name": "wc_all"},
        transform=_wc_entry,
        msg="listIndexes reflects wildcard index key and name",
    )


def test_wildcard_projection_persisted_in_listindexes(collection):
    """A wildcardProjection is persisted and reported by listIndexes."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [
                {"key": {"$**": 1}, "name": "wc_proj", "wildcardProjection": {"a": 0, "b": 0}}
            ],
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})

    def _get_proj(batch):
        for idx in batch:
            if idx["name"] == "wc_proj":
                return idx.get("wildcardProjection")
        return None

    assertSuccess(
        result,
        {"a": 0, "b": 0},
        transform=_get_proj,
        msg="wildcardProjection should be persisted in listIndexes",
    )
