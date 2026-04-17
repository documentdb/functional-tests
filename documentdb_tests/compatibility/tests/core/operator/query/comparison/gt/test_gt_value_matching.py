"""
Tests for $gt value matching — arrays, objects, dates, and timestamps.

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
        filter={"a": {"$gt": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [3, 2, 1]}],
        expected=[{"_id": 1, "a": [3, 2, 1]}],
        msg="$gt [3,2,1] > [1,2,3] because first element 3 > 1",
    ),
    QueryTestCase(
        id="nested_array_not_traversed",
        filter={"a": {"$gt": 5}},
        doc=[{"_id": 1, "a": [[6, 7], [8, 9]]}],
        expected=[],
        msg="$gt scalar does not traverse nested arrays",
    ),
]

OBJECT_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="subdocument_field_value_gt",
        filter={"a": {"$gt": SON([("x", 2), ("y", 1)])}},
        doc=[
            {"_id": 1, "a": SON([("x", 3), ("y", 1)])},
            {"_id": 2, "a": SON([("x", 1), ("y", 1)])},
        ],
        expected=[{"_id": 1, "a": {"x": 3, "y": 1}}],
        msg="$gt subdocument compares field values in order",
    ),
    QueryTestCase(
        id="nonempty_doc_gt_empty",
        filter={"a": {"$gt": {}}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}],
        expected=[{"_id": 2, "a": {"x": 1}}],
        msg="$gt non-empty document is greater than empty document",
    ),
    QueryTestCase(
        id="subdocument_numeric_gt_nan_subdocument",
        filter={"a": {"$gt": SON([("x", float("nan"))])}},
        doc=[
            {"_id": 1, "a": SON([("x", 5)])},
            {"_id": 2, "a": SON([("x", float("nan"))])},
        ],
        expected=[{"_id": 1, "a": {"x": 5}}],
        msg="$gt subdocument with numeric > subdocument with NaN (NaN sorts lowest)",
    ),
    QueryTestCase(
        id="longer_subdoc_gt_shorter_prefix",
        filter={"a": {"$gt": SON([("x", 1)])}},
        doc=[
            {"_id": 1, "a": SON([("x", 1)])},
            {"_id": 2, "a": SON([("x", 1), ("y", 2)])},
            {"_id": 3, "a": SON([("x", 1), ("y", 5)])},
        ],
        expected=[
            {"_id": 2, "a": {"x": 1, "y": 2}},
            {"_id": 3, "a": {"x": 1, "y": 5}},
        ],
        msg="subdocument with more fields is greater than shorter prefix; equal excluded",
    ),
]

DATE_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="epoch_gt_pre_epoch",
        filter={"a": {"$gt": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        expected=[{"_id": 2, "a": DATE_EPOCH}],
        msg="epoch is greater than pre-epoch date",
    ),
    QueryTestCase(
        id="date_equal_not_gt",
        filter={"a": {"$gt": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        expected=[],
        msg="equal date does not match $gt",
    ),
    QueryTestCase(
        id="ts_seconds_then_increment",
        filter={"a": {"$gt": Timestamp(100, 1)}},
        doc=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 2, "a": Timestamp(100, 2)},
            {"_id": 3, "a": Timestamp(99, 999)},
        ],
        expected=[{"_id": 2, "a": Timestamp(100, 2)}],
        msg="Timestamp orders by seconds first, then increment",
    ),
    QueryTestCase(
        id="date_not_gt_timestamp",
        filter={"a": {"$gt": Timestamp(0, 1)}},
        doc=[{"_id": 1, "a": DATE_EPOCH}],
        expected=[],
        msg="Date field does not match $gt with Timestamp query (different BSON types)",
    ),
    QueryTestCase(
        id="timestamp_not_gt_date",
        filter={"a": {"$gt": DATE_EPOCH}},
        doc=[{"_id": 1, "a": TS_EPOCH}],
        expected=[],
        msg="Timestamp field does not match $gt with Date query (different BSON types)",
    ),
]

ALL_TESTS = ARRAY_COMPARISON_TESTS + OBJECT_COMPARISON_TESTS + DATE_COMPARISON_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gt_value_matching(collection, test):
    """Parametrized test for $gt value matching."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
