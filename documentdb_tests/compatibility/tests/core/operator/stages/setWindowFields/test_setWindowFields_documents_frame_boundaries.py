"""
Tests for $setWindowFields documents-mode frame boundary selection.

Using $sum as a sample operator, verifies that document-based frame boundary
specifications correctly control which documents are selected into the window.

Covers: centered, trailing, leading, non-overlapping frames, and edge cases
(empty frame, single-element frame, frame wider than partition).

Note: These stage-level tests verify correct document selection into the frame.
Per-operator tests (under window/$operator/) verify the operator computes
correct results given those documents.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

BASIC_DOCS = [
    {"_id": 1, "partition": "A", "value": 1},
    {"_id": 2, "partition": "A", "value": 2},
    {"_id": 3, "partition": "A", "value": 4},
    {"_id": 4, "partition": "A", "value": 8},
    {"_id": 5, "partition": "A", "value": 16},
]


def _run_sum_window(collection, docs, window, sort_by=None):
    """Helper to run $sum with a given window spec."""
    if sort_by is None:
        sort_by = {"_id": 1}
    collection.insert_many(docs)
    stage = {
        "$setWindowFields": {
            "partitionBy": "$partition",
            "sortBy": sort_by,
            "output": {
                "result": {
                    "$sum": "$value",
                    "window": window,
                }
            },
        }
    }
    return execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": [stage], "cursor": {}},
    )


# Property [Centered Frame]: symmetric window around current row


def test_centered_frame(collection):
    """Centered window [-1, 1] includes one row before and one after current."""
    result = _run_sum_window(collection, BASIC_DOCS, {"documents": [-1, 1]})
    # Row 1: [1, 2] = 3 (no row before)
    # Row 2: [1, 2, 4] = 7
    # Row 3: [2, 4, 8] = 14
    # Row 4: [4, 8, 16] = 28
    # Row 5: [8, 16] = 24 (no row after)
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 3},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 14},
        {"_id": 4, "partition": "A", "value": 8, "result": 28},
        {"_id": 5, "partition": "A", "value": 16, "result": 24},
    ]
    assertSuccess(result, expected, msg="centered window [-1, 1] selects correct documents")


# Property [Trailing Frame]: window includes only current and preceding rows


def test_trailing_frame(collection):
    """Trailing window [-2, 0] includes up to 2 rows before and current."""
    result = _run_sum_window(collection, BASIC_DOCS, {"documents": [-2, 0]})
    # Row 1: [1] = 1
    # Row 2: [1, 2] = 3
    # Row 3: [1, 2, 4] = 7
    # Row 4: [2, 4, 8] = 14
    # Row 5: [4, 8, 16] = 28
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 1},
        {"_id": 2, "partition": "A", "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
        {"_id": 4, "partition": "A", "value": 8, "result": 14},
        {"_id": 5, "partition": "A", "value": 16, "result": 28},
    ]
    assertSuccess(result, expected, msg="trailing window [-2, 0] selects correct documents")


# Property [Leading Frame]: window includes only current and following rows


def test_leading_frame(collection):
    """Leading window [0, 2] includes current and up to 2 rows after."""
    result = _run_sum_window(collection, BASIC_DOCS, {"documents": [0, 2]})
    # Row 1: [1, 2, 4] = 7
    # Row 2: [2, 4, 8] = 14
    # Row 3: [4, 8, 16] = 28
    # Row 4: [8, 16] = 24
    # Row 5: [16] = 16
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 14},
        {"_id": 3, "partition": "A", "value": 4, "result": 28},
        {"_id": 4, "partition": "A", "value": 8, "result": 24},
        {"_id": 5, "partition": "A", "value": 16, "result": 16},
    ]
    assertSuccess(result, expected, msg="leading window [0, 2] selects correct documents")


# Property [Non-Overlapping Frame]: window excludes current row


def test_non_overlapping_both_before(collection):
    """Non-overlapping window [-3, -1] excludes current row, looks back only."""
    result = _run_sum_window(collection, BASIC_DOCS, {"documents": [-3, -1]})
    # Row 1: empty = 0
    # Row 2: [1] = 1
    # Row 3: [1, 2] = 3
    # Row 4: [1, 2, 4] = 7
    # Row 5: [2, 4, 8] = 14
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 0},
        {"_id": 2, "partition": "A", "value": 2, "result": 1},
        {"_id": 3, "partition": "A", "value": 4, "result": 3},
        {"_id": 4, "partition": "A", "value": 8, "result": 7},
        {"_id": 5, "partition": "A", "value": 16, "result": 14},
    ]
    assertSuccess(result, expected, msg="non-overlapping [-3, -1] excludes current row")


def test_non_overlapping_both_after(collection):
    """Non-overlapping window [1, 3] excludes current row, looks forward only."""
    result = _run_sum_window(collection, BASIC_DOCS, {"documents": [1, 3]})
    # Row 1: [2, 4, 8] = 14
    # Row 2: [4, 8, 16] = 28
    # Row 3: [8, 16] = 24
    # Row 4: [16] = 16
    # Row 5: empty = 0
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 14},
        {"_id": 2, "partition": "A", "value": 2, "result": 28},
        {"_id": 3, "partition": "A", "value": 4, "result": 24},
        {"_id": 4, "partition": "A", "value": 8, "result": 16},
        {"_id": 5, "partition": "A", "value": 16, "result": 0},
    ]
    assertSuccess(result, expected, msg="non-overlapping [1, 3] excludes current row")


# Property [Empty Frame]: window selects no documents


def test_empty_frame_returns_zero(collection):
    """Window far beyond partition edges selects no documents — $sum returns 0."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10},
        {"_id": 2, "partition": "A", "value": 20},
    ]
    result = _run_sum_window(collection, docs, {"documents": [5, 10]})
    expected = [
        {"_id": 1, "partition": "A", "value": 10, "result": 0},
        {"_id": 2, "partition": "A", "value": 20, "result": 0},
    ]
    assertSuccess(result, expected, msg="empty frame (beyond partition) returns 0 for $sum")


# Property [Single-Element Frame]: window [0, 0] selects only current row


def test_single_element_frame(collection):
    """Window [0, 0] selects only the current document."""
    result = _run_sum_window(collection, BASIC_DOCS, {"documents": [0, 0]})
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 1},
        {"_id": 2, "partition": "A", "value": 2, "result": 2},
        {"_id": 3, "partition": "A", "value": 4, "result": 4},
        {"_id": 4, "partition": "A", "value": 8, "result": 8},
        {"_id": 5, "partition": "A", "value": 16, "result": 16},
    ]
    assertSuccess(result, expected, msg="window [0, 0] selects only current document")


# Property [Wider Than Partition]: window extends beyond partition edges, clamped


def test_wider_than_partition(collection):
    """Window [-100, 100] extends far beyond partition — equivalent to unbounded."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
    ]
    result = _run_sum_window(collection, docs, {"documents": [-100, 100]})
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
    ]
    assertSuccess(result, expected, msg="wider-than-partition clamped to edges")


# Property [Default Window]: no window key defaults to whole partition


def test_default_window_no_window_key(collection):
    """No explicit window key defaults to unbounded-unbounded (whole partition)."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {"$sum": "$value"},
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
    ]
    assertSuccess(result, expected, msg="no window key defaults to whole partition")


def test_empty_window_object(collection):
    """Empty window object {} is equivalent to no window (whole partition)."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
    ]
    assertSuccess(result, expected, msg="empty window {} = whole partition")


# Property [No SortBy]: documents window works without sortBy for unbounded frames


def test_no_sortby_with_unbounded_documents_window(collection):
    """Documents window [unbounded, unbounded] works without sortBy."""
    docs = [
        {"_id": 1, "partition": "A", "value": 1},
        {"_id": 2, "partition": "A", "value": 2},
        {"_id": 3, "partition": "A", "value": 4},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "output": {
                            "result": {
                                "$sum": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    expected = [
        {"_id": 1, "partition": "A", "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "value": 4, "result": 7},
    ]
    assertSuccess(
        result, expected, ignore_doc_order=True, msg="no sortBy with unbounded documents window"
    )
