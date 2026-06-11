"""Tests for $redact $$DESCEND structural traversal.

Covers deep nesting, large arrays, and empty-container retention.
"""

from __future__ import annotations

from functools import reduce
from typing import Any, cast

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Recursion Depth and Scale]: $redact descends through deep nesting and
# large arrays of embedded documents without error or truncation.
REDACT_STRUCTURAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        "structural_large_array_descended_element_wise",
        docs=[{"_id": 1, "items": [{"n": i, "sub": {"secret": True}} for i in range(10_000)]}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, "items": [{"n": i} for i in range(10_000)]}],
        msg="$redact under $$DESCEND should descend element-wise into a large array of "
        "embedded documents without error",
    ),
    StageTestCase(
        "structural_deep_nesting_depth_99",
        docs=[{"_id": 1, **reduce(lambda v, k: {k: v}, ["a"] * 99, cast(Any, {"secret": True}))}],
        pipeline=[{"$redact": {"$cond": [{"$eq": ["$secret", True]}, "$$PRUNE", "$$DESCEND"]}}],
        expected=[{"_id": 1, **reduce(lambda v, k: {k: v}, ["a"] * 98, cast(Any, {}))}],
        msg="$redact under $$DESCEND should descend through 99 nesting levels and "
        "prune only the leaf without truncation or error",
    ),
]

# Property [Empty Structure Retention]: an already-empty embedded document or
# array of empty documents is retained under $$DESCEND.
REDACT_EMPTY_STRUCTURE_TESTS: list[StageTestCase] = [
    StageTestCase(
        "structural_empty_embedded_document_kept",
        docs=[{"_id": 1, "child": {}}],
        pipeline=[{"$redact": "$$DESCEND"}],
        expected=[{"_id": 1, "child": {}}],
        msg="$redact under $$DESCEND should keep an empty embedded document",
    ),
    StageTestCase(
        "structural_array_of_empty_documents_kept",
        docs=[{"_id": 1, "items": [{}, {}]}],
        pipeline=[{"$redact": "$$DESCEND"}],
        expected=[{"_id": 1, "items": [{}, {}]}],
        msg="$redact under $$DESCEND should keep an array of empty documents",
    ),
]

REDACT_DESCEND_STRUCTURE_TESTS = REDACT_STRUCTURAL_TESTS + REDACT_EMPTY_STRUCTURE_TESTS


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REDACT_DESCEND_STRUCTURE_TESTS))
def test_redact_descend_structure_cases(collection, test_case: StageTestCase):
    """Test $redact $$DESCEND traversal of deep nesting, large arrays, and empty containers."""
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
