"""Tests for explain wiring with geospatial $nearSphere queries.

These are wiring tests: they verify that explain plans $nearSphere queries
across command types (find, count, distinct, findAndModify). Comprehensive
geospatial parsing and semantics live under the geospatial feature directory;
here we only confirm explain delegates to the geo query path.
"""

import pytest
from pymongo import IndexModel

from documentdb_tests.compatibility.tests.core.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Eq

pytestmark = [pytest.mark.admin, pytest.mark.geospatial]


NEAR = {"loc": {"$nearSphere": {"$geometry": {"type": "Point", "coordinates": [0, 0]}}}}

GEO_DOCS = [
    {"_id": 0, "loc": {"type": "Point", "coordinates": [0, 0]}, "a": 1},
    {"_id": 1, "loc": {"type": "Point", "coordinates": [1, 1]}, "a": 2},
    {"_id": 2, "loc": {"type": "Point", "coordinates": [2, 2]}, "a": 3},
]
GEO_INDEXES = [IndexModel([("loc", "2dsphere")])]


NEARSPHERE_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        id="find_basic",
        docs=GEO_DOCS,
        indexes=GEO_INDEXES,
        command=lambda ctx: {
            "explain": {"find": ctx.collection, "filter": NEAR},
            "verbosity": "queryPlanner",
        },
        expected={"ok": Eq(1.0)},
        msg="explain find $nearSphere (basic) should plan",
    ),
    CommandTestCase(
        id="count",
        docs=GEO_DOCS,
        indexes=GEO_INDEXES,
        command=lambda ctx: {
            "explain": {"count": ctx.collection, "query": NEAR},
            "verbosity": "queryPlanner",
        },
        expected={"ok": Eq(1.0)},
        msg="explain count $nearSphere should plan",
    ),
    CommandTestCase(
        id="distinct",
        docs=GEO_DOCS,
        indexes=GEO_INDEXES,
        command=lambda ctx: {
            "explain": {"distinct": ctx.collection, "key": "a", "query": NEAR},
            "verbosity": "queryPlanner",
        },
        expected={"ok": Eq(1.0)},
        msg="explain distinct $nearSphere should plan",
    ),
    CommandTestCase(
        id="findAndModify",
        docs=GEO_DOCS,
        indexes=GEO_INDEXES,
        command=lambda ctx: {
            "explain": {
                "findAndModify": ctx.collection,
                "query": NEAR,
                "update": {"$set": {"visited": True}},
            },
            "verbosity": "queryPlanner",
        },
        expected={"ok": Eq(1.0)},
        msg="explain findAndModify $nearSphere should plan",
    ),
]


@pytest.mark.parametrize("test", pytest_params(NEARSPHERE_TESTS))
def test_explain_nearSphere_plans(collection, test):
    """Test explain plans $nearSphere queries across command types."""
    collection = test.prepare(collection.database, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
        raw_res=True,
    )
