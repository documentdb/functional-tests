"""Tests for $indexStats accesses.ops counter behavior."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection
from pymongo.operations import IndexModel

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.property_checks import Gte

# Property [Ops Increment]: accesses.ops increments after index usage.
OPS_INCREMENT_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="ops_increments_after_find",
        indexes=[IndexModel([("a", 1)])],
        docs=[{"a": 1}, {"a": 2}, {"a": 3}],
        setup=lambda c: list(c.find({"a": 1})),
        pipeline=[{"$indexStats": {}}, {"$match": {"name": "a_1"}}],
        expected={"accesses.ops": Gte(1)},
        msg="accesses.ops should increment after index is used by a query",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(OPS_INCREMENT_TESTS))
def test_indexStats_ops_counter(collection: Collection, test_case: StageTestCase):
    """Test $indexStats accesses.ops counter increments after index usage."""
    coll = populate_collection(collection, test_case)
    if test_case.setup:
        test_case.setup(coll)
    result = execute_command(
        coll,
        {
            "aggregate": coll.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
