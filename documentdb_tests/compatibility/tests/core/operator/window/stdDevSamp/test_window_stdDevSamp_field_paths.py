"""
Tests for $stdDevSamp with nested field paths, array field traversal,
expressions that return different types per document, and $unset/$project
removing fields before $setWindowFields.
"""

from datetime import datetime, timezone

from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command

# Property [Nested Field Paths]: dotted path accesses nested document values


def test_stdDevSamp_dotted_field_path(collection):
    """$stdDevSamp with dotted field path accesses nested document value."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}},
        {"_id": 2, "partition": "A", "data": {"metrics": {"value": 20}}},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$data.metrics.value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # stdDevSamp([10, 20, 30]) = 10.0
    expected = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}, "result": 10.0},
        {"_id": 2, "partition": "A", "data": {"metrics": {"value": 20}}, "result": 10.0},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}, "result": 10.0},
    ]
    assertSuccess(result, expected, msg="dotted field path accesses nested value")


# Property [Missing Path Handling]: missing intermediate or top-level fields are ignored


def test_stdDevSamp_missing_intermediate_path(collection):
    """$stdDevSamp with missing intermediate path treated as missing (ignored)."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"metrics": {"value": 10}}},
        {"_id": 2, "partition": "A", "data": {"other": 99}},
        {"_id": 3, "partition": "A", "data": {"metrics": {"value": 30}}},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$data.metrics.value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Doc 2 missing data.metrics.value -> ignored. stdDevSamp([10, 30]) = 14.142135623730951
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "data": {"metrics": {"value": 10}},
            "result": 14.142135623730951,
        },
        {"_id": 2, "partition": "A", "data": {"other": 99}, "result": 14.142135623730951},
        {
            "_id": 3,
            "partition": "A",
            "data": {"metrics": {"value": 30}},
            "result": 14.142135623730951,
        },
    ]
    assertSuccess(result, expected, msg="missing intermediate path treated as missing")


def test_stdDevSamp_top_level_missing_object(collection):
    """$stdDevSamp where the top-level field of a dotted path is missing."""
    docs = [
        {"_id": 1, "partition": "A", "data": {"value": 10}},
        {"_id": 2, "partition": "A"},
        {"_id": 3, "partition": "A", "data": {"value": 30}},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$data.value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Doc 2 missing "data" entirely -> ignored. stdDevSamp([10, 30]) = 14.142135623730951
    expected = [
        {"_id": 1, "partition": "A", "data": {"value": 10}, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "data": {"value": 30}, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="top-level field missing in dotted path = ignored")


# Property [Non-Numeric Field Types]: arrays, dates, strings are ignored


def test_stdDevSamp_array_field_is_non_numeric(collection):
    """$stdDevSamp on a top-level array field — arrays are non-numeric, should be ignored."""
    docs = [
        {"_id": 1, "partition": "A", "value": [10, 20, 30]},
        {"_id": 2, "partition": "A", "value": 50},
        {"_id": 3, "partition": "A", "value": [40, 50]},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Only doc 2 has a numeric value. Single numeric value -> stdDevSamp = null (N=1, N-1=0)
    expected = [
        {"_id": 1, "partition": "A", "value": [10, 20, 30], "result": None},
        {"_id": 2, "partition": "A", "value": 50, "result": None},
        {"_id": 3, "partition": "A", "value": [40, 50], "result": None},
    ]
    assertSuccess(
        result, expected, msg="array field values are non-numeric — only 1 numeric gives null"
    )


def test_stdDevSamp_date_value_as_expression_ignored(collection):
    """$stdDevSamp with Date value in expression field — non-numeric, ignored."""
    docs = [
        {"_id": 1, "partition": "A", "value": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        {"_id": 2, "partition": "A", "value": 20},
        {"_id": 3, "partition": "A", "value": datetime(2023, 6, 1, tzinfo=timezone.utc)},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # Only doc 2 is numeric -> single value -> stdDevSamp = null (N=1, N-1=0)
    expected = [
        {
            "_id": 1,
            "partition": "A",
            "value": datetime(2023, 1, 1, tzinfo=timezone.utc),
            "result": None,
        },
        {"_id": 2, "partition": "A", "value": 20, "result": None},
        {
            "_id": 3,
            "partition": "A",
            "value": datetime(2023, 6, 1, tzinfo=timezone.utc),
            "result": None,
        },
    ]
    assertSuccess(
        result,
        expected,
        msg="Date values in expression field are non-numeric — only 1 numeric gives null",
    )


# Property [Expression-Based Input]: computed expressions as stdDevSamp input


def test_stdDevSamp_expression_returns_different_types(collection):
    """$stdDevSamp expression returning different types per row — non-numeric ignored."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10},
        {"_id": 2, "partition": "A", "x": -5},
        {"_id": 3, "partition": "A", "x": 30},
        {"_id": 4, "partition": "A", "x": -1},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": {
                                    "$cond": [
                                        {"$gt": ["$x", 0]},
                                        "$x",
                                        "not_a_number",
                                    ]
                                },
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # $cond returns: 10, "not_a_number", 30, "not_a_number"
    # Only numeric: [10, 30] -> stdDevSamp = 14.142135623730951
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "result": 14.142135623730951},
        {"_id": 2, "partition": "A", "x": -5, "result": 14.142135623730951},
        {"_id": 3, "partition": "A", "x": 30, "result": 14.142135623730951},
        {"_id": 4, "partition": "A", "x": -1, "result": 14.142135623730951},
    ]
    assertSuccess(result, expected, msg="expression returning mixed types — non-numeric ignored")


def test_stdDevSamp_expression_returns_null_for_some(collection):
    """$stdDevSamp expression returning null for some docs, number for others."""
    docs = [
        {"_id": 1, "partition": "A", "x": 10, "y": 2},
        {"_id": 2, "partition": "A", "x": 20, "y": None},
        {"_id": 3, "partition": "A", "x": 30, "y": 2},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": {"$multiply": ["$x", "$y"]},
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                }
            ],
            "cursor": {},
        },
    )
    # $multiply: [10*2=20, 20*null=null, 30*2=60]
    # Numeric values: [20, 60] -> stdDevSamp = sqrt(((20-40)^2+(60-40)^2)/1) = sqrt(800) =
    expected = [
        {"_id": 1, "partition": "A", "x": 10, "y": 2, "result": 28.284271247461902},
        {"_id": 2, "partition": "A", "x": 20, "y": None, "result": 28.284271247461902},
        {"_id": 3, "partition": "A", "x": 30, "y": 2, "result": 28.284271247461902},
    ]
    assertSuccess(result, expected, msg="expression returning null for some — null results ignored")


# Property [Pipeline Stage Interaction]: $project/$unset/$match before $setWindowFields


def test_stdDevSamp_project_removes_expression_field(collection):
    """$project removing the expression field before $setWindowFields — treated as missing."""
    docs = [
        {"_id": 1, "partition": "A", "value": 10, "extra": 99},
        {"_id": 2, "partition": "A", "value": 20, "extra": 99},
        {"_id": 3, "partition": "A", "value": 30, "extra": 99},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {"$project": {"partition": 1, "extra": 1}},
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$value",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
            ],
            "cursor": {},
        },
    )
    # All docs missing "value" -> all non-numeric -> result is null
    expected = [
        {"_id": 1, "partition": "A", "extra": 99, "result": None},
        {"_id": 2, "partition": "A", "extra": 99, "result": None},
        {"_id": 3, "partition": "A", "extra": 99, "result": None},
    ]
    assertSuccess(result, expected, msg="$project removing expression field -> all null results")


# Property [Numeric Path Component]:
# Tests that numeric path components access array elements or object keys.


def test_stdDevSamp_numeric_path_component(collection):
    """$stdDevSamp with numeric path component accesses array element or object key."""
    docs = [
        {"_id": 1, "partition": "A", "arr": [{"field": 10}, {"field": 20}]},
        {"_id": 2, "partition": "A", "arr": [{"field": 30}, {"field": 40}]},
        {"_id": 3, "partition": "A", "arr": [{"field": 50}, {"field": 60}]},
    ]
    collection.insert_many(docs)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": [
                {
                    "$setWindowFields": {
                        "partitionBy": "$partition",
                        "sortBy": {"_id": 1},
                        "output": {
                            "result": {
                                "$stdDevSamp": "$arr.0.field",
                                "window": {"documents": ["unbounded", "unbounded"]},
                            }
                        },
                    }
                },
                {"$project": {"_id": 1, "result": 1}},
            ],
            "cursor": {},
        },
    )
    # In $setWindowFields context, $arr.0.field does not resolve to array element —
    # the path returns non-numeric (array) values which are ignored, resulting in null.
    expected = [
        {"_id": 1, "result": None},
        {"_id": 2, "result": None},
        {"_id": 3, "result": None},
    ]
    assertSuccess(result, expected, msg="numeric path component in window context returns null")
