"""Tests for the $replaceWith aggregation stage."""

from __future__ import annotations

from typing import Any

import pytest

from documentdb_tests.compatibility.tests.core.operator.stages.utils.shared_limits import (
    BIG_STORED_STRING_BYTES,
    BOUNDARY_PAD_BYTES,
    MAX_OUTPUT_DOC_SIZE,
    MAX_STORED_NESTING_DEPTH,
    OVER_LIMIT_PAD_BYTES,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.error_codes import (
    BSON_OBJECT_TOO_LARGE_ERROR,
    OVERFLOW_ERROR,
)
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params


def _nest(depth: int, leaf: Any) -> Any:
    """Build a value nested ``depth`` single-key objects deep around ``leaf``."""
    value: Any = leaf
    for _ in range(depth):
        value = {"a": value}
    return value


# The maximum object nesting depth accepted in a constructed replacement-document
# literal; one level deeper is rejected with an overflow error. This is one level
# deeper than $replaceRoot accepts, because $replaceRoot wraps the literal in an
# extra newRoot specification level that consumes one unit of the depth budget.
_MAX_NESTING_DEPTH = 198


# Property [Deeply Nested Promotion Accepted]: a sub-document stored at the
# maximum nesting depth can be promoted to the top level.
REPLACEWITH_DEEP_PROMOTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        "deep_promotion_max_stored_depth",
        docs=[{"_id": 1, "data": _nest(depth=MAX_STORED_NESTING_DEPTH, leaf=1)}],
        pipeline=[{"$replaceWith": "$data"}],
        expected=[_nest(depth=MAX_STORED_NESTING_DEPTH, leaf=1)],
        msg="$replaceWith should accept promoting a sub-document stored at the maximum depth",
    ),
]

# Property [Size Boundary Accepted]: a constructed replacement document is
# accepted at the maximum output document size, enforced on the output even when
# the input is within the standard limit.
REPLACEWITH_SIZE_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "size_boundary_max_output_accepted",
        docs=[{"_id": 1, "data": {"s": "x" * BIG_STORED_STRING_BYTES}}],
        pipeline=[
            {"$replaceWith": {"$mergeObjects": ["$data", {"pad": "y" * BOUNDARY_PAD_BYTES}]}},
            {"$project": {"_id": 0, "size": {"$bsonSize": "$$ROOT"}}},
        ],
        expected=[{"size": MAX_OUTPUT_DOC_SIZE}],
        msg="$replaceWith should accept a constructed output document at the maximum size",
    ),
]

# Property [Nesting Boundary Accepted]: a constructed replacement-document
# literal is accepted up to its maximum nesting depth.
REPLACEWITH_NESTING_BOUNDARY_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nesting_boundary_max_depth_accepted",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": _nest(depth=_MAX_NESTING_DEPTH, leaf=1)}],
        expected=[_nest(depth=_MAX_NESTING_DEPTH, leaf=1)],
        msg="$replaceWith should accept a constructed literal at the maximum nesting depth",
    ),
]

# Property [Size Limit Error]: a constructed output document one byte over the
# maximum output size produces a BSON-object-too-large error, enforced on the
# output document even when the input document is within the standard limit.
REPLACEWITH_SIZE_LIMIT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "size_limit_one_over_rejected",
        docs=[{"_id": 1, "data": {"s": "x" * BIG_STORED_STRING_BYTES}}],
        pipeline=[
            {"$replaceWith": {"$mergeObjects": ["$data", {"pad": "y" * OVER_LIMIT_PAD_BYTES}]}}
        ],
        error_code=BSON_OBJECT_TOO_LARGE_ERROR,
        msg="$replaceWith should reject an output document one byte over the maximum size",
    ),
]

# Property [Nesting Limit Error]: a constructed replacement-document literal one
# level deeper than the maximum nesting depth produces an overflow error.
REPLACEWITH_NESTING_LIMIT_ERROR_TESTS: list[StageTestCase] = [
    StageTestCase(
        "nesting_limit_one_over_rejected",
        docs=[{"_id": 1}],
        pipeline=[{"$replaceWith": _nest(depth=_MAX_NESTING_DEPTH + 1, leaf=1)}],
        error_code=OVERFLOW_ERROR,
        msg="$replaceWith should reject a literal one level over the maximum nesting depth",
    ),
]

REPLACEWITH_LIMITS_TESTS: list[StageTestCase] = (
    REPLACEWITH_DEEP_PROMOTION_TESTS
    + REPLACEWITH_SIZE_BOUNDARY_TESTS
    + REPLACEWITH_NESTING_BOUNDARY_TESTS
    + REPLACEWITH_SIZE_LIMIT_ERROR_TESTS
    + REPLACEWITH_NESTING_LIMIT_ERROR_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(REPLACEWITH_LIMITS_TESTS))
def test_replaceWith_limits_cases(collection, test_case: StageTestCase):
    """Test $replaceWith limits cases."""
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
        ignore_doc_order=True,
    )
