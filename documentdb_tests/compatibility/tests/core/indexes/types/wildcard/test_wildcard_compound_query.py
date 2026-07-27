"""Tests for compound wildcard index queries: filtering on the non-wildcard prefix field
together with a wildcard-covered field."""

import pytest

from documentdb_tests.compatibility.tests.core.indexes.commands.utils.index_test_case import (
    IndexQueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

pytestmark = pytest.mark.index

COMPOUND_WILDCARD_QUERY_TESTS: list[IndexQueryTestCase] = [
    IndexQueryTestCase(
        id="prefix_and_wildcard_field_nonwildcard_first",
        indexes=({"key": {"a": 1, "$**": 1}, "name": "cwi_a_wc", "wildcardProjection": {"a": 0}},),
        doc=(
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
        ),
        filter={"a": 1, "b": 10},
        hint="cwi_a_wc",
        expected=[{"_id": 1, "a": 1, "b": 10}],
        msg="Compound wildcard (non-wildcard first) serves a prefix + wildcard-field query",
    ),
    IndexQueryTestCase(
        id="prefix_and_wildcard_field_wildcard_first",
        indexes=({"key": {"$**": 1, "a": 1}, "name": "cwi_wc_a", "wildcardProjection": {"a": 0}},),
        doc=(
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
        ),
        filter={"a": 1, "b": 10},
        hint="cwi_wc_a",
        expected=[{"_id": 1, "a": 1, "b": 10}],
        msg="Compound wildcard (wildcard first) serves a prefix + wildcard-field query",
    ),
    IndexQueryTestCase(
        id="prefix_equality_wildcard_range",
        indexes=({"key": {"a": 1, "$**": 1}, "name": "cwi_a_wc", "wildcardProjection": {"a": 0}},),
        doc=(
            {"_id": 1, "a": 1, "b": 5},
            {"_id": 2, "a": 1, "b": 15},
            {"_id": 3, "a": 2, "b": 15},
        ),
        filter={"a": 1, "b": {"$gte": 10}},
        hint="cwi_a_wc",
        sort={"_id": 1},
        expected=[{"_id": 2, "a": 1, "b": 15}],
        msg="Compound wildcard serves prefix equality plus a range on the wildcard field",
    ),
    IndexQueryTestCase(
        id="prefix_only_query",
        indexes=({"key": {"a": 1, "$**": 1}, "name": "cwi_a_wc", "wildcardProjection": {"a": 0}},),
        doc=(
            {"_id": 1, "a": 1, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 30},
        ),
        filter={"a": 1},
        hint="cwi_a_wc",
        sort={"_id": 1},
        expected=[{"_id": 1, "a": 1, "b": 10}, {"_id": 2, "a": 1, "b": 20}],
        msg="Compound wildcard serves a query on the non-wildcard prefix field alone",
    ),
]


@pytest.mark.parametrize("test", pytest_params(COMPOUND_WILDCARD_QUERY_TESTS))
def test_compound_wildcard_query(collection, test):
    """Verify a compound wildcard index serves a query filtering on the non-wildcard prefix
    field together with a wildcard-covered field."""
    execute_command(
        collection,
        {"createIndexes": collection.name, "indexes": list(test.indexes)},
    )
    collection.insert_many(list(test.doc))
    result = execute_command(
        collection,
        {"find": collection.name, "filter": test.filter, "hint": test.hint},
    )
    assertSuccess(result, test.expected, msg=test.msg)
