"""
Tests for $stdDevPop computation under documents-mode window frame shapes.

Verifies the operator computes correct results given the 4 defined frame shapes:
whole-partition, cumulative, reverse-cumulative, and sliding.

Note: Stage-level frame boundary tests (under stages/setWindowFields/) verify
that the correct documents are selected into the frame (centered, trailing,
leading, non-overlapping, edge cases). These per-operator tests verify the
operator produces correct values given those documents.
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    BASIC_DOCS,
    WindowTestCase,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

STDDEVPOP_DOCUMENTS_FRAME_TESTS: list[WindowTestCase] = [
    # Property [Whole Partition]: unbounded-unbounded frame covers entire partition
    WindowTestCase(
        "whole_partition",
        docs=BASIC_DOCS,
        window={"documents": ["unbounded", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
            {"_id": 2, "partition": "A", "value": 20, "result": 14.142135623730951},
            {"_id": 3, "partition": "A", "value": 30, "result": 14.142135623730951},
            {"_id": 4, "partition": "A", "value": 40, "result": 14.142135623730951},
            {"_id": 5, "partition": "A", "value": 50, "result": 14.142135623730951},
        ],
        msg="whole partition stdDevPop should be sqrt(200)",
    ),
    # Property [Cumulative Frame]: expanding frame from start to current
    WindowTestCase(
        "cumulative",
        docs=BASIC_DOCS,
        window={"documents": ["unbounded", "current"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 0.0},
            {"_id": 2, "partition": "A", "value": 20, "result": 5.0},
            {"_id": 3, "partition": "A", "value": 30, "result": 8.16496580927726},
            {"_id": 4, "partition": "A", "value": 40, "result": 11.180339887498949},
            {"_id": 5, "partition": "A", "value": 50, "result": 14.142135623730951},
        ],
        msg="cumulative stdDevPop should grow",
    ),
    # Property [Reverse Cumulative Frame]: shrinking frame from current to end
    WindowTestCase(
        "reverse_cumulative",
        docs=BASIC_DOCS,
        window={"documents": ["current", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 14.142135623730951},
            {"_id": 2, "partition": "A", "value": 20, "result": 11.180339887498949},
            {"_id": 3, "partition": "A", "value": 30, "result": 8.16496580927726},
            {"_id": 4, "partition": "A", "value": 40, "result": 5.0},
            {"_id": 5, "partition": "A", "value": 50, "result": 0},
        ],
        msg="reverse-cumulative stdDevPop should shrink",
    ),
    # Property [Sliding Frame]: fixed-size window that moves with current row
    WindowTestCase(
        "sliding_centered",
        docs=BASIC_DOCS,
        window={"documents": [-1, 1]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 5.0},
            {"_id": 2, "partition": "A", "value": 20, "result": 8.16496580927726},
            {"_id": 3, "partition": "A", "value": 30, "result": 8.16496580927726},
            {"_id": 4, "partition": "A", "value": 40, "result": 8.16496580927726},
            {"_id": 5, "partition": "A", "value": 50, "result": 5.0},
        ],
        msg="centered sliding window [-1,1]",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STDDEVPOP_DOCUMENTS_FRAME_TESTS))
def test_stdDevPop_documents_frames(collection, test):
    """$stdDevPop with various documents-mode window frames."""
    result = run_window_operator(
        collection, "$stdDevPop", test.docs, test.window, sort_by=test.sort_by
    )
    assertSuccess(result, test.expected, msg=test.msg)
