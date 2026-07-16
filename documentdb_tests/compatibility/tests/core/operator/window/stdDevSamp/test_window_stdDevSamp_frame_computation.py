"""
Tests for $stdDevSamp computation under documents-mode window frame shapes.

Verifies the operator computes correct results given the 4 defined frame shapes:
whole-partition, cumulative, reverse-cumulative, and sliding.

Key difference from $stdDevPop: single-element frames return null (N-1 denominator
is undefined for N=1).

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

STDDEVSAMP_DOCUMENTS_FRAME_TESTS: list[WindowTestCase] = [
    # Property [Whole Partition]: unbounded-unbounded frame covers entire partition
    WindowTestCase(
        "whole_partition",
        docs=BASIC_DOCS,
        window={"documents": ["unbounded", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 15.811388300841896},
            {"_id": 2, "partition": "A", "value": 20, "result": 15.811388300841896},
            {"_id": 3, "partition": "A", "value": 30, "result": 15.811388300841896},
            {"_id": 4, "partition": "A", "value": 40, "result": 15.811388300841896},
            {"_id": 5, "partition": "A", "value": 50, "result": 15.811388300841896},
        ],
        msg="whole partition stdDevSamp = sqrt(250)",
    ),
    # Property [Cumulative Frame]: expanding frame from start to current
    WindowTestCase(
        "cumulative",
        docs=BASIC_DOCS,
        window={"documents": ["unbounded", "current"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": None},
            {"_id": 2, "partition": "A", "value": 20, "result": 7.0710678118654755},
            {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
            {"_id": 4, "partition": "A", "value": 40, "result": 12.909944487358056},
            {"_id": 5, "partition": "A", "value": 50, "result": 15.811388300841896},
        ],
        msg="cumulative stdDevSamp grows; first row is null (N=1 undefined)",
    ),
    # Property [Reverse Cumulative Frame]: shrinking frame from current to end
    WindowTestCase(
        "reverse_cumulative",
        docs=BASIC_DOCS,
        window={"documents": ["current", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 15.811388300841896},
            {"_id": 2, "partition": "A", "value": 20, "result": 12.909944487358056},
            {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
            {"_id": 4, "partition": "A", "value": 40, "result": 7.0710678118654755},
            {"_id": 5, "partition": "A", "value": 50, "result": None},
        ],
        msg="reverse-cumulative stdDevSamp shrinks; last row is null (N=1 undefined)",
    ),
    # Property [Sliding Frame]: fixed-size window that moves with current row
    WindowTestCase(
        "sliding_centered",
        docs=BASIC_DOCS,
        window={"documents": [-1, 1]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": 7.0710678118654755},
            {"_id": 2, "partition": "A", "value": 20, "result": 10.0},
            {"_id": 3, "partition": "A", "value": 30, "result": 10.0},
            {"_id": 4, "partition": "A", "value": 40, "result": 10.0},
            {"_id": 5, "partition": "A", "value": 50, "result": 7.0710678118654755},
        ],
        msg="centered sliding window [-1,1]; edge rows have 2 elements",
    ),
]


@pytest.mark.parametrize("test", pytest_params(STDDEVSAMP_DOCUMENTS_FRAME_TESTS))
def test_stdDevSamp_documents_frames(collection, test):
    """$stdDevSamp with various documents-mode window frames."""
    result = run_window_operator(
        collection, "$stdDevSamp", test.docs, test.window, sort_by=test.sort_by
    )
    assertSuccess(result, test.expected, msg=test.msg)
