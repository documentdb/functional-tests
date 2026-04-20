"""
Tests for $lt value matching — arrays, objects, dates, and timestamps.

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
        filter={"a": {"$lt": [3, 2, 1]}},
        doc=[{"_id": 1, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [1, 2, 3]}],
        msg="$lt [1,2,3] < [3,2,1] because first element 1 < 3",
    ),
    QueryTestCase(
        id="nested_array_not_traversed",
        filter={"a": {"$lt": 5}},
        doc=[{"_id": 1, "a": [[1, 2], [3, 4]]}],
        expected=[],
        msg="$lt scalar does not traverse nested arrays",
    ),
]

OBJECT_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="subdocument_field_value_lt",
        filter={"a": {"$lt": SON([("x", 2), ("y", 1)])}},
        doc=[
            {"_id": 1, "a": SON([("x", 1), ("y", 1)])},
            {"_id": 2, "a": SON([("x", 3), ("y", 1)])},
        ],
        expected=[{"_id": 1, "a": {"x": 1, "y": 1}}],
        msg="$lt subdocument compares field values in order",
    ),
    QueryTestCase(
        id="empty_doc_lt_nonempty",
        filter={"a": {"$lt": {"x": 1}}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 2}}],
        expected=[{"_id": 1, "a": {}}],
        msg="$lt empty document is less than non-empty document",
    ),
    QueryTestCase(
        id="subdocument_nothing_lt_nan_subdocument",
        filter={"a": {"$lt": SON([("x", float("nan"))])}},
        doc=[
            {"_id": 1, "a": SON([("x", 5)])},
            {"_id": 2, "a": SON([("x", float("nan"))])},
        ],
        expected=[],
        msg="$lt nothing is less than subdocument containing NaN (NaN sorts lowest)",
    ),
]

DATE_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="pre_epoch_lt_epoch",
        filter={"a": {"$lt": DATE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        expected=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        msg="pre-epoch date is less than epoch",
    ),
    QueryTestCase(
        id="date_equal_not_lt",
        filter={"a": {"$lt": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        expected=[],
        msg="equal date does not match $lt",
    ),
    QueryTestCase(
        id="ts_seconds_then_increment",
        filter={"a": {"$lt": Timestamp(100, 2)}},
        doc=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 2, "a": Timestamp(100, 2)},
            {"_id": 3, "a": Timestamp(99, 999)},
        ],
        expected=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 3, "a": Timestamp(99, 999)},
        ],
        msg="Timestamp orders by seconds first, then increment",
    ),
    QueryTestCase(
        id="date_not_lt_timestamp",
        filter={"a": {"$lt": Timestamp(2000000000, 1)}},
        doc=[{"_id": 1, "a": DATE_EPOCH}],
        expected=[],
        msg="Date field does not match $lt with Timestamp query (different BSON types)",
    ),
    QueryTestCase(
        id="timestamp_not_lt_date",
        filter={"a": {"$lt": DATE_EPOCH}},
        doc=[{"_id": 1, "a": TS_EPOCH}],
        expected=[],
        msg="Timestamp field does not match $lt with Date query (different BSON types)",
    ),
]

ALL_TESTS = ARRAY_COMPARISON_TESTS + OBJECT_COMPARISON_TESTS + DATE_COMPARISON_TESTS


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_lt_value_matching(collection, test):
    """Parametrized test for $lt value matching."""
    collection.insert_many(test.doc)
    result = execute_command(collection, {"find": collection.name, "filter": test.filter})
    assertSuccess(result, test.expected, ignore_doc_order=True)
