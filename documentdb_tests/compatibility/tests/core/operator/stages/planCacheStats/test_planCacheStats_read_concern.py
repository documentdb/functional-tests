"""Tests for $planCacheStats read concern handling."""

from __future__ import annotations

import pytest
from pymongo.collection import Collection

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import INVALID_OPTIONS_ERROR
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Read Concern Success]: readConcern "local" is accepted.
READ_CONCERN_LOCAL_TEST: list[StageTestCase] = [
    StageTestCase(
        "read_concern_local",
        docs=[],
        pipeline=[{"$planCacheStats": {}}],
        expected=[],
        msg="readConcern 'local' should succeed",
    ),
]

# Property [Read Concern Error]: any read concern other than "local" produces
# an INVALID_OPTIONS_ERROR.
READ_CONCERN_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        f"read_concern_{level}",
        docs=[],
        pipeline=[{"$planCacheStats": {}}],
        error_code=INVALID_OPTIONS_ERROR,
        msg=f"readConcern {level!r} should produce INVALID_OPTIONS_ERROR",
    )
    for level in ("available", "majority", "linearizable", "snapshot")
]

READ_CONCERN_ALL_TESTS = READ_CONCERN_LOCAL_TEST + READ_CONCERN_ERROR_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(READ_CONCERN_ALL_TESTS))
def test_planCacheStats_read_concern(collection: Collection, test_case: StageTestCase):
    """Test $planCacheStats read concern handling."""
    populate_collection(collection, test_case)
    level = test_case.id.removeprefix("read_concern_")
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
            "readConcern": {"level": level},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )
