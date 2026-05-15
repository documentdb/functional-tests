"""
Tests for $avg accumulator in $group context.

Covers numeric equivalence in grouping, single/empty groups,
precision edge cases, multiple groups, and comparison with $sum.
"""

from __future__ import annotations

import pytest
from bson import Decimal128, Int64

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Numeric Equivalence]: numerically equivalent group keys
# (int32, int64, double, Decimal128) produce a single group.

NUMERIC_EQUIVALENCE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="numeric_equivalence_grouping",
        docs=[
            {"_id": 1, "key": 1, "value": 10},
            {"_id": 2, "key": Int64(1), "value": 20},
            {"_id": 3, "key": 1.0, "value": 30},
            {"_id": 4, "key": Decimal128("1"), "value": 40},
        ],
        pipeline=[
            {"$group": {"_id": "$key", "avg": {"$avg": "$value"}}},
        ],
        expected=[{"_id": 1, "avg": 25.0}],
        msg="Numerically equivalent group keys should produce a single group",
    ),
    AccumulatorTestCase(
        id="zero_equivalence",
        docs=[
            {"_id": 1, "key": 0, "value": 10},
            {"_id": 2, "key": Int64(0), "value": 20},
            {"_id": 3, "key": 0.0, "value": 30},
            {"_id": 4, "key": Decimal128("0"), "value": 40},
        ],
        pipeline=[
            {"$group": {"_id": "$key", "avg": {"$avg": "$value"}}},
        ],
        expected=[{"_id": 0, "avg": 25.0}],
        msg="All zero representations should group together",
    ),
]

# Property [Single and Empty Groups]: $avg returns correct results for
# single-document groups, empty collections, and null group IDs.

SINGLE_EMPTY_GROUP_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="single_document",
        docs=[{"_id": 1, "category": "A", "value": 42}],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": 42.0}],
        msg="$avg of single document should return that value as double",
    ),
    AccumulatorTestCase(
        id="single_document_non_numeric",
        docs=[{"_id": 1, "category": "A", "value": "hello"}],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": None}],
        msg="$avg of single non-numeric document should return null",
    ),
    AccumulatorTestCase(
        id="single_document_null",
        docs=[{"_id": 1, "category": "A", "value": None}],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": None}],
        msg="$avg of single null document should return null",
    ),
    AccumulatorTestCase(
        id="single_document_missing_field",
        docs=[{"_id": 1, "category": "A"}],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": None}],
        msg="$avg of single document with missing field should return null",
    ),
    AccumulatorTestCase(
        id="empty_collection",
        docs=None,
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
        ],
        expected=[],
        msg="$avg on empty collection should produce no output",
    ),
    AccumulatorTestCase(
        id="all_filtered_out",
        docs=[
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
        ],
        pipeline=[
            {"$match": {"category": "Z"}},
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
        ],
        expected=[],
        msg="$avg after filtering all documents should produce no output",
    ),
    AccumulatorTestCase(
        id="null_id",
        docs=[
            {"_id": 1, "value": 10},
            {"_id": 2, "value": 20},
            {"_id": 3, "value": 30},
        ],
        pipeline=[
            {"$group": {"_id": None, "avg": {"$avg": "$value"}}},
        ],
        expected=[{"_id": None, "avg": 20.0}],
        msg="$avg with _id: null should average entire collection",
    ),
]

# Property [Precision]: $avg produces correct fractional and repeating
# decimal results and handles large document counts.

PRECISION_EDGE_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="odd_sum_two_int32",
        docs=[
            {"_id": 1, "category": "A", "value": 1},
            {"_id": 2, "category": "A", "value": 2},
        ],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": 1.5}],
        msg="$avg of 1 and 2 should return 1.5",
    ),
    AccumulatorTestCase(
        id="repeating_decimal",
        docs=[
            {"_id": 1, "category": "A", "value": 1},
            {"_id": 2, "category": "A", "value": 1},
            {"_id": 3, "category": "A", "value": 2},
        ],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
        ],
        expected=[{"_id": "A", "avg": 1.3333333333333333}],
        msg="$avg of 1,1,2 should return 4/3",
    ),
    AccumulatorTestCase(
        id="sequence_1_to_100",
        docs=[{"_id": i, "category": "A", "value": i} for i in range(1, 101)],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": 50.5}],
        msg="$avg of 1..100 should return 50.5",
    ),
    AccumulatorTestCase(
        id="large_count_identical",
        docs=[{"_id": i, "category": "A", "value": 7} for i in range(1000)],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[{"_id": "A", "avg": 7.0}],
        msg="$avg of 1000 identical values should return that value",
    ),
]

# Property [Multiple Groups]: $avg computes independent averages per group
# with different counts, null groups, and mixed types.

MULTIPLE_GROUPS_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="different_counts",
        docs=[
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "B", "value": 20},
            {"_id": 3, "category": "B", "value": 40},
            {"_id": 4, "category": "C", "value": 5},
            {"_id": 5, "category": "C", "value": 10},
            {"_id": 6, "category": "C", "value": 15},
        ],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "avg": 10.0},
            {"_id": "B", "avg": 30.0},
            {"_id": "C", "avg": 10.0},
        ],
        msg="$avg should compute correct average per group with different counts",
    ),
    AccumulatorTestCase(
        id="one_all_nulls_one_all_numeric",
        docs=[
            {"_id": 1, "category": "A", "value": None},
            {"_id": 2, "category": "A", "value": None},
            {"_id": 3, "category": "B", "value": 10},
            {"_id": 4, "category": "B", "value": 20},
        ],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "A", "avg": None},
            {"_id": "B", "avg": 15.0},
        ],
        msg="Group with all nulls returns null, group with numerics returns average",
    ),
    AccumulatorTestCase(
        id="mixed_types_per_group",
        docs=[
            {"_id": 1, "category": "int", "value": 10},
            {"_id": 2, "category": "int", "value": 20},
            {"_id": 3, "category": "dec", "value": Decimal128("10")},
            {"_id": 4, "category": "dec", "value": Decimal128("20")},
        ],
        pipeline=[
            {"$group": {"_id": "$category", "avg": {"$avg": "$value"}}},
            {"$sort": {"_id": 1}},
        ],
        expected=[
            {"_id": "dec", "avg": Decimal128("15")},
            {"_id": "int", "avg": 15.0},
        ],
        msg="Int group returns double, Decimal128 group returns Decimal128",
    ),
]

# Property [Comparison with Related Operators]: $avg results are consistent
# with $sum/$count, and non-numeric handling differs from $sum.

COMPARISON_WITH_RELATED_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        id="equals_sum_divided_by_count",
        docs=[
            {"_id": 1, "category": "A", "value": 10},
            {"_id": 2, "category": "A", "value": 20},
            {"_id": 3, "category": "A", "value": 30},
            {"_id": 4, "category": "A", "value": 40},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$category",
                    "avg": {"$avg": "$value"},
                    "sum": {"$sum": "$value"},
                    "count": {"$sum": 1},
                }
            },
        ],
        expected=[{"_id": "A", "avg": 25.0, "sum": 100, "count": 4}],
        msg="$avg should equal $sum / count",
    ),
    AccumulatorTestCase(
        id="vs_sum_non_numeric_handling",
        docs=[
            {"_id": 1, "category": "A", "value": "hello"},
            {"_id": 2, "category": "A", "value": "world"},
        ],
        pipeline=[
            {
                "$group": {
                    "_id": "$category",
                    "avg": {"$avg": "$value"},
                    "sum": {"$sum": "$value"},
                }
            },
        ],
        expected=[{"_id": "A", "avg": None, "sum": 0}],
        msg="$avg returns null for non-numeric but $sum returns 0",
    ),
]

AVG_GROUP_CONTEXT_TESTS: list[AccumulatorTestCase] = (
    NUMERIC_EQUIVALENCE_TESTS
    + SINGLE_EMPTY_GROUP_TESTS
    + PRECISION_EDGE_TESTS
    + MULTIPLE_GROUPS_TESTS
    + COMPARISON_WITH_RELATED_TESTS
)


@pytest.mark.parametrize("test_case", pytest_params(AVG_GROUP_CONTEXT_TESTS))
def test_avg_group_context(collection, test_case: AccumulatorTestCase):
    """Test $avg in $group context with grouping behavior."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": test_case.pipeline,
            "cursor": {},
        },
    )
    assertResult(result, expected=test_case.expected, msg=test_case.msg)
