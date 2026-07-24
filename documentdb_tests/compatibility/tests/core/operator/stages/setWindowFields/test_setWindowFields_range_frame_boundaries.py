"""
Tests for $setWindowFields range-mode frame boundary selection.

Using $sum as a sample operator, verifies that numeric range-based frame bounds
correctly define the window of documents selected for computation.

Covers: symmetric range, asymmetric range, unbounded/current combinations,
value-ties inclusion, gaps in sortBy values, and empty range frames.

Note: These stage-level tests verify correct document selection by range value.
Per-operator tests (under window/$operator/) verify the operator computes
correct results given those documents.
"""

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def _run_sum_range_window(collection, docs, window, sort_by=None):
    """Helper to run $sum with a range window spec."""
    if sort_by is None:
        sort_by = {"score": 1}
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


# Property [Symmetric Range]: range [-N, N] includes documents within N of current sortBy value


def test_range_symmetric_sliding(collection):
    """Range [-5, 5] includes documents whose sortBy value is within 5 of current."""
    docs = [
        {"_id": 1, "partition": "A", "score": 0, "value": 1},
        {"_id": 2, "partition": "A", "score": 3, "value": 2},
        {"_id": 3, "partition": "A", "score": 10, "value": 4},
        {"_id": 4, "partition": "A", "score": 12, "value": 8},
        {"_id": 5, "partition": "A", "score": 20, "value": 16},
    ]
    result = _run_sum_range_window(collection, docs, {"range": [-5, 5]})
    # score=0:  range [-5, 5] -> scores in [-5, 5] -> includes 0, 3 -> 1+2 = 3
    # score=3:  range [-2, 8] -> scores in [-2, 8] -> includes 0, 3 -> 1+2 = 3
    # score=10: range [5, 15] -> scores in [5, 15] -> includes 10, 12 -> 4+8 = 12
    # score=12: range [7, 17] -> scores in [7, 17] -> includes 10, 12 -> 4+8 = 12
    # score=20: range [15, 25] -> scores in [15, 25] -> includes 20 -> 16
    expected = [
        {"_id": 1, "partition": "A", "score": 0, "value": 1, "result": 3},
        {"_id": 2, "partition": "A", "score": 3, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "score": 10, "value": 4, "result": 12},
        {"_id": 4, "partition": "A", "score": 12, "value": 8, "result": 12},
        {"_id": 5, "partition": "A", "score": 20, "value": 16, "result": 16},
    ]
    assertSuccess(result, expected, msg="symmetric range [-5, 5] selects correct documents")


# Property [Unbounded Range]: unbounded combined with numeric bound


def test_range_unbounded_to_current(collection):
    """Range [unbounded, current] includes all documents up to current sortBy value."""
    docs = [
        {"_id": 1, "partition": "A", "score": 1, "value": 1},
        {"_id": 2, "partition": "A", "score": 2, "value": 2},
        {"_id": 3, "partition": "A", "score": 3, "value": 4},
        {"_id": 4, "partition": "A", "score": 4, "value": 8},
    ]
    result = _run_sum_range_window(collection, docs, {"range": ["unbounded", "current"]})
    expected = [
        {"_id": 1, "partition": "A", "score": 1, "value": 1, "result": 1},
        {"_id": 2, "partition": "A", "score": 2, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "score": 3, "value": 4, "result": 7},
        {"_id": 4, "partition": "A", "score": 4, "value": 8, "result": 15},
    ]
    assertSuccess(result, expected, msg="range [unbounded, current] cumulative selection")


def test_range_current_to_unbounded(collection):
    """Range [current, unbounded] includes current and all following documents."""
    docs = [
        {"_id": 1, "partition": "A", "score": 1, "value": 1},
        {"_id": 2, "partition": "A", "score": 2, "value": 2},
        {"_id": 3, "partition": "A", "score": 3, "value": 4},
        {"_id": 4, "partition": "A", "score": 4, "value": 8},
    ]
    result = _run_sum_range_window(collection, docs, {"range": ["current", "unbounded"]})
    expected = [
        {"_id": 1, "partition": "A", "score": 1, "value": 1, "result": 15},
        {"_id": 2, "partition": "A", "score": 2, "value": 2, "result": 14},
        {"_id": 3, "partition": "A", "score": 3, "value": 4, "result": 12},
        {"_id": 4, "partition": "A", "score": 4, "value": 8, "result": 8},
    ]
    assertSuccess(result, expected, msg="range [current, unbounded] reverse-cumulative selection")


# Property [Value-Ties]: range [0, 0] includes all docs with identical sortBy value


def test_range_zero_zero_includes_ties(collection):
    """Range [0, 0] includes all documents sharing the same sortBy value."""
    docs = [
        {"_id": 1, "partition": "A", "score": 5, "value": 1},
        {"_id": 2, "partition": "A", "score": 5, "value": 2},
        {"_id": 3, "partition": "A", "score": 5, "value": 4},
        {"_id": 4, "partition": "A", "score": 10, "value": 8},
    ]
    result = _run_sum_range_window(collection, docs, {"range": [0, 0]})
    # score=5 ties: all three included -> 1+2+4 = 7
    # score=10: only itself -> 8
    expected = [
        {"_id": 1, "partition": "A", "score": 5, "value": 1, "result": 7},
        {"_id": 2, "partition": "A", "score": 5, "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "score": 5, "value": 4, "result": 7},
        {"_id": 4, "partition": "A", "score": 10, "value": 8, "result": 8},
    ]
    assertSuccess(result, expected, msg="range [0, 0] includes all value-ties")


# Property [Gaps in SortBy]: documents with large gaps in sortBy values are excluded


def test_range_with_gaps(collection):
    """Range window correctly excludes documents with large sortBy gaps."""
    docs = [
        {"_id": 1, "partition": "A", "score": 1, "value": 1},
        {"_id": 2, "partition": "A", "score": 2, "value": 2},
        {"_id": 3, "partition": "A", "score": 100, "value": 4},
        {"_id": 4, "partition": "A", "score": 101, "value": 8},
    ]
    result = _run_sum_range_window(collection, docs, {"range": [-5, 5]})
    # score=1: range [-4, 6] -> includes 1, 2 -> 1+2 = 3
    # score=2: range [-3, 7] -> includes 1, 2 -> 1+2 = 3
    # score=100: range [95, 105] -> includes 100, 101 -> 4+8 = 12
    # score=101: range [96, 106] -> includes 100, 101 -> 4+8 = 12
    expected = [
        {"_id": 1, "partition": "A", "score": 1, "value": 1, "result": 3},
        {"_id": 2, "partition": "A", "score": 2, "value": 2, "result": 3},
        {"_id": 3, "partition": "A", "score": 100, "value": 4, "result": 12},
        {"_id": 4, "partition": "A", "score": 101, "value": 8, "result": 12},
    ]
    assertSuccess(result, expected, msg="range excludes documents with large sortBy gaps")


# Property [Empty Range]: range that includes no documents


def test_range_empty_returns_zero(collection):
    """Range window selecting no documents returns 0 for $sum."""
    docs = [
        {"_id": 1, "partition": "A", "score": 1, "value": 10},
        {"_id": 2, "partition": "A", "score": 100, "value": 20},
    ]
    result = _run_sum_range_window(collection, docs, {"range": [-2, -1]})
    # score=1: range [-1, 0] -> no doc with score in [-1, 0] -> 0
    # score=100: range [98, 99] -> no doc with score in [98, 99] -> 0
    expected = [
        {"_id": 1, "partition": "A", "score": 1, "value": 10, "result": 0},
        {"_id": 2, "partition": "A", "score": 100, "value": 20, "result": 0},
    ]
    assertSuccess(result, expected, msg="empty range frame returns 0 for $sum")


# Property [Fractional Range]: non-integer range bounds


def test_range_fractional_bounds(collection):
    """Range with fractional bounds correctly includes documents."""
    docs = [
        {"_id": 1, "partition": "A", "score": 1.0, "value": 1},
        {"_id": 2, "partition": "A", "score": 1.5, "value": 2},
        {"_id": 3, "partition": "A", "score": 2.0, "value": 4},
        {"_id": 4, "partition": "A", "score": 3.0, "value": 8},
    ]
    result = _run_sum_range_window(collection, docs, {"range": [-0.5, 0.5]})
    # score=1.0: range [0.5, 1.5] -> includes 1.0, 1.5 -> 1+2 = 3
    # score=1.5: range [1.0, 2.0] -> includes 1.0, 1.5, 2.0 -> 1+2+4 = 7
    # score=2.0: range [1.5, 2.5] -> includes 1.5, 2.0 -> 2+4 = 6
    # score=3.0: range [2.5, 3.5] -> includes 3.0 -> 8
    expected = [
        {"_id": 1, "partition": "A", "score": 1.0, "value": 1, "result": 3},
        {"_id": 2, "partition": "A", "score": 1.5, "value": 2, "result": 7},
        {"_id": 3, "partition": "A", "score": 2.0, "value": 4, "result": 6},
        {"_id": 4, "partition": "A", "score": 3.0, "value": 8, "result": 8},
    ]
    assertSuccess(result, expected, msg="fractional range bounds select correct documents")
