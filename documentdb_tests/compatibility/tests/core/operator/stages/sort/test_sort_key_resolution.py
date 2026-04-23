from __future__ import annotations

import pytest
from bson import Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Compound Sort]: when sorting on multiple fields, documents are
# sorted by the first field, then ties are broken by subsequent fields in
# left-to-right order, with each field independently ascending or descending.
SORT_COMPOUND_TESTS: list[StageTestCase] = [
    StageTestCase(
        "compound_left_to_right",
        docs=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 4, "a": 1, "b": 40},
        ],
        pipeline=[{"$sort": {"a": 1, "b": 1}}],
        expected=[
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 4, "a": 1, "b": 40},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 1, "a": 2, "b": 30},
        ],
        msg="$sort should sort by first field then by second field left to right",
    ),
    StageTestCase(
        "compound_non_alphabetical_order",
        docs=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 4, "a": 1, "b": 40},
        ],
        pipeline=[{"$sort": {"b": 1, "a": 1}}],
        expected=[
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 4, "a": 1, "b": 40},
        ],
        msg="$sort should use key insertion order, not alphabetical field name order",
    ),
    StageTestCase(
        "compound_asc_desc",
        docs=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 4, "a": 1, "b": 40},
        ],
        pipeline=[{"$sort": {"a": 1, "b": -1}}],
        expected=[
            {"_id": 4, "a": 1, "b": 40},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 3, "a": 2, "b": 10},
        ],
        msg="$sort should apply ascending on first field and descending on second field",
    ),
    StageTestCase(
        "compound_desc_asc",
        docs=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 4, "a": 1, "b": 40},
        ],
        pipeline=[{"$sort": {"a": -1, "b": 1}}],
        expected=[
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 4, "a": 1, "b": 40},
        ],
        msg="$sort should apply descending on first field and ascending on second field",
    ),
    StageTestCase(
        "compound_desc_desc",
        docs=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 2, "a": 1, "b": 20},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 4, "a": 1, "b": 40},
        ],
        pipeline=[{"$sort": {"a": -1, "b": -1}}],
        expected=[
            {"_id": 1, "a": 2, "b": 30},
            {"_id": 3, "a": 2, "b": 10},
            {"_id": 4, "a": 1, "b": 40},
            {"_id": 2, "a": 1, "b": 20},
        ],
        msg="$sort should apply descending on both first and second fields",
    ),
]

# Property [Null and Missing Field Behavior]: documents where the sort field
# is null, missing, or an array containing only null sort equivalently.
SORT_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        "null_missing_array_null_equivalent",
        docs=[
            {"_id": 5},
            {"_id": 3, "v": [None]},
            {"_id": 1, "v": None},
            {"_id": 6, "v": [None]},
            {"_id": 4, "v": None},
            {"_id": 2},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "v": None},
            {"_id": 2},
            {"_id": 3, "v": [None]},
            {"_id": 4, "v": None},
            {"_id": 5},
            {"_id": 6, "v": [None]},
        ],
        msg="$sort should sort null, missing, and [null] equivalently, interleaved by _id",
    ),
    StageTestCase(
        "null_missing_nonexistent_sort_field",
        docs=[
            {"_id": 2, "x": "b"},
            {"_id": 1, "x": "a"},
            {"_id": 3, "x": "c"},
        ],
        pipeline=[{"$sort": {"v": 1, "_id": 1}}],
        expected=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "b"},
            {"_id": 3, "x": "c"},
        ],
        msg="$sort on a field absent from all documents should treat all as missing",
    ),
]

SORT_KEY_RESOLUTION_TESTS = SORT_COMPOUND_TESTS + SORT_NULL_MISSING_TESTS


@pytest.mark.parametrize("test_case", pytest_params(SORT_KEY_RESOLUTION_TESTS))
def test_sort_key_resolution(collection, test_case: StageTestCase):
    """Test $sort compound keys, null, and missing fields."""
    populate_collection(collection, test_case)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=test_case.msg,
    )


def test_sort_key_resolution_timestamp_zero_replaced(collection):
    """Test $sort with Timestamp(0, 0) which is replaced by the server on insert."""
    collection.insert_many(
        [
            {"_id": 1, "v": Timestamp(0, 0)},
            {"_id": 3, "v": Timestamp(1, 1)},
            {"_id": 2, "v": Timestamp(100, 1)},
        ]
    )
    # Timestamp(0, 0) is replaced by the server with the current time, which
    # is larger than Timestamp(200, 1). Sort ascending and verify _id order.
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [{"$sort": {"v": 1}}, {"$project": {"_id": 1}}],
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=[{"_id": 3}, {"_id": 2}, {"_id": 1}],
        msg=(
            "$sort should correctly order Timestamp(0, 0) after server"
            " replacement with the current time"
        ),
    )
