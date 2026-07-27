"""Tests for queries served by a wildcard index constrained by a wildcardProjection
(inclusion/exclusion projections, _id handling)."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

WILDCARD_PROJECTION_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="inclusion_nested_leaf_served",
        indexes=({"key": {"$**": 1}, "name": "wc_inc", "wildcardProjection": {"a": 1}},),
        doc=(
            {"_id": 1, "a": {"b": 1}, "z": 9},
            {"_id": 2, "a": {"b": 2}, "z": 8},
        ),
        filter={"a.b": 2},
        hint="wc_inc",
        expected=[{"_id": 2, "a": {"b": 2}, "z": 8}],
        msg="Inclusion projection indexes the whole subtree; a nested leaf under it is served",
    ),
    IndexQueryTestCase(
        id="inclusion_range_on_projected_field",
        indexes=({"key": {"$**": 1}, "name": "wc_inc", "wildcardProjection": {"a": 1}},),
        doc=(
            {"_id": 1, "a": 1, "b": 100},
            {"_id": 2, "a": 5, "b": 100},
            {"_id": 3, "a": 9, "b": 100},
        ),
        filter={"a": {"$gte": 5}},
        hint="wc_inc",
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 5, "b": 100}, {"_id": 3, "a": 9, "b": 100}],
        msg="Range query on an included field is served by the wildcard index",
    ),
    IndexQueryTestCase(
        id="exclusion_sibling_of_excluded_served",
        indexes=({"key": {"$**": 1}, "name": "wc_exc", "wildcardProjection": {"a": 0}},),
        doc=(
            {"_id": 1, "a": 1, "b": {"c": 1}},
            {"_id": 2, "a": 2, "b": {"c": 2}},
        ),
        filter={"b.c": 2},
        hint="wc_exc",
        expected=[{"_id": 2, "a": 2, "b": {"c": 2}}],
        msg="Exclusion projection still indexes non-excluded nested leaves",
    ),
    IndexQueryTestCase(
        id="exclusion_multiple_fields_served",
        indexes=({"key": {"$**": 1}, "name": "wc_exc2", "wildcardProjection": {"a": 0, "b": 0}},),
        doc=(
            {"_id": 1, "a": 1, "b": 2, "c": 3},
            {"_id": 2, "a": 4, "b": 5, "c": 6},
        ),
        filter={"c": 6},
        hint="wc_exc2",
        expected=[{"_id": 2, "a": 4, "b": 5, "c": 6}],
        msg="Query on a field outside a multi-field exclusion projection is served",
    ),
    IndexQueryTestCase(
        id="exclude_id_inclusion_serves_field",
        indexes=(
            {
                "key": {"$**": 1},
                "name": "wc_noid",
                "wildcardProjection": {"_id": 0, "a": 1},
            },
        ),
        doc=({"_id": 1, "a": 1}, {"_id": 2, "a": 2}),
        filter={"a": 2},
        hint="wc_noid",
        expected=[{"_id": 2, "a": 2}],
        msg="Inclusion projection with _id excluded still serves the included field",
    ),
]


@pytest.mark.parametrize("test", pytest_params(WILDCARD_PROJECTION_QUERY_TESTS))
def test_wildcard_projection_query_served(collection, test):
    """Verify queries are served by a wildcard index constrained by a wildcardProjection."""
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
