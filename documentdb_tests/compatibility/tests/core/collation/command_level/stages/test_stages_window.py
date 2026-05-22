"""Tests for collation effects on setWindowFields, fill, and densify stages."""

from __future__ import annotations

import pytest

from documentdb_tests.compatibility.tests.core.collections.commands.utils.command_test_case import (
    CommandContext,
    CommandTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [SetWindowFields Partitioning and Sorting]: collation affects
# $setWindowFields partitionBy grouping so that collation-equal strings are
# placed in the same partition, and affects sortBy ordering within partitions.
COLLATION_SET_WINDOW_FIELDS_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "swf_partition_strength1_case_variants_same_partition",
        docs=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": 20},
            {"_id": 3, "category": "APPLE", "val": 30},
            {"_id": 4, "category": "banana", "val": 40},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$category",
                        "sortBy": {"_id": 1},
                        "output": {"rank": {"$rank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "category": "apple", "val": 10, "rank": 1},
            {"_id": 2, "category": "Apple", "val": 20, "rank": 2},
            {"_id": 3, "category": "APPLE", "val": 30, "rank": 3},
            {"_id": 4, "category": "banana", "val": 40, "rank": 1},
        ],
        msg="$setWindowFields with strength 1 should place case variants in the same partition",
    ),
    CommandTestCase(
        "swf_partition_no_collation_case_variants_separate",
        docs=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": 20},
            {"_id": 3, "category": "APPLE", "val": 30},
            {"_id": 4, "category": "banana", "val": 40},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$category",
                        "sortBy": {"_id": 1},
                        "output": {"rank": {"$rank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        # Binary comparison: each case variant is its own partition.
        expected=[
            {"_id": 1, "category": "apple", "val": 10, "rank": 1},
            {"_id": 2, "category": "Apple", "val": 20, "rank": 1},
            {"_id": 3, "category": "APPLE", "val": 30, "rank": 1},
            {"_id": 4, "category": "banana", "val": 40, "rank": 1},
        ],
        msg=(
            "$setWindowFields without collation should treat case variants"
            " as separate partitions"
        ),
    ),
    CommandTestCase(
        "swf_sortby_collation_aware_ordering",
        docs=[
            {"_id": 1, "group": "x", "name": "banana"},
            {"_id": 2, "group": "x", "name": "apple"},
            {"_id": 3, "group": "x", "name": "Cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$group",
                        "sortBy": {"name": 1},
                        "output": {"rank": {"$rank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Collation-aware: apple < banana < Cherry.
        expected=[
            {"_id": 1, "group": "x", "name": "banana", "rank": 2},
            {"_id": 2, "group": "x", "name": "apple", "rank": 1},
            {"_id": 3, "group": "x", "name": "Cherry", "rank": 3},
        ],
        msg="$setWindowFields sortBy should use collation-aware ordering within partitions",
    ),
    CommandTestCase(
        "swf_sortby_no_collation_binary_ordering",
        docs=[
            {"_id": 1, "group": "x", "name": "banana"},
            {"_id": 2, "group": "x", "name": "apple"},
            {"_id": 3, "group": "x", "name": "Cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$group",
                        "sortBy": {"name": 1},
                        "output": {"rank": {"$rank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        # Binary comparison: 'C' (67) < 'a' (97) < 'b' (98).
        expected=[
            {"_id": 1, "group": "x", "name": "banana", "rank": 3},
            {"_id": 2, "group": "x", "name": "apple", "rank": 2},
            {"_id": 3, "group": "x", "name": "Cherry", "rank": 1},
        ],
        msg="$setWindowFields sortBy without collation should use binary ordering",
    ),
]

# Property [DenseRank Ordering]: $denseRank respects collation for sort
# ordering and tie detection, producing consecutive ranks without gaps when
# collation-equal values create ties.
COLLATION_DENSE_RANK_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "swf_denserank_collation_ties_no_gaps",
        docs=[
            {"_id": 1, "group": "x", "name": "apple"},
            {"_id": 2, "group": "x", "name": "Apple"},
            {"_id": 3, "group": "x", "name": "banana"},
            {"_id": 4, "group": "x", "name": "Cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$group",
                        "sortBy": {"name": 1},
                        "output": {"dr": {"$denseRank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Collation strength 1: apple == Apple (tie at rank 1), banana=2, Cherry=3.
        # $denseRank produces consecutive ranks without gaps.
        expected=[
            {"_id": 1, "group": "x", "name": "apple", "dr": 1},
            {"_id": 2, "group": "x", "name": "Apple", "dr": 1},
            {"_id": 3, "group": "x", "name": "banana", "dr": 2},
            {"_id": 4, "group": "x", "name": "Cherry", "dr": 3},
        ],
        msg="$denseRank with collation should produce consecutive ranks for collation-equal ties",
    ),
    CommandTestCase(
        "swf_denserank_no_collation_binary_ordering",
        docs=[
            {"_id": 1, "group": "x", "name": "apple"},
            {"_id": 2, "group": "x", "name": "Apple"},
            {"_id": 3, "group": "x", "name": "banana"},
            {"_id": 4, "group": "x", "name": "Cherry"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$group",
                        "sortBy": {"name": 1},
                        "output": {"dr": {"$denseRank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        # Binary: Apple(1) < Cherry(2) < apple(3) < banana(4), no ties.
        expected=[
            {"_id": 1, "group": "x", "name": "apple", "dr": 3},
            {"_id": 2, "group": "x", "name": "Apple", "dr": 1},
            {"_id": 3, "group": "x", "name": "banana", "dr": 4},
            {"_id": 4, "group": "x", "name": "Cherry", "dr": 2},
        ],
        msg="$denseRank without collation should use binary ordering with no ties",
    ),
    CommandTestCase(
        "swf_denserank_partition_collation_groups_variants",
        docs=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": 20},
            {"_id": 3, "category": "APPLE", "val": 30},
            {"_id": 4, "category": "banana", "val": 40},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$category",
                        "sortBy": {"_id": 1},
                        "output": {"dr": {"$denseRank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Strength 1 merges case variants into one partition; _id ordering
        # produces no ties so denseRank is sequential.
        expected=[
            {"_id": 1, "category": "apple", "val": 10, "dr": 1},
            {"_id": 2, "category": "Apple", "val": 20, "dr": 2},
            {"_id": 3, "category": "APPLE", "val": 30, "dr": 3},
            {"_id": 4, "category": "banana", "val": 40, "dr": 1},
        ],
        msg="$denseRank with collation should place case variants in the same partition",
    ),
    CommandTestCase(
        "swf_denserank_partition_no_collation_separate",
        docs=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": 20},
            {"_id": 3, "category": "APPLE", "val": 30},
            {"_id": 4, "category": "banana", "val": 40},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$category",
                        "sortBy": {"_id": 1},
                        "output": {"dr": {"$denseRank": {}}},
                    }
                },
                {"$sort": {"_id": 1}},
            ],
            "cursor": {},
        },
        # Binary: each case variant is its own single-doc partition.
        expected=[
            {"_id": 1, "category": "apple", "val": 10, "dr": 1},
            {"_id": 2, "category": "Apple", "val": 20, "dr": 1},
            {"_id": 3, "category": "APPLE", "val": 30, "dr": 1},
            {"_id": 4, "category": "banana", "val": 40, "dr": 1},
        ],
        msg="$denseRank without collation should treat case variants as separate partitions",
    ),
]

# Property [Fill and Densify Partitioning]: $fill and $densify
# partitionByFields respect collation so that collation-equal strings are
# merged into one partition.
COLLATION_FILL_DENSIFY_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "fill_partition_strength1_case_variants_merged",
        docs=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": None},
            {"_id": 3, "category": "APPLE", "val": 30},
            {"_id": 4, "category": "banana", "val": None},
            {"_id": 5, "category": "banana", "val": 50},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$fill": {
                        "partitionByFields": ["category"],
                        "output": {"val": {"method": "locf"}},
                    }
                },
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Strength 1 merges all case variants into one partition, so LOCF
        # carries _id:1 val=10 forward to _id:2.
        expected=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": 10},
            {"_id": 3, "category": "APPLE", "val": 30},
            {"_id": 4, "category": "banana", "val": None},
            {"_id": 5, "category": "banana", "val": 50},
        ],
        msg="$fill with strength 1 should merge case variants into one partition for LOCF",
    ),
    CommandTestCase(
        "fill_partition_no_collation_case_variants_separate",
        docs=[
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 2, "category": "Apple", "val": None},
            {"_id": 3, "category": "banana", "val": None},
            {"_id": 4, "category": "banana", "val": 50},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {"$sort": {"_id": 1}},
                {
                    "$fill": {
                        "partitionByFields": ["category"],
                        "output": {"val": {"method": "locf"}},
                    }
                },
            ],
            "cursor": {},
        },
        # Binary comparison: "Apple" and "apple" are separate partitions, so
        # _id:2 has no prior value in its partition and remains None.
        expected=[
            {"_id": 2, "category": "Apple", "val": None},
            {"_id": 1, "category": "apple", "val": 10},
            {"_id": 3, "category": "banana", "val": None},
            {"_id": 4, "category": "banana", "val": 50},
        ],
        msg="$fill without collation should treat case variants as separate partitions",
    ),
    CommandTestCase(
        "densify_partition_strength1_case_variants_merged",
        docs=[
            {"_id": 1, "category": "apple", "val": 0},
            {"_id": 2, "category": "Apple", "val": 10},
            {"_id": 3, "category": "banana", "val": 0},
            {"_id": 4, "category": "banana", "val": 10},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$densify": {
                        "field": "val",
                        "partitionByFields": ["category"],
                        "range": {"step": 5, "bounds": "partition"},
                    }
                }
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        # Strength 1 merges apple and Apple into one partition (val 0, 10),
        # so densify fills at val=5 within the merged partition.
        expected=[
            {"_id": 1, "category": "apple", "val": 0},
            {"category": "Apple", "val": 5},
            {"_id": 2, "category": "Apple", "val": 10},
            {"_id": 3, "category": "banana", "val": 0},
            {"category": "banana", "val": 5},
            {"_id": 4, "category": "banana", "val": 10},
        ],
        msg="$densify with strength 1 should merge case variants into one partition",
    ),
    CommandTestCase(
        "densify_partition_no_collation_case_variants_separate",
        docs=[
            {"_id": 1, "category": "apple", "val": 0},
            {"_id": 2, "category": "Apple", "val": 10},
            {"_id": 3, "category": "banana", "val": 0},
            {"_id": 4, "category": "banana", "val": 10},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$densify": {
                        "field": "val",
                        "partitionByFields": ["category"],
                        "range": {"step": 5, "bounds": "partition"},
                    }
                }
            ],
            "cursor": {},
        },
        # Binary comparison: "Apple" and "apple" are separate single-value
        # partitions so no densification occurs for them. Only banana (0, 10)
        # gets a fill at val=5.
        expected=[
            {"_id": 2, "category": "Apple", "val": 10},
            {"_id": 1, "category": "apple", "val": 0},
            {"_id": 3, "category": "banana", "val": 0},
            {"category": "banana", "val": 5},
            {"_id": 4, "category": "banana", "val": 10},
        ],
        msg="$densify without collation should treat case variants as separate partitions",
    ),
]

# Property [SetWindowFields Window Function Collation]: $min, $max, $first,
# $last, and $documentNumber window functions are affected by collation through
# the sortBy ordering.
COLLATION_WINDOW_FUNCTION_TESTS: list[CommandTestCase] = [
    CommandTestCase(
        "window_min_case_insensitive",
        docs=[
            {"_id": 1, "cat": "fruit", "x": "a"},
            {"_id": 2, "cat": "fruit", "x": "B"},
            {"_id": 3, "cat": "fruit", "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$cat",
                        "sortBy": {"_id": 1},
                        "output": {
                            "wmin": {"$min": "$x"},
                            "wmax": {"$max": "$x"},
                        },
                    }
                },
                {"$project": {"x": 1, "wmin": 1, "wmax": 1}},
                {"$limit": 1},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "x": "a", "wmin": "a", "wmax": "c"}],
        msg="$min/$max window functions should use collation for string comparison",
    ),
    CommandTestCase(
        "window_min_no_collation_binary",
        docs=[
            {"_id": 1, "cat": "fruit", "x": "a"},
            {"_id": 2, "cat": "fruit", "x": "B"},
            {"_id": 3, "cat": "fruit", "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$cat",
                        "sortBy": {"_id": 1},
                        "output": {
                            "wmin": {"$min": "$x"},
                            "wmax": {"$max": "$x"},
                        },
                    }
                },
                {"$project": {"x": 1, "wmin": 1, "wmax": 1}},
                {"$limit": 1},
            ],
            "cursor": {},
        },
        expected=[{"_id": 1, "x": "a", "wmin": "B", "wmax": "c"}],
        msg="$min/$max window functions without collation should use binary comparison",
    ),
    CommandTestCase(
        "window_first_last_case_insensitive",
        docs=[
            {"_id": 1, "cat": "fruit", "x": "a"},
            {"_id": 2, "cat": "fruit", "x": "B"},
            {"_id": 3, "cat": "fruit", "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$cat",
                        "sortBy": {"x": 1},
                        "output": {
                            "wfirst": {"$first": "$x"},
                            "wlast": {"$last": "$x"},
                        },
                    }
                },
                {"$project": {"x": 1, "wfirst": 1, "wlast": 1}},
                {"$limit": 1},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[{"_id": 1, "x": "a", "wfirst": "a", "wlast": "c"}],
        msg="$first/$last window functions should reflect collation-aware sortBy ordering",
    ),
    CommandTestCase(
        "window_first_last_no_collation_binary",
        docs=[
            {"_id": 1, "cat": "fruit", "x": "a"},
            {"_id": 2, "cat": "fruit", "x": "B"},
            {"_id": 3, "cat": "fruit", "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$cat",
                        "sortBy": {"x": 1},
                        "output": {
                            "wfirst": {"$first": "$x"},
                            "wlast": {"$last": "$x"},
                        },
                    }
                },
                {"$project": {"x": 1, "wfirst": 1, "wlast": 1}},
                {"$limit": 1},
            ],
            "cursor": {},
        },
        expected=[{"_id": 2, "x": "B", "wfirst": "B", "wlast": "c"}],
        msg="$first/$last window functions without collation should use binary sortBy ordering",
    ),
    CommandTestCase(
        "window_documentnumber_case_insensitive",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "B"},
            {"_id": 3, "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"x": 1},
                        "output": {"docNum": {"$documentNumber": {}}},
                    }
                },
                {"$sort": {"docNum": 1}},
                {"$project": {"x": 1, "docNum": 1}},
            ],
            "cursor": {},
            "collation": {"locale": "en", "strength": 1},
        },
        expected=[
            {"_id": 1, "x": "a", "docNum": 1},
            {"_id": 2, "x": "B", "docNum": 2},
            {"_id": 3, "x": "c", "docNum": 3},
        ],
        msg="$documentNumber should reflect collation-aware sortBy ordering",
    ),
    CommandTestCase(
        "window_documentnumber_no_collation_binary",
        docs=[
            {"_id": 1, "x": "a"},
            {"_id": 2, "x": "B"},
            {"_id": 3, "x": "c"},
        ],
        command=lambda ctx: {
            "aggregate": ctx.collection,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "sortBy": {"x": 1},
                        "output": {"docNum": {"$documentNumber": {}}},
                    }
                },
                {"$sort": {"docNum": 1}},
                {"$project": {"x": 1, "docNum": 1}},
            ],
            "cursor": {},
        },
        expected=[
            {"_id": 2, "x": "B", "docNum": 1},
            {"_id": 1, "x": "a", "docNum": 2},
            {"_id": 3, "x": "c", "docNum": 3},
        ],
        msg="$documentNumber without collation should use binary sortBy ordering",
    ),
]

COLLATION_AGGREGATE_WINDOW_TESTS: list[CommandTestCase] = (
    COLLATION_SET_WINDOW_FIELDS_TESTS
    + COLLATION_DENSE_RANK_TESTS
    + COLLATION_FILL_DENSIFY_TESTS
    + COLLATION_WINDOW_FUNCTION_TESTS
)


@pytest.mark.parametrize("test", pytest_params(COLLATION_AGGREGATE_WINDOW_TESTS))
def test_collation_aggregate_window(database_client, collection, test):
    """Test collation effects on $setWindowFields stage."""
    collection = test.prepare(database_client, collection)
    ctx = CommandContext.from_collection(collection)
    result = execute_command(collection, test.build_command(ctx))
    assertResult(
        result,
        expected=test.build_expected(ctx),
        error_code=test.error_code,
        msg=test.msg,
    )
