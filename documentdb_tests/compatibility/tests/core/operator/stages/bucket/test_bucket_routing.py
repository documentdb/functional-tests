"""Tests for $bucket aggregation stage — document routing behavior."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import (
    Binary,
    Code,
    MaxKey,
    MinKey,
    ObjectId,
    Regex,
    Timestamp,
)

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Null and Missing Behavior]: when groupBy resolves to null or
# missing and a default bucket is specified, the document routes to the
# default bucket.
BUCKET_NULL_MISSING_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": None}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": "other", "count": 1}],
        msg="$bucket should route null groupBy value to the default bucket",
        id="null_routes_to_default",
    ),
    StageTestCase(
        docs=[{"_id": 1}, {"_id": 2, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": "other", "count": 1}],
        msg="$bucket should route missing field to the default bucket",
        id="missing_routes_to_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 15}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$$REMOVE",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": "other", "count": 2}],
        msg="$bucket should route $$REMOVE groupBy to the default bucket",
        id="remove_routes_to_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$add": ["$x", None]},
                    "boundaries": [0, 20],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": "other", "count": 1}],
        msg="$bucket should route null arithmetic result to the default bucket",
        id="null_arithmetic_routes_to_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": {"$literal": None},
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": "other", "count": 1}],
        msg="$bucket should route $literal null groupBy to the default bucket",
        id="literal_null_routes_to_default",
    ),
]

# Property [Half-Open Intervals]: each boundary pair defines a half-open
# interval where the lower bound is inclusive and the upper bound is exclusive.
BUCKET_HALF_OPEN_INTERVAL_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[
            {"_id": 1, "x": 0},
            {"_id": 2, "x": 5},
            {"_id": 3, "x": 10},
            {"_id": 4, "x": 20},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20],
                    "default": "other",
                }
            }
        ],
        expected=[
            {"_id": 0, "count": 2},
            {"_id": 10, "count": 1},
            {"_id": "other", "count": 1},
        ],
        msg=(
            "$bucket lower bound should be inclusive and upper bound"
            " exclusive; value at last upper bound routes to default"
        ),
        id="half_open_lower_inclusive_upper_exclusive",
    ),
]

# Property [Non-Empty Buckets Only]: only buckets containing at least one
# input document appear in the output.
BUCKET_NON_EMPTY_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 25}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20, 30],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": 20, "count": 1}],
        msg="$bucket should omit empty buckets from the output",
        id="only_non_empty_buckets_appear",
    ),
]

# Property [Non-Existent Collection]: a non-existent collection produces an
# empty result array with no error, even without a default.
BUCKET_NONEXISTENT_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=None,
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[],
        msg="$bucket on non-existent collection should return empty result",
        id="nonexistent_collection_with_default",
    ),
    StageTestCase(
        docs=None,
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                }
            }
        ],
        expected=[],
        msg="$bucket on non-existent collection without default should return empty result",
        id="nonexistent_collection_no_default",
    ),
]

# Property [Empty Collection]: an empty but existing collection produces an
# empty result array with no error, even without a default.
BUCKET_EMPTY_COLLECTION_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[],
        msg="$bucket on empty collection should return empty result",
        id="empty_collection_with_default",
    ),
    StageTestCase(
        docs=[],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                }
            }
        ],
        expected=[],
        msg="$bucket on empty collection without default should return empty result",
        id="empty_collection_no_default",
    ),
]

# Property [BSON Type Routing]: all BSON types are accepted as resolved
# groupBy values; types that do not match the boundary type route to the
# default bucket. Null/missing and numeric type promotion is covered
# elsewhere.
BUCKET_BSON_TYPE_ROUTING_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[
            {"_id": 1, "x": "hello"},
            {"_id": 2, "x": True},
            {"_id": 3, "x": datetime(2024, 1, 1, tzinfo=timezone.utc)},
            {"_id": 4, "x": ObjectId("000000000000000000000001")},
            {"_id": 5, "x": Regex("abc")},
            {"_id": 6, "x": Binary(b"hi")},
            {"_id": 7, "x": Code("function(){}")},
            {"_id": 8, "x": Code("function(){}", {"a": 1})},
            {"_id": 9, "x": Timestamp(1, 1)},
            {"_id": 10, "x": [1, 2]},
            {"_id": 11, "x": {"a": 1}},
            {"_id": 12, "x": MinKey()},
            {"_id": 13, "x": MaxKey()},
            {"_id": 14, "x": 5},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": "other", "count": 13}],
        msg=(
            "$bucket should route non-numeric BSON types to the default"
            " bucket when boundaries are numeric"
        ),
        id="mismatched_bson_types_route_to_default",
    ),
]

# Property [Array and Document Comparison]: array and document groupBy values
# are compared as single values using sort comparison logic, not unwrapped.
BUCKET_ARRAY_DOCUMENT_COMPARISON_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[
            {"_id": 1, "x": [5, 15]},
            {"_id": 2, "x": 5},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10, 20],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": "other", "count": 1}],
        msg="$bucket should treat array groupBy as a single value, not unwrap it",
        id="array_groupby_not_unwrapped",
    ),
    StageTestCase(
        docs=[
            {"_id": 1, "x": [1]},
            {"_id": 2, "x": [2]},
            {"_id": 3, "x": [3]},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [[0], [2], [4]],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": [0], "count": 1}, {"_id": [2], "count": 2}],
        msg="$bucket should sort array groupBy values by element-wise comparison",
        id="array_boundaries_element_wise",
    ),
    StageTestCase(
        docs=[
            {"_id": 1, "x": {"a": 1}},
            {"_id": 2, "x": {"a": 3}},
        ],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [{"a": 0}, {"a": 2}, {"a": 4}],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": {"a": 0}, "count": 1}, {"_id": {"a": 2}, "count": 1}],
        msg="$bucket should sort document groupBy values by key comparison",
        id="document_boundaries_key_comparison",
    ),
]

# Property [Default Bucket Routing]: documents whose groupBy value falls
# outside all boundary ranges route to the default bucket; the default
# bucket is not emitted when all documents fall within ranges.
BUCKET_DEFAULT_ROUTING_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": -5}, {"_id": 2, "x": 50}, {"_id": 3, "x": 5}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 1}, {"_id": "other", "count": 2}],
        msg="$bucket should route values below and above boundary ranges to the default bucket",
        id="outside_range_routes_to_default",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 5}, {"_id": 2, "x": 8}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [0, 10],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 0, "count": 2}],
        msg=(
            "$bucket should not emit the default bucket when all"
            " documents fall within boundary ranges"
        ),
        id="default_not_emitted_when_all_in_range",
    ),
]

# Property [Default Bucket Ordering]: the default bucket appears in the
# output ordered by its _id value in BSON comparison order relative to
# boundary bucket _id values.
BUCKET_DEFAULT_ORDERING_TESTS: list[StageTestCase] = [
    StageTestCase(
        docs=[{"_id": 1, "x": 50}, {"_id": 2, "x": 15}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [10, 20],
                    "default": -1,
                }
            }
        ],
        expected=[{"_id": -1, "count": 1}, {"_id": 10, "count": 1}],
        msg="$bucket default with _id less than boundaries should appear first",
        id="default_ordered_before_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}, {"_id": 2, "x": 15}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [10, 20],
                    "default": 100,
                }
            }
        ],
        expected=[{"_id": 10, "count": 1}, {"_id": 100, "count": 1}],
        msg="$bucket default with _id greater than boundaries should appear last",
        id="default_ordered_after_boundaries",
    ),
    StageTestCase(
        docs=[{"_id": 1, "x": 50}, {"_id": 2, "x": 15}],
        pipeline=[
            {
                "$bucket": {
                    "groupBy": "$x",
                    "boundaries": [10, 20],
                    "default": "other",
                }
            }
        ],
        expected=[{"_id": 10, "count": 1}, {"_id": "other", "count": 1}],
        msg=(
            "$bucket string default should appear after numeric boundary"
            " _ids in BSON comparison order"
        ),
        id="default_string_ordered_after_numeric",
    ),
]

BUCKET_ROUTING_TESTS = (
    BUCKET_NULL_MISSING_TESTS
    + BUCKET_HALF_OPEN_INTERVAL_TESTS
    + BUCKET_NON_EMPTY_TESTS
    + BUCKET_NONEXISTENT_COLLECTION_TESTS
    + BUCKET_EMPTY_COLLECTION_TESTS
    + BUCKET_BSON_TYPE_ROUTING_TESTS
    + BUCKET_ARRAY_DOCUMENT_COMPARISON_TESTS
    + BUCKET_DEFAULT_ROUTING_TESTS
    + BUCKET_DEFAULT_ORDERING_TESTS
)


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(BUCKET_ROUTING_TESTS))
def test_bucket_routing(collection, test_case: StageTestCase):
    """Test $bucket document routing behavior."""
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
