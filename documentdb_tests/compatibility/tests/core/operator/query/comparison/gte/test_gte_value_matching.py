"""
Tests for $gte value matching — arrays, objects, dates, timestamps, and strings.

Covers array comparison semantics (first-element-wins, nested traversal),
object/subdocument comparison (field values, empty, NaN sort order),
date ordering across epoch boundary, timestamp ordering,
Date vs Timestamp type distinction, and string lexicographic/case comparison.
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
        filter={"a": {"$gte": [1, 2, 3]}},
        doc=[{"_id": 1, "a": [3, 2, 1]}, {"_id": 2, "a": [1, 2, 3]}],
        expected=[{"_id": 1, "a": [3, 2, 1]}, {"_id": 2, "a": [1, 2, 3]}],
        msg="$gte includes equal array and array with greater first element",
    ),
    QueryTestCase(
        id="nested_array_not_traversed",
        filter={"a": {"$gte": 5}},
        doc=[{"_id": 1, "a": [[6, 7], [8, 9]]}],
        expected=[],
        msg="$gte scalar does not traverse nested arrays",
    ),
]

OBJECT_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="subdocument_field_value_gte",
        filter={"a": {"$gte": SON([("x", 2), ("y", 1)])}},
        doc=[
            {"_id": 1, "a": SON([("x", 3), ("y", 1)])},
            {"_id": 2, "a": SON([("x", 2), ("y", 1)])},
            {"_id": 3, "a": SON([("x", 1), ("y", 1)])},
        ],
        expected=[{"_id": 1, "a": {"x": 3, "y": 1}}, {"_id": 2, "a": {"x": 2, "y": 1}}],
        msg="$gte subdocument includes equal and greater",
    ),
    QueryTestCase(
        id="nonempty_doc_gte_empty",
        filter={"a": {"$gte": {}}},
        doc=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}],
        expected=[{"_id": 1, "a": {}}, {"_id": 2, "a": {"x": 1}}],
        msg="$gte empty document matches empty and non-empty",
    ),
    QueryTestCase(
        id="subdocument_numeric_gte_nan_subdocument",
        filter={"a": {"$gte": SON([("x", float("nan"))])}},
        doc=[
            {"_id": 1, "a": SON([("x", 5)])},
        ],
        expected=[{"_id": 1, "a": {"x": 5}}],
        msg="$gte NaN subdocument matches greater numeric (NaN sorts lowest)",
    ),
]

DATE_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="epoch_gte_pre_epoch",
        filter={"a": {"$gte": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        expected=[{"_id": 1, "a": DATE_BEFORE_EPOCH}, {"_id": 2, "a": DATE_EPOCH}],
        msg="$gte pre-epoch returns both equal and later dates",
    ),
    QueryTestCase(
        id="date_equal_matches_gte",
        filter={"a": {"$gte": DATE_BEFORE_EPOCH}},
        doc=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        expected=[{"_id": 1, "a": DATE_BEFORE_EPOCH}],
        msg="equal date matches $gte",
    ),
    QueryTestCase(
        id="ts_seconds_then_increment",
        filter={"a": {"$gte": Timestamp(100, 1)}},
        doc=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 2, "a": Timestamp(100, 2)},
            {"_id": 3, "a": Timestamp(99, 999)},
        ],
        expected=[
            {"_id": 1, "a": Timestamp(100, 1)},
            {"_id": 2, "a": Timestamp(100, 2)},
        ],
        msg="Timestamp orders by seconds first, then increment",
    ),
    QueryTestCase(
        id="date_not_gte_timestamp",
        filter={"a": {"$gte": Timestamp(0, 1)}},
        doc=[{"_id": 1, "a": DATE_EPOCH}],
        expected=[],
        msg="Date field does not match $gte with Timestamp query (different BSON types)",
    ),
    QueryTestCase(
        id="timestamp_not_gte_date",
        filter={"a": {"$gte": DATE_EPOCH}},
        doc=[{"_id": 1, "a": TS_EPOCH}],
        expected=[],
        msg="Timestamp field does not match $gte with Date query (different BSON types)",
    ),
]

STRING_COMPARISON_TESTS: list[QueryTestCase] = [
    QueryTestCase(
        id="prefix_shorter_not_gte_longer",
        filter={"a": {"$gte": "abcdef"}},
        doc=[{"_id": 1, "a": "abc"}],
        expected=[],
        msg="prefix 'abc' is not >= longer string 'abcdef'",
    ),
    QueryTestCase(
        id="prefix_longer_gte_shorter",
        filter={"a": {"$gte": "abc"}},
        doc=[{"_id": 1, "a": "abcdef"}],
        expected=[{"_id": 1, "a": "abcdef"}],
        msg="longer string 'abcdef' is >= prefix 'abc'",
    ),
    QueryTestCase(
        id="empty_string_gte_empty_string",
        filter={"a": {"$gte": ""}},
        doc=[{"_id": 1, "a": ""}, {"_id": 2, "a": "a"}],
        expected=[{"_id": 1, "a": ""}, {"_id": 2, "a": "a"}],
        msg="empty string and non-empty both match $gte empty string",
    ),
    QueryTestCase(
        id="nonempty_not_gte_when_less",
        filter={"a": {"$gte": "b"}},
        doc=[{"_id": 1, "a": ""}],
        expected=[],
        msg="empty string does not match $gte 'b'",
    ),
    QueryTestCase(
        id="case_sensitivity_upper_less_than_lower",
        filter={"a": {"$gte": "a"}},
        doc=[{"_id": 1, "a": "A"}, {"_id": 2, "a": "a"}, {"_id": 3, "a": "b"}],
        expected=[{"_id": 2, "a": "a"}, {"_id": 3, "a": "b"}],
        msg="binary comparison: 'A' (0x41) < 'a' (0x61), so 'A' not >= 'a'",
    ),
    QueryTestCase(
        id="case_sensitivity_lower_gte_upper",
        filter={"a": {"$gte": "A"}},
        doc=[{"_id": 1, "a": "A"}, {"_id": 2, "a": "a"}, {"_id": 3, "a": "Z"}],
        expected=[{"_id": 1, "a": "A"}, {"_id": 2, "a": "a"}, {"_id": 3, "a": "Z"}],
        msg="binary comparison: 'a' and 'Z' are both >= 'A'",
    ),
]

ALL_TESTS = (
    ARRAY_COMPARISON_TESTS
    + OBJECT_COMPARISON_TESTS
    + DATE_COMPARISON_TESTS
    + STRING_COMPARISON_TESTS
)


@pytest.mark.parametrize("test", pytest_params(ALL_TESTS))
def test_gte_value_matching(collection, test):
    """Parametrized test for $gte value matching."""
    collection.insert_many(test.doc)
    cmd = {"find": collection.name, "filter": test.filter}
    result = execute_command(collection, cmd)
    assertSuccess(result, test.expected, ignore_doc_order=True)
