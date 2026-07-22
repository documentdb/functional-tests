"""Tests for wildcard index query behavior: equality, range, scoped-path, logical/array
operators, sort, projection output, count, aggregation, and distinct.

wildcardProjection-constrained queries live in test_wildcard_projection_query.py and compound
wildcard queries live in test_wildcard_compound_query.py."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess, assertSuccessPartial
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

EQUALITY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="scalar",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 5}, {"_id": 2, "a": 7}),
        filter={"a": 5},
        hint="wc_all",
        expected=[{"_id": 1, "a": 5}],
        msg="Equality on scalar via wildcard index",
    ),
    IndexQueryTestCase(
        id="string",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "s": "hello"}, {"_id": 2, "s": "world"}),
        filter={"s": "world"},
        hint="wc_all",
        expected=[{"_id": 2, "s": "world"}],
        msg="Equality on string via wildcard index",
    ),
    IndexQueryTestCase(
        id="nested_path",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": 1}}, {"_id": 2, "a": {"b": 2}}),
        filter={"a.b": 2},
        hint="wc_all",
        expected=[{"_id": 2, "a": {"b": 2}}],
        msg="Equality on nested path via wildcard",
    ),
    IndexQueryTestCase(
        id="no_match",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 5}, {"_id": 2, "a": 7}),
        filter={"a": 99},
        hint="wc_all",
        expected=[],
        msg="No-match equality returns empty set",
    ),
    IndexQueryTestCase(
        id="schema_less_field",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "b": "x"}, {"_id": 3, "a": 1, "c": True}),
        filter={"b": "x"},
        hint="wc_all",
        expected=[{"_id": 2, "b": "x"}],
        msg="Query on a field only some documents have returns the correct subset",
    ),
    IndexQueryTestCase(
        id="scoped_in_scope",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=({"_id": 1, "sub": {"x": 1}}, {"_id": 2, "sub": {"x": 2}}),
        filter={"sub.x": 2},
        hint="wc_sub",
        expected=[{"_id": 2, "sub": {"x": 2}}],
        msg="Scoped wildcard in-scope query",
    ),
    IndexQueryTestCase(
        id="hint_by_key_pattern",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        filter={"a": 2},
        hint={"$**": 1},
        expected=[{"_id": 2, "a": 2}],
        msg="Hint by key pattern returns correct doc",
    ),
    IndexQueryTestCase(
        id="id_field_unhinted",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        filter={"_id": 2},
        expected=[{"_id": 2, "a": 2}],
        msg="Query on _id returns the correct document with only a wildcard index",
    ),
    IndexQueryTestCase(
        id="id_included_via_projection_hinted",
        indexes=({"key": {"$**": 1}, "name": "wc_id", "wildcardProjection": {"_id": 1}},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        filter={"_id": 2},
        hint="wc_id",
        expected=[{"_id": 2, "a": 2}],
        msg="Hinted _id query works when _id included in wildcardProjection",
    ),
    IndexQueryTestCase(
        id="hidden_index_unhinted",
        indexes=({"key": {"$**": 1}, "name": "wc_hidden", "hidden": True},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        filter={"a": 2},
        expected=[{"_id": 2, "a": 2}],
        msg="Query correctness when the only wildcard index is hidden",
    ),
]


@pytest.mark.parametrize("test", pytest_params(EQUALITY_TESTS))
def test_wildcard_equality(collection, test):
    """Verify equality queries return correct documents via wildcard indexes."""
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


RANGE_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="gt",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        filter={"a": {"$gt": 4}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 9}],
        msg="$gt range via wildcard",
    ),
    IndexQueryTestCase(
        id="gte",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        filter={"a": {"$gte": 5}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 9}],
        msg="$gte range via wildcard",
    ),
    IndexQueryTestCase(
        id="lt",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        filter={"a": {"$lt": 5}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1}],
        msg="$lt range via wildcard",
    ),
    IndexQueryTestCase(
        id="lte",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        filter={"a": {"$lte": 5}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1}, {"_id": 2, "a": 5}],
        msg="$lte range via wildcard",
    ),
    IndexQueryTestCase(
        id="type_bracketing",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": 10},
            {"_id": 2, "a": "20"},
            {"_id": 3, "a": True},
            {"_id": 4, "a": 30},
        ),
        filter={"a": {"$gt": 5}},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 10}, {"_id": 4, "a": 30}],
        msg="Numeric range is type-bracketed — excludes string/bool values",
    ),
    IndexQueryTestCase(
        id="scoped_range_in_scope",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=(
            {"_id": 1, "sub": {"x": 1}},
            {"_id": 2, "sub": {"x": 5}},
            {"_id": 3, "sub": {"x": 9}},
        ),
        filter={"sub.x": {"$gte": 5}},
        hint="wc_sub",
        sort={"_id": 1},
        expected=[{"_id": 2, "sub": {"x": 5}}, {"_id": 3, "sub": {"x": 9}}],
        msg="Scoped wildcard range in-scope query",
    ),
]


@pytest.mark.parametrize("test", pytest_params(RANGE_TESTS))
def test_wildcard_range(collection, test):
    """Verify range queries return only documents satisfying the predicate."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "hint": test.hint, "sort": test.sort}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


SCOPED_WILDCARD_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="deeper_scope_nested_leaf",
        indexes=({"key": {"a.b.$**": 1}, "name": "wc_ab"},),
        doc=({"_id": 1, "a": {"b": {"c": 1}}}, {"_id": 2, "a": {"b": {"c": 2}}}),
        filter={"a.b.c": 2},
        hint="wc_ab",
        expected=[{"_id": 2, "a": {"b": {"c": 2}}}],
        msg="Deeper scoped wildcard (a.b.$**) serves a query on a leaf within scope",
    ),
    IndexQueryTestCase(
        id="scope_sibling_leaf",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=({"_id": 1, "sub": {"x": 1, "y": 2}}, {"_id": 2, "sub": {"x": 3, "y": 4}}),
        filter={"sub.y": 2},
        hint="wc_sub",
        expected=[{"_id": 1, "sub": {"x": 1, "y": 2}}],
        msg="Scoped wildcard indexes every leaf under scope; a sibling leaf is queryable",
    ),
    IndexQueryTestCase(
        id="scope_multikey_array",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=({"_id": 1, "sub": {"tags": ["a", "b"]}}, {"_id": 2, "sub": {"tags": ["c"]}}),
        filter={"sub.tags": "b"},
        hint="wc_sub",
        expected=[{"_id": 1, "sub": {"tags": ["a", "b"]}}],
        msg="Scoped wildcard matches an array element within scope (multikey)",
    ),
    IndexQueryTestCase(
        id="scope_in_predicate",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=(
            {"_id": 1, "sub": {"x": 1}},
            {"_id": 2, "sub": {"x": 2}},
            {"_id": 3, "sub": {"x": 3}},
        ),
        filter={"sub.x": {"$in": [1, 3]}},
        hint="wc_sub",
        sort={"_id": 1},
        expected=[{"_id": 1, "sub": {"x": 1}}, {"_id": 3, "sub": {"x": 3}}],
        msg="Scoped wildcard serves an $in predicate on an in-scope field",
    ),
    IndexQueryTestCase(
        id="scope_sort_within_scope",
        indexes=({"key": {"sub.$**": 1}, "name": "wc_sub"},),
        doc=(
            {"_id": 1, "sub": {"x": 9}},
            {"_id": 2, "sub": {"x": 3}},
            {"_id": 3, "sub": {"x": 6}},
        ),
        filter={"sub.x": {"$gte": 3}},
        sort={"sub.x": 1},
        hint="wc_sub",
        expected=[
            {"_id": 2, "sub": {"x": 3}},
            {"_id": 3, "sub": {"x": 6}},
            {"_id": 1, "sub": {"x": 9}},
        ],
        msg="Scoped wildcard provides sort order for an in-scope field",
    ),
    IndexQueryTestCase(
        id="scope_rooted_at_id_subfield",
        indexes=({"key": {"_id.$**": 1}, "name": "wc_id_sub"},),
        doc=({"_id": {"a": 1, "b": 2}}, {"_id": {"a": 3, "b": 4}}),
        filter={"_id.a": 3},
        hint="wc_id_sub",
        expected=[{"_id": {"a": 3, "b": 4}}],
        msg="Scoped wildcard rooted at _id serves a query on an _id subfield",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SCOPED_WILDCARD_TESTS))
def test_wildcard_scoped_path(collection, test):
    """Verify path-specific (scoped) wildcard indexes serve queries on fields within scope."""
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


OPERATOR_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="or_two_fields",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": 1, "b": 0},
            {"_id": 2, "a": 0, "b": 2},
            {"_id": 3, "a": 0, "b": 0},
        ),
        filter={"$or": [{"a": 1}, {"b": 2}]},
        hint="wc_all",
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1, "b": 0}, {"_id": 2, "a": 0, "b": 2}],
        msg="$or across two fields returns the correct union",
    ),
    IndexQueryTestCase(
        id="or_multi_field_branch",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1, "b": 9},
            {"_id": 3, "c": 3},
        ),
        filter={"$or": [{"a": 1, "b": 2}, {"c": 3}]},
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1, "b": 2}, {"_id": 3, "c": 3}],
        msg="$or with a multi-field branch returns correct results",
    ),
    IndexQueryTestCase(
        id="explicit_and",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": 1, "b": 2},
            {"_id": 2, "a": 1, "b": 9},
            {"_id": 3, "a": 5, "b": 2},
        ),
        filter={"$and": [{"a": 1}, {"b": 2}]},
        hint="wc_all",
        expected=[{"_id": 1, "a": 1, "b": 2}],
        msg="Explicit $and across two fields returns the correct intersection",
    ),
    IndexQueryTestCase(
        id="implicit_and",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": 1, "b": 5},
            {"_id": 2, "a": 1, "b": 9},
            {"_id": 3, "a": 2, "b": 5},
        ),
        filter={"a": 1, "b": 5},
        hint="wc_all",
        expected=[{"_id": 1, "a": 1, "b": 5}],
        msg="Implicit AND applies both predicates via wildcard hint",
    ),
    IndexQueryTestCase(
        id="elemmatch_not_covered",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": [{"b": 5}, {"b": 1}]},
            {"_id": 2, "a": [{"b": 1}]},
        ),
        filter={"a": {"$elemMatch": {"b": {"$gte": 4}}}},
        hint="wc_all",
        expected=[{"_id": 1, "a": [{"b": 5}, {"b": 1}]}],
        msg="$elemMatch (not coverable) returns correct docs",
    ),
    IndexQueryTestCase(
        id="prefix_regex",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "s": "hello"},
            {"_id": 2, "s": "help"},
            {"_id": 3, "s": "world"},
        ),
        filter={"s": {"$regex": "^he"}},
        hint="wc_all",
        expected=[{"_id": 1, "s": "hello"}, {"_id": 2, "s": "help"}],
        msg="Prefix $regex on a string field served by wildcard index",
    ),
]


@pytest.mark.parametrize("test", pytest_params(OPERATOR_TESTS))
def test_wildcard_operators(collection, test):
    """Verify logical and array operator queries return correct documents via the wildcard
    index."""
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


SORT_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="same_field_ascending",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 9}, {"_id": 2, "a": 3}, {"_id": 3, "a": 6}),
        filter={"a": {"$gte": 3}},
        sort={"a": 1},
        hint="wc_all",
        expected=[{"_id": 2, "a": 3}, {"_id": 3, "a": 6}, {"_id": 1, "a": 9}],
        msg="Ascending sort on the query field returns ordered results",
    ),
    IndexQueryTestCase(
        id="same_field_descending",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 9}, {"_id": 2, "a": 3}, {"_id": 3, "a": 6}),
        filter={"a": {"$gte": 3}},
        sort={"a": -1},
        hint="wc_all",
        expected=[{"_id": 1, "a": 9}, {"_id": 3, "a": 6}, {"_id": 2, "a": 3}],
        msg="Descending sort on the query field returns ordered results",
    ),
    IndexQueryTestCase(
        id="different_field",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=(
            {"_id": 1, "a": 1, "b": 30},
            {"_id": 2, "a": 1, "b": 10},
            {"_id": 3, "a": 1, "b": 20},
        ),
        filter={"a": 1},
        sort={"b": 1},
        hint="wc_all",
        expected=[
            {"_id": 2, "a": 1, "b": 10},
            {"_id": 3, "a": 1, "b": 20},
            {"_id": 1, "a": 1, "b": 30},
        ],
        msg="Sort on a different field returns correctly ordered results",
    ),
    IndexQueryTestCase(
        id="multikey_field",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [3, 1]}, {"_id": 2, "a": [2, 5]}, {"_id": 3, "a": [0, 4]}),
        filter={"a": {"$gte": 0}},
        sort={"a": 1},
        hint="wc_all",
        expected=[{"_id": 3, "a": [0, 4]}, {"_id": 1, "a": [3, 1]}, {"_id": 2, "a": [2, 5]}],
        msg="Sort on multikey field orders by minimum element",
    ),
]


@pytest.mark.parametrize("test", pytest_params(SORT_TESTS))
def test_wildcard_sort(collection, test):
    """Verify sorted queries via the wildcard index return correctly ordered results."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {"find": collection.name, "filter": test.filter, "sort": test.sort, "hint": test.hint}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


PROJECTION_OUTPUT_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="equality",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 5}, {"_id": 2, "a": 7}),
        filter={"a": 5},
        hint="wc_all",
        expected=[{"a": 5}],
        msg="Projection onto the query field returns only the projected field (equality)",
    ),
    IndexQueryTestCase(
        id="range",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        filter={"a": {"$gte": 5}},
        hint="wc_all",
        sort={"a": 1},
        expected=[{"a": 5}, {"a": 9}],
        msg="Projection onto the query field returns only the projected field (range)",
    ),
    IndexQueryTestCase(
        id="in",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}),
        filter={"a": {"$in": [1, 3]}},
        hint="wc_all",
        sort={"a": 1},
        expected=[{"a": 1}, {"a": 3}],
        msg="Projection onto the query field returns only the projected field ($in)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(PROJECTION_OUTPUT_TESTS))
def test_wildcard_projection_output(collection, test):
    """Verify a hinted wildcard query with a projection onto the query field (_id excluded)
    returns only the projected field. This checks projection output correctness, not that the
    plan is index-covered (verifying coverage would require explain, which the suite does not
    test)."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {
        "find": collection.name,
        "filter": test.filter,
        "projection": {"_id": 0, "a": 1},
        "hint": test.hint,
    }
    if test.sort:
        cmd["sort"] = test.sort
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


COUNT_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="range",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        filter={"a": {"$gte": 5}},
        hint="wc_all",
        expected={"n": 2, "ok": 1.0},
        msg="count range predicate",
    ),
    IndexQueryTestCase(
        id="in_predicate",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 3}, {"_id": 4, "a": 4}),
        filter={"a": {"$in": [1, 3]}},
        hint="wc_all",
        expected={"n": 2, "ok": 1.0},
        msg="count $in predicate",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COUNT_TESTS))
def test_wildcard_count(collection, test):
    """Verify count returns the correct number of matches via the wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection, {"count": collection.name, "query": test.filter, "hint": test.hint}
    )
    assertSuccessPartial(result, test.expected, msg=test.msg)


AGGREGATION_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="match",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        command_options={"pipeline": [{"$match": {"a": {"$gte": 5}}}, {"$sort": {"_id": 1}}]},
        hint="wc_all",
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 9}],
        msg="$match via wildcard index",
    ),
    IndexQueryTestCase(
        id="match_project_covered",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 5}, {"_id": 2, "a": 7}),
        command_options={"pipeline": [{"$match": {"a": 5}}, {"$project": {"_id": 0, "a": 1}}]},
        hint="wc_all",
        expected=[{"a": 5}],
        msg="$match + $project returns projected fields",
    ),
    IndexQueryTestCase(
        id="match_expr",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        command_options={
            "pipeline": [{"$match": {"$expr": {"$gt": ["$a", 4]}}}, {"$sort": {"_id": 1}}]
        },
        expected=[{"_id": 2, "a": 5}, {"_id": 3, "a": 9}],
        msg="$match with $expr returns correct docs",
    ),
    IndexQueryTestCase(
        id="count",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 5}, {"_id": 3, "a": 9}),
        command_options={"pipeline": [{"$match": {"a": {"$gte": 5}}}, {"$count": "total"}]},
        hint="wc_all",
        expected=[{"total": 2}],
        msg="$count aggregation range predicate",
    ),
]


@pytest.mark.parametrize("test", pytest_params(AGGREGATION_TESTS))
def test_wildcard_aggregation(collection, test):
    """Verify aggregation pipelines on wildcard-indexed fields return correct results."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    cmd = {
        "aggregate": collection.name,
        "pipeline": test.command_options["pipeline"],
        "cursor": {},
    }
    if test.hint:
        cmd["hint"] = test.hint
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, msg=test.msg)


def _sorted_values(result):
    return sorted(result["values"])


DISTINCT_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="no_query",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}, {"_id": 3, "a": 2}, {"_id": 4, "a": 3}),
        command_options={"key": "a"},
        expected=[1, 2, 3],
        msg="distinct with no query",
    ),
    IndexQueryTestCase(
        id="equality_query",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": 5}, {"_id": 2, "a": 5}, {"_id": 3, "a": 7}),
        command_options={"key": "a", "query": {"a": 5}},
        expected=[5],
        msg="distinct with equality query",
    ),
    IndexQueryTestCase(
        id="multikey",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": [1, 2]}, {"_id": 2, "a": [2, 3]}, {"_id": 3, "a": []}),
        command_options={"key": "a", "query": {"a": {"$gte": 1}}},
        expected=[1, 2, 3],
        msg="distinct on multikey field unwraps array elements",
    ),
    IndexQueryTestCase(
        id="dotted_path",
        indexes=({"key": {"$**": 1}, "name": "wc_all"},),
        doc=({"_id": 1, "a": {"b": 10}}, {"_id": 2, "a": {"b": 10}}, {"_id": 3, "a": {"b": 20}}),
        command_options={"key": "a.b", "query": {"a.b": {"$gte": 10}}},
        expected=[10, 20],
        msg="distinct on dotted path",
    ),
]


@pytest.mark.parametrize("test", pytest_params(DISTINCT_TESTS))
def test_wildcard_distinct(collection, test):
    """Verify distinct returns the correct unique values via the wildcard index."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(collection, {"distinct": collection.name, **test.command_options})
    assertSuccess(result, test.expected, transform=_sorted_values, raw_res=True, msg=test.msg)


def test_wildcard_index_matches_collection_scan(collection):
    """Wildcard index scan results match an unhinted (collection scan) query for a range."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": [{"key": {"$**": 1}, "name": "wc_all"}]},
    )
    docs = [{"_id": i, "a": i * 3 % 7} for i in range(10)]
    collection.insert_many(docs)
    hinted = execute_command(
        collection,
        {
            "find": collection.name,
            "filter": {"a": {"$gte": 2}},
            "hint": "wc_all",
            "sort": {"_id": 1},
        },
    )
    unhinted = execute_command(
        collection,
        {"find": collection.name, "filter": {"a": {"$gte": 2}}, "sort": {"_id": 1}},
    )
    assertSuccess(
        hinted,
        unhinted["cursor"]["firstBatch"],
        msg="Wildcard IXSCAN results match collection scan results",
    )


def test_wildcard_hidden_created(collection):
    """A wildcard index created with hidden:true is reported as hidden in listIndexes."""
    execute_command(
        collection,
        {
            "createIndexes": collection.name,
            "indexes": [{"key": {"$**": 1}, "name": "wc_hidden", "hidden": True}],
        },
    )
    result = execute_command(collection, {"listIndexes": collection.name})

    def _hidden(batch):
        for idx in batch:
            if idx["name"] == "wc_hidden":
                return idx.get("hidden")
        return None

    assertSuccess(result, True, transform=_hidden, msg="Hidden wildcard index reports hidden:true")
