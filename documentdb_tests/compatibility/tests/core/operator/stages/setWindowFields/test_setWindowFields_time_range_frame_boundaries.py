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

from documentdb_tests.compatibility.tests.core.operator.window.utils.window_test_case import (
    run_window_operator,
)
from documentdb_tests.framework.assertions import assertSuccess

# Property [Day Unit]: time-range with unit=day selects documents within N days


def test_time_range_day_sliding(collection):
    """Time-range [-1, 1] unit=day includes documents within 1 day of current."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 1},
        {"_id": 2, "partition": "A", "date": datetime(2023, 1, 2, tzinfo=timezone.utc), "value": 2},
        {"_id": 3, "partition": "A", "date": datetime(2023, 1, 3, tzinfo=timezone.utc), "value": 4},
        {"_id": 4, "partition": "A", "date": datetime(2023, 1, 5, tzinfo=timezone.utc), "value": 8},
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "day"}, sort_by={"date": 1}
    )
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
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-2, 2], "unit": "hour"}, sort_by={"date": 1}
    )
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
    result = run_window_operator(
        collection,
        "$sum",
        docs,
        {"range": ["unbounded", "current"], "unit": "day"},
        sort_by={"date": 1},
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
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-7, 7], "unit": "day"}, sort_by={"date": 1}
    )
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


# Property [Month Unit - Variable Length]: month unit handles variable-length months correctly


def test_time_range_month_sliding(collection):
    """Time-range [-1, 1] unit=month includes documents within 1 month of current."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 15, tzinfo=timezone.utc),
            "value": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 2, 15, tzinfo=timezone.utc),
            "value": 2,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 3, 15, tzinfo=timezone.utc),
            "value": 4,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 5, 15, tzinfo=timezone.utc),
            "value": 8,
        },
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "month"}, sort_by={"date": 1}
    )
    # Jan 15: range [Dec 15, Feb 15] -> includes Jan 15, Feb 15 -> 1+2 = 3
    # Feb 15: range [Jan 15, Mar 15] -> includes Jan 15, Feb 15, Mar 15 -> 1+2+4 = 7
    # Mar 15: range [Feb 15, Apr 15] -> includes Feb 15, Mar 15 -> 2+4 = 6
    # May 15: range [Apr 15, Jun 15] -> includes May 15 only -> 8
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 15, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 2, 15, tzinfo=timezone.utc),
            "value": 2,
            "result": 7,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 3, 15, tzinfo=timezone.utc),
            "value": 4,
            "result": 6,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 5, 15, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range month unit [-1, 1] selects correct documents")


# Property [Minute Unit]: time-range with unit=minute selects documents within N minutes


def test_time_range_minute_sliding(collection):
    """Time-range [-1, 1] unit=minute includes documents within 1 minute of current."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "value": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
            "value": 2,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 3, 0, tzinfo=timezone.utc),
            "value": 4,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 5, 0, tzinfo=timezone.utc),
            "value": 8,
        },
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "minute"}, sort_by={"date": 1}
    )
    # 00:00: range [23:59 prev, 00:01] -> includes 00:00, 00:01 -> 1+2 = 3
    # 00:01: range [00:00, 00:02] -> includes 00:00, 00:01 -> 1+2 = 3
    # 00:03: range [00:02, 00:04] -> includes 00:03 only -> 4
    # 00:05: range [00:04, 00:06] -> includes 00:05 only -> 8
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
            "value": 2,
            "result": 3,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 3, 0, tzinfo=timezone.utc),
            "value": 4,
            "result": 4,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 5, 0, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range minute unit [-1, 1] selects correct documents")


# Property [Second Unit]: time-range with unit=second selects documents within N seconds


def test_time_range_second_sliding(collection):
    """Time-range [-1, 1] unit=second includes documents within 1 second of current."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "value": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            "value": 2,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 3, tzinfo=timezone.utc),
            "value": 4,
        },
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "second"}, sort_by={"date": 1}
    )
    # 00:00:00: range [-1s, +1s] -> includes 00:00:00, 00:00:01 -> 1+2 = 3
    # 00:00:01: range [0s, +2s] -> includes 00:00:00, 00:00:01 -> 1+2 = 3
    # 00:00:03: range [+2s, +4s] -> includes 00:00:03 only -> 4
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
            "value": 2,
            "result": 3,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 3, tzinfo=timezone.utc),
            "value": 4,
            "result": 4,
        },
    ]
    assertSuccess(result, expected, msg="time-range second unit [-1, 1] selects correct documents")


# Property [Millisecond Unit]: time-range with unit=millisecond selects documents within N ms


def test_time_range_millisecond_sliding(collection):
    """Time-range [-1, 1] unit=millisecond includes documents within 1ms of current."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
            "value": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
            "value": 2,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, 3000, tzinfo=timezone.utc),
            "value": 4,
        },
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "millisecond"}, sort_by={"date": 1}
    )
    # +0ms: range [-1ms, +1ms] -> includes +0ms, +1ms -> 1+2 = 3
    # +1ms: range [+0ms, +2ms] -> includes +0ms, +1ms -> 1+2 = 3
    # +3ms: range [+2ms, +4ms] -> includes +3ms only -> 4
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, 1000, tzinfo=timezone.utc),
            "value": 2,
            "result": 3,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 1, 0, 0, 0, 3000, tzinfo=timezone.utc),
            "value": 4,
            "result": 4,
        },
    ]
    assertSuccess(
        result, expected, msg="time-range millisecond unit [-1, 1] selects correct documents"
    )


# Property [Week Unit]: time-range with unit=week selects documents within N weeks


def test_time_range_week_sliding(collection):
    """Time-range [-1, 1] unit=week includes documents within 1 week of current."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2023, 1, 1, tzinfo=timezone.utc), "value": 1},
        {"_id": 2, "partition": "A", "date": datetime(2023, 1, 8, tzinfo=timezone.utc), "value": 2},
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 15, tzinfo=timezone.utc),
            "value": 4,
        },
        {"_id": 4, "partition": "A", "date": datetime(2023, 2, 1, tzinfo=timezone.utc), "value": 8},
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "week"}, sort_by={"date": 1}
    )
    # Jan 1: range [Dec 25, Jan 8] -> includes Jan 1, Jan 8 -> 1+2 = 3
    # Jan 8: range [Jan 1, Jan 15] -> includes Jan 1, Jan 8, Jan 15 -> 1+2+4 = 7
    # Jan 15: range [Jan 8, Jan 22] -> includes Jan 8, Jan 15 -> 2+4 = 6
    # Feb 1: range [Jan 25, Feb 8] -> includes Feb 1 only -> 8
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
            "date": datetime(2023, 1, 8, tzinfo=timezone.utc),
            "value": 2,
            "result": 7,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 1, 15, tzinfo=timezone.utc),
            "value": 4,
            "result": 6,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2023, 2, 1, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range week unit [-1, 1] selects correct documents")


# Property [Quarter Unit - Variable Length]: quarter unit handles variable-length quarters


def test_time_range_quarter_sliding(collection):
    """Time-range [-1, 1] unit=quarter includes documents within 1 quarter of current."""
    docs = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 15, tzinfo=timezone.utc),
            "value": 1,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 4, 15, tzinfo=timezone.utc),
            "value": 2,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 7, 15, tzinfo=timezone.utc),
            "value": 4,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2024, 1, 15, tzinfo=timezone.utc),
            "value": 8,
        },
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "quarter"}, sort_by={"date": 1}
    )
    # Jan 15 2023: range [Oct 15 2022, Apr 15 2023] -> includes Jan 15, Apr 15 -> 1+2 = 3
    # Apr 15 2023: range [Jan 15, Jul 15] -> includes Jan 15, Apr 15, Jul 15 -> 1+2+4 = 7
    # Jul 15 2023: range [Apr 15, Oct 15] -> includes Apr 15, Jul 15 -> 2+4 = 6
    # Jan 15 2024: range [Oct 15 2023, Apr 15 2024] -> includes Jan 15 2024 only -> 8
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2023, 1, 15, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 4, 15, tzinfo=timezone.utc),
            "value": 2,
            "result": 7,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2023, 7, 15, tzinfo=timezone.utc),
            "value": 4,
            "result": 6,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2024, 1, 15, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range quarter unit [-1, 1] selects correct documents")


# Property [Year Unit - Variable Length]: year unit handles leap years correctly


def test_time_range_year_sliding(collection):
    """Time-range [-1, 1] unit=year includes documents within 1 year of current."""
    docs = [
        {"_id": 1, "partition": "A", "date": datetime(2022, 6, 1, tzinfo=timezone.utc), "value": 1},
        {"_id": 2, "partition": "A", "date": datetime(2023, 6, 1, tzinfo=timezone.utc), "value": 2},
        {"_id": 3, "partition": "A", "date": datetime(2024, 6, 1, tzinfo=timezone.utc), "value": 4},
        {"_id": 4, "partition": "A", "date": datetime(2026, 6, 1, tzinfo=timezone.utc), "value": 8},
    ]
    result = run_window_operator(
        collection, "$sum", docs, {"range": [-1, 1], "unit": "year"}, sort_by={"date": 1}
    )
    # Jun 2022: range [Jun 2021, Jun 2023] -> includes 2022, 2023 -> 1+2 = 3
    # Jun 2023: range [Jun 2022, Jun 2024] -> includes 2022, 2023, 2024 -> 1+2+4 = 7
    # Jun 2024: range [Jun 2023, Jun 2025] -> includes 2023, 2024 -> 2+4 = 6
    # Jun 2026: range [Jun 2025, Jun 2027] -> includes 2026 only -> 8
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "date": datetime(2022, 6, 1, tzinfo=timezone.utc),
            "value": 1,
            "result": 3,
        },
        {
            "_id": 2,
            "partition": "A",
            "date": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "value": 2,
            "result": 7,
        },
        {
            "_id": 3,
            "partition": "A",
            "date": datetime(2024, 6, 1, tzinfo=timezone.utc),
            "value": 4,
            "result": 6,
        },
        {
            "_id": 4,
            "partition": "A",
            "date": datetime(2026, 6, 1, tzinfo=timezone.utc),
            "value": 8,
            "result": 8,
        },
    ]
    assertSuccess(result, expected, msg="time-range year unit [-1, 1] selects correct documents")
