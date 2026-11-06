"""Tests that expression operators work within $group expressions."""

from __future__ import annotations

from typing import Any

import pytest
from bson import Int64, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

GROUP_EXPRESSION_TESTS: list[StageTestCase] = [
    StageTestCase(
        id="group_id_tsIncrement",
        docs=[
            {"_id": 1, "ts": Timestamp(100, 5)},
            {"_id": 2, "ts": Timestamp(200, 5)},
            {"_id": 3, "ts": Timestamp(300, 10)},
        ],
        pipeline=[
            {"$group": {"_id": {"$tsIncrement": "$ts"}, "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": Int64(5), "count": 2}, {"_id": Int64(10), "count": 1}],
        msg="$tsIncrement should work as a $group _id expression",
    ),
    StageTestCase(
        id="group_accumulator_tsIncrement",
        docs=[
            {"_id": 1, "ts": Timestamp(100, 3)},
            {"_id": 2, "ts": Timestamp(200, 7)},
        ],
        pipeline=[
            {"$group": {"_id": None, "max_ordinal": {"$max": {"$tsIncrement": "$ts"}}}},
        ],
        expected=[{"_id": None, "max_ordinal": Int64(7)}],
        msg="$tsIncrement should work inside an accumulator expression in $group",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(GROUP_EXPRESSION_TESTS))
def test_group_expression_cases(collection: Any, test_case: StageTestCase):
    """Test that expression operators work within $group."""
    coll = populate_collection(collection, test_case)
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
