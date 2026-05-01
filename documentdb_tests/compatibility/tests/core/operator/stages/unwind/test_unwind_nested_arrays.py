"""Tests for $unwind stage — nested arrays."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Nested Arrays]: $unwind peels exactly one level of array nesting
# per invocation - inner arrays are preserved as elements, and successive
# $unwind stages on the same field flatten additional nesting levels.
UNWIND_NESTED_ARRAYS_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nested_array_of_arrays",
        docs=[{"_id": 1, "a": [[1, 2], [3]]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": [1, 2]},
            {"_id": 1, "a": [3]},
        ],
        msg="$unwind should produce one document per inner array",
    ),
    StageTestCase(
        "nested_deeply_nested",
        docs=[{"_id": 1, "a": [[[1]], [[2, 3]]]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": [[1]]},
            {"_id": 1, "a": [[2, 3]]},
        ],
        msg="$unwind should peel only one level, preserving deeper nesting",
    ),
    StageTestCase(
        "nested_mixed_scalars_and_arrays",
        docs=[{"_id": 1, "a": [1, [2, 3], 4]}],
        pipeline=[{"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 1},
            {"_id": 1, "a": [2, 3]},
            {"_id": 1, "a": 4},
        ],
        msg="$unwind should preserve inner arrays alongside scalar elements",
    ),
    StageTestCase(
        "nested_successive_unwind_flattens",
        docs=[{"_id": 1, "a": [[10, 20], [30]]}],
        pipeline=[{"$unwind": {"path": "$a"}}, {"$unwind": {"path": "$a"}}],
        expected=[
            {"_id": 1, "a": 10},
            {"_id": 1, "a": 20},
            {"_id": 1, "a": 30},
        ],
        msg="Successive $unwind stages on the same field should flatten additional nesting",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(UNWIND_NESTED_ARRAYS_TESTS))
def test_unwind_nested_arrays(collection, test_case: StageTestCase):
    """Test $unwind nested array behavior."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
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
