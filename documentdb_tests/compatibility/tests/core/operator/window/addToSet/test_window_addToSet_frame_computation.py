"""
Tests for $addToSet computation under documents-mode window frame shapes.

Verifies the correct set given the documents in each frame shape (whole,
cumulative, reverse-cumulative, sliding) plus the empty-frame result ([]). Input
has duplicate values so dedup is observable, and the sliding frame shows a value
leaving the set as its documents exit. Results compared with ignore_order_in=["result"].
"""

import pytest

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    WindowTestCase,
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.parametrize import pytest_params

# Values with duplicates so dedup within each frame is visible.
FRAME_DOCS = [
    {"_id": 1, "partition": "A", "value": 10},
    {"_id": 2, "partition": "A", "value": 10},
    {"_id": 3, "partition": "A", "value": 20},
    {"_id": 4, "partition": "A", "value": 30},
    {"_id": 5, "partition": "A", "value": 20},
]

EMPTY_FRAME_DOCS = [
    {"_id": 1, "partition": "A", "value": 10},
    {"_id": 2, "partition": "A", "value": 20},
    {"_id": 3, "partition": "A", "value": 30},
]

ADDTOSET_FRAME_TESTS: list[WindowTestCase] = [
    # Property [Whole Partition]: unbounded-unbounded frame -> set of all distinct values.
    WindowTestCase(
        "whole_partition",
        docs=FRAME_DOCS,
        window={"documents": ["unbounded", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": [10, 20, 30]},
            {"_id": 2, "partition": "A", "value": 10, "result": [10, 20, 30]},
            {"_id": 3, "partition": "A", "value": 20, "result": [10, 20, 30]},
            {"_id": 4, "partition": "A", "value": 30, "result": [10, 20, 30]},
            {"_id": 5, "partition": "A", "value": 20, "result": [10, 20, 30]},
        ],
        msg="whole partition -> set of all distinct values",
    ),
    # Property [Cumulative Frame]: expanding frame from start to current; set grows with dedup.
    WindowTestCase(
        "cumulative",
        docs=FRAME_DOCS,
        window={"documents": ["unbounded", "current"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": [10]},
            {"_id": 2, "partition": "A", "value": 10, "result": [10]},
            {"_id": 3, "partition": "A", "value": 20, "result": [10, 20]},
            {"_id": 4, "partition": "A", "value": 30, "result": [10, 20, 30]},
            {"_id": 5, "partition": "A", "value": 20, "result": [10, 20, 30]},
        ],
        msg="cumulative frame -> expanding deduplicated set",
    ),
    # Property [Reverse Cumulative Frame]: shrinking frame from current to end.
    WindowTestCase(
        "reverse_cumulative",
        docs=FRAME_DOCS,
        window={"documents": ["current", "unbounded"]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": [10, 20, 30]},
            {"_id": 2, "partition": "A", "value": 10, "result": [10, 20, 30]},
            {"_id": 3, "partition": "A", "value": 20, "result": [20, 30]},
            {"_id": 4, "partition": "A", "value": 30, "result": [20, 30]},
            {"_id": 5, "partition": "A", "value": 20, "result": [20]},
        ],
        msg="reverse-cumulative frame -> shrinking deduplicated set",
    ),
    # Property [Sliding Frame]: fixed-size window; demonstrates removal as values exit the frame.
    WindowTestCase(
        "sliding_centered",
        docs=FRAME_DOCS,
        window={"documents": [-1, 1]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": [10]},
            {"_id": 2, "partition": "A", "value": 10, "result": [10, 20]},
            {"_id": 3, "partition": "A", "value": 20, "result": [10, 20, 30]},
            {"_id": 4, "partition": "A", "value": 30, "result": [20, 30]},
            {"_id": 5, "partition": "A", "value": 20, "result": [20, 30]},
        ],
        msg="centered sliding window [-1,1]; value 10 leaves the set as its docs exit the frame",
    ),
    # Property [Empty Frame]: a frame selecting no documents -> [].
    WindowTestCase(
        "empty_frame",
        docs=EMPTY_FRAME_DOCS,
        window={"documents": [-3, -2]},
        expected=[
            {"_id": 1, "partition": "A", "value": 10, "result": []},
            {"_id": 2, "partition": "A", "value": 20, "result": []},
            {"_id": 3, "partition": "A", "value": 30, "result": [10]},
        ],
        msg="empty frame -> [] (early rows select no documents)",
    ),
]


@pytest.mark.parametrize("test", pytest_params(ADDTOSET_FRAME_TESTS))
def test_addToSet_documents_frames(collection, test):
    """$addToSet with various documents-mode window frames produces the correct set."""
    result = run_window_operator(
        collection, "$addToSet", test.docs, test.window, sort_by=test.sort_by
    )
    assertSuccess(result, test.expected, msg=test.msg, ignore_order_in=["result"])
