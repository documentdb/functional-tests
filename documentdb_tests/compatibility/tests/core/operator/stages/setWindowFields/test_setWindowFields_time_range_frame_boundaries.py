"""
Tests for $setWindowFields time-range-mode frame boundary selection.

Using $sum as a sample operator, verifies that time-based range frame bounds
correctly define the window of documents selected for computation.

Covers: day unit sliding, hour unit sliding, unbounded/current with time unit,
gaps in dates excluding documents, and multiple time units.

Note: These stage-level tests verify correct document selection by time range.
Per-operator tests (under window/$operator/) verify the operator computes
correct results given those documents.
"""

from datetime import datetime, timezone

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command


def _run_sum_time_range_window(collection, docs, window, sort_by=None):
    """Helper to run $sum with a time-range window spec."""
    if sort_by is None:
        sort_by = {"date": 1}
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


# Property [Day Unit]: time-range with unit=day selects documents within N days


def test_time_range_day_sliding(collection):
    """Time-range [-1, 1] unit=day includes documents within 1 day of current."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 1},
        {"_id": 2, "partition": "A", "date": datetime(2023, 1, 2, tzinfo=timezone.utc), "value": 2},
        {"_id": 3, "partition": "A", "date": datetime(2023, 1, 3, tzinfo=timezone.utc), "value": 4},
        {"_id": 4, "partition": "A", "date": datetime(2023, 1, 5, tzinfo=timezone.utc), "value": 8},
    ]
    result = _run_sum_time_range_window(collection, docs, {"range": [-1, 1], "unit": "day"})
    # Jan 1: range [Dec 31, Jan 2] -> includes Jan 1, Jan 2 -> 1+2 = 3
    # Jan 2: range [Jan 1, Jan 3] -> includes Jan 1, Jan 2, Jan 3 -> 1+2+4 = 7
    # Jan 3: range [Jan 2, Jan 4] -> includes Jan 2, Jan 3 -> 2+4 = 6
    # Jan 5: range [Jan 4, Jan 6] -> includes Jan 5 only -> 8
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 2, tzinfo=timezone.utc),
            "value": 2,
            "result": 7,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 3, tzinfo=timezone.utc),
            "value": 4,
            "result": 6,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 1, 5, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range day unit [-1, 1] selects correct documents")


# Property [Hour Unit]: time-range with unit=hour selects documents within N hours


def test_time_range_hour_sliding(collection):
    """Time-range [-2, 2] unit=hour includes documents within 2 hours of current."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
            "value": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc),
            "value": 2,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 3, 0, tzinfo=timezone.utc),
            "value": 4,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 1, 1, 6, 0, tzinfo=timezone.utc),
            "value": 8,
        },
    ]
    result = _run_sum_time_range_window(collection, docs, {"range": [-2, 2], "unit": "hour"})
    # 00:00: range [22:00 prev, 02:00] -> includes 00:00, 01:00 -> 1+2 = 3
    # 01:00: range [23:00 prev, 03:00] -> includes 00:00, 01:00, 03:00 -> 1+2+4 = 7
    # 03:00: range [01:00, 05:00] -> includes 01:00, 03:00 -> 2+4 = 6
    # 06:00: range [04:00, 08:00] -> includes 06:00 only -> 8
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 1, 0, tzinfo=timezone.utc),
            "value": 2,
            "result": 7,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 3, 0, tzinfo=timezone.utc),
            "value": 4,
            "result": 6,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 1, 1, 6, 0, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range hour unit [-2, 2] selects correct documents")


# Property [Unbounded Time Range]: unbounded combined with time unit


def test_time_range_unbounded_to_current(collection):
    """Time-range [unbounded, current] with unit includes all preceding documents."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 1},
        {"_id": 2, "partition": "A", "date": datetime(2023, 1, 2, tzinfo=timezone.utc), "value": 2},
        {"_id": 3, "partition": "A", "date": datetime(2023, 1, 3, tzinfo=timezone.utc), "value": 4},
    ]
    result = _run_sum_time_range_window(
        collection, docs, {"range": ["unbounded", "current"], "unit": "day"}
    )
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "value": 1,
            "result": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 2, tzinfo=timezone.utc),
            "value": 2,
            "result": 3,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 3, tzinfo=timezone.utc),
            "value": 4,
            "result": 7,
        },
    ]
    assertSuccess(result, expected, msg="time-range [unbounded, current] cumulative selection")


# Property [Gap Exclusion]: documents far apart in time are excluded from frame


def test_time_range_gap_exclusion(collection):
    """Time-range window excludes documents separated by large time gaps."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 1},
        {"_id": 2, "partition": "A", "date": datetime(2023, 1, 2, tzinfo=timezone.utc), "value": 2},
        {"_id": 3, "partition": "A", "date": datetime(2023, 6, 1, tzinfo=timezone.utc), "value": 4},
    ]
    result = _run_sum_time_range_window(collection, docs, {"range": [-7, 7], "unit": "day"})
    # Jan 1: range [Dec 25, Jan 8] -> includes Jan 1, Jan 2 -> 1+2 = 3
    # Jan 2: range [Dec 26, Jan 9] -> includes Jan 1, Jan 2 -> 1+2 = 3
    # Jun 1: range [May 25, Jun 8] -> includes Jun 1 only -> 4
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 2, tzinfo=timezone.utc),
            "value": 2,
            "result": 3,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "value": 4,
            "result": 4,
        },
    ]
    assertSuccess(result, expected, msg="time-range excludes documents with large time gaps")
