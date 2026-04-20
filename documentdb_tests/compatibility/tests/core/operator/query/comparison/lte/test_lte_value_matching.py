"""
Tests for $lte value matching — arrays, objects, dates, and timestamps.

Covers array comparison semantics (first-element-wins, nested traversal),
object/subdocument comparison (field values, empty, NaN sort order),
date ordering across epoch boundary, timestamp ordering,
and Date vs Timestamp type distinction.
"""

import pytest
from bson import SON, Timestamp

from documentdb_tests.compatibility.tests.core.operator.query.utils.query_test_case import (
    QueryTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params
from documentdb_tests.framework.test_constants import (
    DATE_BEFORE_EPOCH,
    DATE_EPOCH,
    TS_EPOCH,
)

ARRAY_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="array_first_element_decides",
        filter={"a": {"$lte": [3, 2, 1]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [3, 2, 1]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}, {"_id": 2, "a": [3, 2, 1]}],
        msg="$lte includes equal array and array with lesser first element",
    ),
    QueryTestCase(
        id="nested_array_not_traversed",
        filter={"a": {"$lte": 5}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[],
        msg="$lte scalar does not traverse nested arrays",
    ),
]

OBJECT_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="subdocument_field_value_lte",
        filter={"a": {"$lte": SON([("x", 2), ("y", 1)])}},
        doc=[
            {"_id": 1, "a": SON([("x", 1), ("y", 1)])},
            {"_id": 2, "a": SON([("x", 2), ("y", 1)])},
            {"_id": 3, "a": SON([("x", 3), ("y", 1)])},
        ],
        expected=[{"_id": 1, "a": {"x": 1, "y": 1}}, {"_id": 2, "a": {"x": 2, "y": 1}}],
        msg="$lte subdocument includes equal and lesser",
    ),
    QueryTestCase(
        id="empty_doc_lte_nonempty",
        filter={"a": {"$lte": {"x": 1}}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}, {"_id": 3, "a": {"x": 2}}],
        expected=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}],
        msg="$lte empty document and equal document both match",
    ),
    QueryTestCase(
        id="subdocument_nothing_lte_nan_subdocument",
        filter={"a": {"$lte": SON([("x", float("nan"))])}},
        doc=[
            {"_id": 1, "a": SON([("x", 5)])},
        ],
        expected=[],
        msg="$lte nothing is less than or equal to subdocument with NaN (NaN sorts lowest)",
    ),
]

DATE_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="pre_epoch_lte_epoch",
        filter={"a": {"$lte": DATE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        expected=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        msg="$lte epoch returns both equal and earlier dates",
    ),
    QueryTestCase(
        id="date_equal_matches_lte",
        filter={"a": {"$lte": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        expected=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        msg="equal date matches $lte",
    ),
    QueryTestCase(
        id="ts_seconds_then_increment",
        filter={"a": {"$lte": Timestamp(100, 2)}},
        doc=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 2, "a": Timestamp(100, 2)},
            {"_id": 3, "a": Timestamp(99, 999)},
        ],
        expected=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 2, "a": Timestamp(100, 2)},
            {"_id": 3, "a": Timestamp(99, 999)},
        ],
        msg="Timestamp orders by seconds first, then increment",
    ),
    QueryTestCase(
        id="date_not_lte_timestamp",
        filter={"a": {"$lte": Timestamp(2000000000, 1)}},
        doc=[{"_id": 1, "a": DATE_EPOCH}],
        expected=[],
        msg="Date field does not match $lte with Timestamp query (different BSON types)",
    ),
    QueryTestCase(
        id="timestamp_not_lte_date",
        filter={"a": {"$lte": DATE_EPOCH}},
        doc=[{"_id": 1, "a": TS_EPOCH}],
        expected=[],
        msg="Timestamp field does not match $lte with Date query (different BSON types)",
    ),
]

ALL_TESTS = ARRAY_COMPARISON_TESTS + OBJECT_COMPARISON_TESTS + DATE_COMPARISON_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lte_value_matching(collection, test):
    """Parametrized test for $lte value matching."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
