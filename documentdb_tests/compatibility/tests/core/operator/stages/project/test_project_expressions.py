"""Tests that each expression operator works within $project."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Support]: each expression operator produces the correct
# result when used as a computed field in $project.
PROJECT_EXPRESSION_TESTS: list[StageTestCase] = [
    # Arithmetic.
    StageTestCase(
        "expr_abs",
        docs=[{"_id": 1, "a": -5}],
        pipeline=[{"$project": {"r": {"$abs": "$a"}}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$abs should work in $project",
    ),
    StageTestCase(
        "expr_add",
        docs=[{"_id": 1, "a": 3, "b": 4}],
        pipeline=[{"$project": {"r": {"$add": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$add should work in $project",
    ),
    StageTestCase(
        "expr_ceil",
        docs=[{"_id": 1, "a": 2.3}],
        pipeline=[{"$project": {"r": {"$ceil": "$a"}}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$ceil should work in $project",
    ),
    StageTestCase(
        "expr_divide",
        docs=[{"_id": 1, "a": 10, "b": 4}],
        pipeline=[{"$project": {"r": {"$divide": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 2.5}],
        msg="$divide should work in $project",
    ),
    StageTestCase(
        "expr_exp",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$project": {"r": {"$exp": "$a"}}}],
        expected=[{"_id": 1, "r": 1.0}],
        msg="$exp should work in $project",
    ),
    StageTestCase(
        "expr_floor",
        docs=[{"_id": 1, "a": 2.7}],
        pipeline=[{"$project": {"r": {"$floor": "$a"}}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$floor should work in $project",
    ),
    StageTestCase(
        "expr_ln",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"r": {"$ln": "$a"}}}],
        expected=[{"_id": 1, "r": 2.302585092994046}],
        msg="$ln should work in $project",
    ),
    StageTestCase(
        "expr_log",
        docs=[{"_id": 1, "a": 100, "b": 10}],
        pipeline=[{"$project": {"r": {"$log": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$log should work in $project",
    ),
    StageTestCase(
        "expr_log10",
        docs=[{"_id": 1, "a": 1000}],
        pipeline=[{"$project": {"r": {"$log10": "$a"}}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$log10 should work in $project",
    ),
    StageTestCase(
        "expr_mod",
        docs=[{"_id": 1, "a": 10, "b": 3}],
        pipeline=[{"$project": {"r": {"$mod": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$mod should work in $project",
    ),
    StageTestCase(
        "expr_multiply",
        docs=[{"_id": 1, "a": 3, "b": 4}],
        pipeline=[{"$project": {"r": {"$multiply": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 12}],
        msg="$multiply should work in $project",
    ),
    StageTestCase(
        "expr_pow",
        docs=[{"_id": 1, "a": 2, "b": 3}],
        pipeline=[{"$project": {"r": {"$pow": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 8}],
        msg="$pow should work in $project",
    ),
    StageTestCase(
        "expr_round",
        docs=[{"_id": 1, "a": 2.567}],
        pipeline=[{"$project": {"r": {"$round": ["$a", 1]}}}],
        expected=[{"_id": 1, "r": 2.6}],
        msg="$round should work in $project",
    ),
    StageTestCase(
        "expr_sqrt",
        docs=[{"_id": 1, "a": 9}],
        pipeline=[{"$project": {"r": {"$sqrt": "$a"}}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$sqrt should work in $project",
    ),
    StageTestCase(
        "expr_subtract",
        docs=[{"_id": 1, "a": 10, "b": 3}],
        pipeline=[{"$project": {"r": {"$subtract": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$subtract should work in $project",
    ),
    StageTestCase(
        "expr_trunc",
        docs=[{"_id": 1, "a": 2.9}],
        pipeline=[{"$project": {"r": {"$trunc": "$a"}}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$trunc should work in $project",
    ),
    StageTestCase(
        "expr_sigmoid",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$project": {"r": {"$sigmoid": "$a"}}}],
        expected=[{"_id": 1, "r": 0.5}],
        msg="$sigmoid should work in $project",
    ),
    # Array.
    StageTestCase(
        "expr_arrayElemAt",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"r": {"$arrayElemAt": ["$a", 1]}}}],
        expected=[{"_id": 1, "r": 20}],
        msg="$arrayElemAt should work in $project",
    ),
    StageTestCase(
        "expr_arrayToObject",
        docs=[{"_id": 1, "a": [["k", "v"]]}],
        pipeline=[{"$project": {"r": {"$arrayToObject": "$a"}}}],
        expected=[{"_id": 1, "r": {"k": "v"}}],
        msg="$arrayToObject should work in $project",
    ),
    StageTestCase(
        "expr_concatArrays",
        docs=[{"_id": 1, "a": [1], "b": [2]}],
        pipeline=[{"$project": {"r": {"$concatArrays": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$concatArrays should work in $project",
    ),
    StageTestCase(
        "expr_filter",
        docs=[{"_id": 1, "a": [1, 2, 3, 4]}],
        pipeline=[
            {"$project": {"r": {"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 2]}}}}}
        ],
        expected=[{"_id": 1, "r": [3, 4]}],
        msg="$filter should work in $project",
    ),
    StageTestCase(
        "expr_firstN",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$project": {"r": {"$firstN": {"input": "$a", "n": 2}}}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$firstN should work in $project",
    ),
    StageTestCase(
        "expr_in",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[{"$project": {"r": {"$in": ["$a", [1, 2, 3]]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$in should work in $project",
    ),
    StageTestCase(
        "expr_indexOfArray",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"r": {"$indexOfArray": ["$a", 20]}}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$indexOfArray should work in $project",
    ),
    StageTestCase(
        "expr_isArray",
        docs=[{"_id": 1, "a": [1, 2]}],
        pipeline=[{"$project": {"r": {"$isArray": "$a"}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$isArray should work in $project",
    ),
    StageTestCase(
        "expr_lastN",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$project": {"r": {"$lastN": {"input": "$a", "n": 2}}}}],
        expected=[{"_id": 1, "r": [2, 3]}],
        msg="$lastN should work in $project",
    ),
    StageTestCase(
        "expr_map",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[
            {"$project": {"r": {"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}}}}
        ],
        expected=[{"_id": 1, "r": [2, 4, 6]}],
        msg="$map should work in $project",
    ),
    StageTestCase(
        "expr_maxN_array",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$project": {"r": {"$maxN": {"input": "$a", "n": 2}}}}],
        expected=[{"_id": 1, "r": [3, 2]}],
        msg="$maxN should work in $project",
    ),
    StageTestCase(
        "expr_minN_array",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$project": {"r": {"$minN": {"input": "$a", "n": 2}}}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$minN should work in $project",
    ),
    StageTestCase(
        "expr_objectToArray",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$project": {"r": {"$objectToArray": "$a"}}}],
        expected=[{"_id": 1, "r": [{"k": "x", "v": 1}]}],
        msg="$objectToArray should work in $project",
    ),
    StageTestCase(
        "expr_range",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"r": {"$range": [0, 3]}}}],
        expected=[{"_id": 1, "r": [0, 1, 2]}],
        msg="$range should work in $project",
    ),
    StageTestCase(
        "expr_reduce",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[
            {
                "$project": {
                    "r": {
                        "$reduce": {
                            "input": "$a",
                            "initialValue": 0,
                            "in": {"$add": ["$$value", "$$this"]},
                        }
                    }
                }
            }
        ],
        expected=[{"_id": 1, "r": 6}],
        msg="$reduce should work in $project",
    ),
    StageTestCase(
        "expr_reverseArray",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$project": {"r": {"$reverseArray": "$a"}}}],
        expected=[{"_id": 1, "r": [3, 2, 1]}],
        msg="$reverseArray should work in $project",
    ),
    StageTestCase(
        "expr_size",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$project": {"r": {"$size": "$a"}}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$size should work in $project",
    ),
    StageTestCase(
        "expr_slice",
        docs=[{"_id": 1, "a": [1, 2, 3, 4]}],
        pipeline=[{"$project": {"r": {"$slice": ["$a", 2]}}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$slice should work in $project",
    ),
    StageTestCase(
        "expr_sortArray",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$project": {"r": {"$sortArray": {"input": "$a", "sortBy": 1}}}}],
        expected=[{"_id": 1, "r": [1, 2, 3]}],
        msg="$sortArray should work in $project",
    ),
    StageTestCase(
        "expr_zip",
        docs=[{"_id": 1, "a": [1, 2], "b": [3, 4]}],
        pipeline=[{"$project": {"r": {"$zip": {"inputs": ["$a", "$b"]}}}}],
        expected=[{"_id": 1, "r": [[1, 3], [2, 4]]}],
        msg="$zip should work in $project",
    ),
    # Bitwise.
    StageTestCase(
        "expr_bitAnd",
        docs=[{"_id": 1, "a": 7, "b": 3}],
        pipeline=[{"$project": {"r": {"$bitAnd": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$bitAnd should work in $project",
    ),
    StageTestCase(
        "expr_bitNot",
        docs=[{"_id": 1, "a": Int64(5)}],
        pipeline=[{"$project": {"r": {"$bitNot": "$a"}}}],
        expected=[{"_id": 1, "r": Int64(-6)}],
        msg="$bitNot should work in $project",
    ),
    StageTestCase(
        "expr_bitOr",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$project": {"r": {"$bitOr": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$bitOr should work in $project",
    ),
    StageTestCase(
        "expr_bitXor",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$project": {"r": {"$bitXor": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 6}],
        msg="$bitXor should work in $project",
    ),
    # Boolean.
    StageTestCase(
        "expr_and",
        docs=[{"_id": 1, "a": True, "b": False}],
        pipeline=[{"$project": {"r": {"$and": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": False}],
        msg="$and should work in $project",
    ),
    StageTestCase(
        "expr_not",
        docs=[{"_id": 1, "a": False}],
        pipeline=[{"$project": {"r": {"$not": ["$a"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$not should work in $project",
    ),
    StageTestCase(
        "expr_or",
        docs=[{"_id": 1, "a": False, "b": True}],
        pipeline=[{"$project": {"r": {"$or": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$or should work in $project",
    ),
    # Comparisons.
    StageTestCase(
        "expr_cmp",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$project": {"r": {"$cmp": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$cmp should work in $project",
    ),
    StageTestCase(
        "expr_eq",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        pipeline=[{"$project": {"r": {"$eq": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$eq should work in $project",
    ),
    StageTestCase(
        "expr_gt",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$project": {"r": {"$gt": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$gt should work in $project",
    ),
    StageTestCase(
        "expr_gte",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        pipeline=[{"$project": {"r": {"$gte": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$gte should work in $project",
    ),
    StageTestCase(
        "expr_lt",
        docs=[{"_id": 1, "a": 3, "b": 5}],
        pipeline=[{"$project": {"r": {"$lt": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$lt should work in $project",
    ),
    StageTestCase(
        "expr_lte",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        pipeline=[{"$project": {"r": {"$lte": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$lte should work in $project",
    ),
    StageTestCase(
        "expr_ne",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$project": {"r": {"$ne": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$ne should work in $project",
    ),
    # Conditional.
    StageTestCase(
        "expr_cond",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$project": {"r": {"$cond": [{"$gt": ["$a", 5]}, "big", "small"]}}}],
        expected=[{"_id": 1, "r": "big"}],
        msg="$cond should work in $project",
    ),
    StageTestCase(
        "expr_ifNull",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$project": {"r": {"$ifNull": ["$a", "default"]}}}],
        expected=[{"_id": 1, "r": "default"}],
        msg="$ifNull should work in $project",
    ),
    StageTestCase(
        "expr_switch",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[
            {
                "$project": {
                    "r": {
                        "$switch": {
                            "branches": [{"case": {"$eq": ["$a", 2]}, "then": "two"}],
                            "default": "other",
                        }
                    }
                }
            }
        ],
        expected=[{"_id": 1, "r": "two"}],
        msg="$switch should work in $project",
    ),
    # Date.
    StageTestCase(
        "expr_dateAdd",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[
            {"$project": {"r": {"$dateAdd": {"startDate": "$d", "unit": "day", "amount": 1}}}}
        ],
        expected=[{"_id": 1, "r": datetime(2024, 1, 2)}],
        msg="$dateAdd should work in $project",
    ),
    StageTestCase(
        "expr_dateDiff",
        docs=[
            {
                "_id": 1,
                "a": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "b": datetime(2024, 1, 4, tzinfo=timezone.utc),
            }
        ],
        pipeline=[
            {"$project": {"r": {"$dateDiff": {"startDate": "$a", "endDate": "$b", "unit": "day"}}}}
        ],
        expected=[{"_id": 1, "r": Int64(3)}],
        msg="$dateDiff should work in $project",
    ),
    StageTestCase(
        "expr_dateFromParts",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"r": {"$dateFromParts": {"year": 2024, "month": 6, "day": 15}}}}],
        expected=[{"_id": 1, "r": datetime(2024, 6, 15)}],
        msg="$dateFromParts should work in $project",
    ),
    StageTestCase(
        "expr_dateFromString",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"r": {"$dateFromString": {"dateString": "2024-01-01"}}}}],
        expected=[{"_id": 1, "r": datetime(2024, 1, 1)}],
        msg="$dateFromString should work in $project",
    ),
    StageTestCase(
        "expr_dateSubtract",
        docs=[{"_id": 1, "d": datetime(2024, 1, 3, tzinfo=timezone.utc)}],
        pipeline=[
            {"$project": {"r": {"$dateSubtract": {"startDate": "$d", "unit": "day", "amount": 1}}}}
        ],
        expected=[{"_id": 1, "r": datetime(2024, 1, 2)}],
        msg="$dateSubtract should work in $project",
    ),
    StageTestCase(
        "expr_dateToParts",
        docs=[{"_id": 1, "d": datetime(2024, 3, 15, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$dateToParts": {"date": "$d"}}}}],
        expected=[
            {
                "_id": 1,
                "r": {
                    "year": 2024,
                    "month": 3,
                    "day": 15,
                    "hour": 0,
                    "minute": 0,
                    "second": 0,
                    "millisecond": 0,
                },
            }
        ],
        msg="$dateToParts should work in $project",
    ),
    StageTestCase(
        "expr_dateToString",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$dateToString": {"date": "$d", "format": "%Y-%m-%d"}}}}],
        expected=[{"_id": 1, "r": "2024-01-01"}],
        msg="$dateToString should work in $project",
    ),
    StageTestCase(
        "expr_dateTrunc",
        docs=[{"_id": 1, "d": datetime(2024, 3, 15, 10, 30, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$dateTrunc": {"date": "$d", "unit": "month"}}}}],
        expected=[{"_id": 1, "r": datetime(2024, 3, 1)}],
        msg="$dateTrunc should work in $project",
    ),
    StageTestCase(
        "expr_dayOfMonth",
        docs=[{"_id": 1, "d": datetime(2024, 3, 15, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$dayOfMonth": "$d"}}}],
        expected=[{"_id": 1, "r": 15}],
        msg="$dayOfMonth should work in $project",
    ),
    StageTestCase(
        "expr_dayOfWeek",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$dayOfWeek": "$d"}}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$dayOfWeek should work in $project",
    ),
    StageTestCase(
        "expr_dayOfYear",
        docs=[{"_id": 1, "d": datetime(2024, 2, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$dayOfYear": "$d"}}}],
        expected=[{"_id": 1, "r": 32}],
        msg="$dayOfYear should work in $project",
    ),
    StageTestCase(
        "expr_hour",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 14, 0, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$hour": "$d"}}}],
        expected=[{"_id": 1, "r": 14}],
        msg="$hour should work in $project",
    ),
    StageTestCase(
        "expr_isoDayOfWeek",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$isoDayOfWeek": "$d"}}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$isoDayOfWeek should work in $project",
    ),
    StageTestCase(
        "expr_isoWeek",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$isoWeek": "$d"}}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$isoWeek should work in $project",
    ),
    StageTestCase(
        "expr_isoWeekYear",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$isoWeekYear": "$d"}}}],
        expected=[{"_id": 1, "r": Int64(2024)}],
        msg="$isoWeekYear should work in $project",
    ),
    StageTestCase(
        "expr_millisecond",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$millisecond": "$d"}}}],
        expected=[{"_id": 1, "r": 123}],
        msg="$millisecond should work in $project",
    ),
    StageTestCase(
        "expr_minute",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 10, 45, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$minute": "$d"}}}],
        expected=[{"_id": 1, "r": 45}],
        msg="$minute should work in $project",
    ),
    StageTestCase(
        "expr_month",
        docs=[{"_id": 1, "d": datetime(2024, 7, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$month": "$d"}}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$month should work in $project",
    ),
    StageTestCase(
        "expr_second",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 0, 0, 30, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$second": "$d"}}}],
        expected=[{"_id": 1, "r": 30}],
        msg="$second should work in $project",
    ),
    StageTestCase(
        "expr_toDate",
        docs=[{"_id": 1, "a": Int64(1704067200000)}],
        pipeline=[{"$project": {"r": {"$toDate": "$a"}}}],
        expected=[{"_id": 1, "r": datetime(2024, 1, 1)}],
        msg="$toDate should work in $project",
    ),
    StageTestCase(
        "expr_week",
        docs=[{"_id": 1, "d": datetime(2024, 1, 15, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$week": "$d"}}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$week should work in $project",
    ),
    StageTestCase(
        "expr_year",
        docs=[{"_id": 1, "d": datetime(2024, 6, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$project": {"r": {"$year": "$d"}}}],
        expected=[{"_id": 1, "r": 2024}],
        msg="$year should work in $project",
    ),
    # Misc.
    StageTestCase(
        "expr_binarySize",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$binarySize": "$a"}}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$binarySize should work in $project",
    ),
    StageTestCase(
        "expr_bsonSize",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$project": {"r": {"$bsonSize": "$a"}}}],
        expected=[{"_id": 1, "r": 12}],
        msg="$bsonSize should work in $project",
    ),
    StageTestCase(
        "expr_getField",
        docs=[{"_id": 1, "a": {"x": 42}}],
        pipeline=[{"$project": {"r": {"$getField": {"field": "x", "input": "$a"}}}}],
        expected=[{"_id": 1, "r": 42}],
        msg="$getField should work in $project",
    ),
    StageTestCase(
        "expr_let",
        docs=[{"_id": 1, "a": 5}],
        pipeline=[
            {"$project": {"r": {"$let": {"vars": {"x": "$a"}, "in": {"$multiply": ["$$x", 2]}}}}}
        ],
        expected=[{"_id": 1, "r": 10}],
        msg="$let should work in $project",
    ),
    StageTestCase(
        "expr_literal",
        docs=[{"_id": 1}],
        pipeline=[{"$project": {"r": {"$literal": "$notAFieldPath"}}}],
        expected=[{"_id": 1, "r": "$notAFieldPath"}],
        msg="$literal should work in $project",
    ),
    StageTestCase(
        "expr_toHashedIndexKey",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$toHashedIndexKey": "$a"}}}],
        expected=[{"_id": 1, "r": Int64(5347277839332858538)}],
        msg="$toHashedIndexKey should work in $project",
    ),
    # Object.
    StageTestCase(
        "expr_mergeObjects",
        docs=[{"_id": 1, "a": {"x": 1}, "b": {"y": 2}}],
        pipeline=[{"$project": {"r": {"$mergeObjects": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": {"x": 1, "y": 2}}],
        msg="$mergeObjects should work in $project",
    ),
    StageTestCase(
        "expr_setField",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$project": {"r": {"$setField": {"field": "y", "input": "$a", "value": 2}}}}],
        expected=[{"_id": 1, "r": {"x": 1, "y": 2}}],
        msg="$setField should work in $project",
    ),
    StageTestCase(
        "expr_unsetField",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        pipeline=[{"$project": {"r": {"$unsetField": {"field": "x", "input": "$a"}}}}],
        expected=[{"_id": 1, "r": {"y": 2}}],
        msg="$unsetField should work in $project",
    ),
    # Set.
    StageTestCase(
        "expr_allElementsTrue",
        docs=[{"_id": 1, "a": [True, True]}],
        pipeline=[{"$project": {"r": {"$allElementsTrue": ["$a"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$allElementsTrue should work in $project",
    ),
    StageTestCase(
        "expr_anyElementTrue",
        docs=[{"_id": 1, "a": [False, True]}],
        pipeline=[{"$project": {"r": {"$anyElementTrue": ["$a"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$anyElementTrue should work in $project",
    ),
    StageTestCase(
        "expr_setDifference",
        docs=[{"_id": 1, "a": [1, 2, 3], "b": [2]}],
        pipeline=[{"$project": {"r": {"$setDifference": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": [1, 3]}],
        msg="$setDifference should work in $project",
    ),
    StageTestCase(
        "expr_setEquals",
        docs=[{"_id": 1, "a": [1, 2], "b": [2, 1]}],
        pipeline=[{"$project": {"r": {"$setEquals": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$setEquals should work in $project",
    ),
    StageTestCase(
        "expr_setIntersection",
        docs=[{"_id": 1, "a": [1, 2, 3], "b": [2, 3, 4]}],
        pipeline=[{"$project": {"r": {"$setIntersection": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": [2, 3]}],
        msg="$setIntersection should work in $project",
    ),
    StageTestCase(
        "expr_setIsSubset",
        docs=[{"_id": 1, "a": [1, 2], "b": [1, 2, 3]}],
        pipeline=[{"$project": {"r": {"$setIsSubset": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$setIsSubset should work in $project",
    ),
    # String.
    StageTestCase(
        "expr_concat",
        docs=[{"_id": 1, "a": "hello", "b": " world"}],
        pipeline=[{"$project": {"r": {"$concat": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": "hello world"}],
        msg="$concat should work in $project",
    ),
    StageTestCase(
        "expr_indexOfBytes",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$indexOfBytes": ["$a", "ll"]}}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$indexOfBytes should work in $project",
    ),
    StageTestCase(
        "expr_indexOfCP",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$indexOfCP": ["$a", "ll"]}}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$indexOfCP should work in $project",
    ),
    StageTestCase(
        "expr_ltrim",
        docs=[{"_id": 1, "a": "  hi"}],
        pipeline=[{"$project": {"r": {"$ltrim": {"input": "$a"}}}}],
        expected=[{"_id": 1, "r": "hi"}],
        msg="$ltrim should work in $project",
    ),
    StageTestCase(
        "expr_regexFind",
        docs=[{"_id": 1, "a": "hello 123"}],
        pipeline=[{"$project": {"r": {"$regexFind": {"input": "$a", "regex": "[0-9]+"}}}}],
        expected=[{"_id": 1, "r": {"match": "123", "idx": 6, "captures": []}}],
        msg="$regexFind should work in $project",
    ),
    StageTestCase(
        "expr_regexFindAll",
        docs=[{"_id": 1, "a": "a1b2"}],
        pipeline=[{"$project": {"r": {"$regexFindAll": {"input": "$a", "regex": "[0-9]"}}}}],
        expected=[
            {
                "_id": 1,
                "r": [
                    {"match": "1", "idx": 1, "captures": []},
                    {"match": "2", "idx": 3, "captures": []},
                ],
            }
        ],
        msg="$regexFindAll should work in $project",
    ),
    StageTestCase(
        "expr_regexMatch",
        docs=[{"_id": 1, "a": "hello123"}],
        pipeline=[{"$project": {"r": {"$regexMatch": {"input": "$a", "regex": "[0-9]+"}}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$regexMatch should work in $project",
    ),
    StageTestCase(
        "expr_replaceAll",
        docs=[{"_id": 1, "a": "aabbcc"}],
        pipeline=[
            {"$project": {"r": {"$replaceAll": {"input": "$a", "find": "b", "replacement": "x"}}}}
        ],
        expected=[{"_id": 1, "r": "aaxxcc"}],
        msg="$replaceAll should work in $project",
    ),
    StageTestCase(
        "expr_replaceOne",
        docs=[{"_id": 1, "a": "aabbcc"}],
        pipeline=[
            {"$project": {"r": {"$replaceOne": {"input": "$a", "find": "b", "replacement": "x"}}}}
        ],
        expected=[{"_id": 1, "r": "aaxbcc"}],
        msg="$replaceOne should work in $project",
    ),
    StageTestCase(
        "expr_rtrim",
        docs=[{"_id": 1, "a": "hi  "}],
        pipeline=[{"$project": {"r": {"$rtrim": {"input": "$a"}}}}],
        expected=[{"_id": 1, "r": "hi"}],
        msg="$rtrim should work in $project",
    ),
    StageTestCase(
        "expr_split",
        docs=[{"_id": 1, "a": "a,b,c"}],
        pipeline=[{"$project": {"r": {"$split": ["$a", ","]}}}],
        expected=[{"_id": 1, "r": ["a", "b", "c"]}],
        msg="$split should work in $project",
    ),
    StageTestCase(
        "expr_strcasecmp",
        docs=[{"_id": 1, "a": "abc", "b": "ABC"}],
        pipeline=[{"$project": {"r": {"$strcasecmp": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 0}],
        msg="$strcasecmp should work in $project",
    ),
    StageTestCase(
        "expr_strLenBytes",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$strLenBytes": "$a"}}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$strLenBytes should work in $project",
    ),
    StageTestCase(
        "expr_strLenCP",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$strLenCP": "$a"}}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$strLenCP should work in $project",
    ),
    StageTestCase(
        "expr_substr",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$substr": ["$a", 1, 3]}}}],
        expected=[{"_id": 1, "r": "ell"}],
        msg="$substr should work in $project",
    ),
    StageTestCase(
        "expr_substrBytes",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$substrBytes": ["$a", 1, 3]}}}],
        expected=[{"_id": 1, "r": "ell"}],
        msg="$substrBytes should work in $project",
    ),
    StageTestCase(
        "expr_substrCP",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$substrCP": ["$a", 1, 3]}}}],
        expected=[{"_id": 1, "r": "ell"}],
        msg="$substrCP should work in $project",
    ),
    StageTestCase(
        "expr_toLower",
        docs=[{"_id": 1, "a": "HELLO"}],
        pipeline=[{"$project": {"r": {"$toLower": "$a"}}}],
        expected=[{"_id": 1, "r": "hello"}],
        msg="$toLower should work in $project",
    ),
    StageTestCase(
        "expr_toString",
        docs=[{"_id": 1, "a": 123}],
        pipeline=[{"$project": {"r": {"$toString": "$a"}}}],
        expected=[{"_id": 1, "r": "123"}],
        msg="$toString should work in $project",
    ),
    StageTestCase(
        "expr_toUpper",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$project": {"r": {"$toUpper": "$a"}}}],
        expected=[{"_id": 1, "r": "HELLO"}],
        msg="$toUpper should work in $project",
    ),
    StageTestCase(
        "expr_trim",
        docs=[{"_id": 1, "a": "  hi  "}],
        pipeline=[{"$project": {"r": {"$trim": {"input": "$a"}}}}],
        expected=[{"_id": 1, "r": "hi"}],
        msg="$trim should work in $project",
    ),
    # Timestamp.
    StageTestCase(
        "expr_tsIncrement",
        docs=[{"_id": 1, "t": Timestamp(100, 5)}],
        pipeline=[{"$project": {"r": {"$tsIncrement": "$t"}}}],
        expected=[{"_id": 1, "r": Int64(5)}],
        msg="$tsIncrement should work in $project",
    ),
    StageTestCase(
        "expr_tsSecond",
        docs=[{"_id": 1, "t": Timestamp(100, 5)}],
        pipeline=[{"$project": {"r": {"$tsSecond": "$t"}}}],
        expected=[{"_id": 1, "r": Int64(100)}],
        msg="$tsSecond should work in $project",
    ),
    # Trigonometry.
    StageTestCase(
        "expr_acos",
        docs=[{"_id": 1, "a": 0.5}],
        pipeline=[{"$project": {"r": {"$acos": "$a"}}}],
        expected=[{"_id": 1, "r": 1.0471975511965979}],
        msg="$acos should work in $project",
    ),
    StageTestCase(
        "expr_acosh",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[{"$project": {"r": {"$acosh": "$a"}}}],
        expected=[{"_id": 1, "r": 1.3169578969248166}],
        msg="$acosh should work in $project",
    ),
    StageTestCase(
        "expr_asin",
        docs=[{"_id": 1, "a": 0.5}],
        pipeline=[{"$project": {"r": {"$asin": "$a"}}}],
        expected=[{"_id": 1, "r": 0.5235987755982989}],
        msg="$asin should work in $project",
    ),
    StageTestCase(
        "expr_asinh",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$asinh": "$a"}}}],
        expected=[{"_id": 1, "r": 0.881373587019543}],
        msg="$asinh should work in $project",
    ),
    StageTestCase(
        "expr_atan",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$atan": "$a"}}}],
        expected=[{"_id": 1, "r": 0.7853981633974483}],
        msg="$atan should work in $project",
    ),
    StageTestCase(
        "expr_atan2",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        pipeline=[{"$project": {"r": {"$atan2": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": 0.7853981633974483}],
        msg="$atan2 should work in $project",
    ),
    StageTestCase(
        "expr_atanh",
        docs=[{"_id": 1, "a": 0.5}],
        pipeline=[{"$project": {"r": {"$atanh": "$a"}}}],
        expected=[{"_id": 1, "r": 0.5493061443340548}],
        msg="$atanh should work in $project",
    ),
    StageTestCase(
        "expr_cos",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$project": {"r": {"$cos": "$a"}}}],
        expected=[{"_id": 1, "r": 1.0}],
        msg="$cos should work in $project",
    ),
    StageTestCase(
        "expr_cosh",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$project": {"r": {"$cosh": "$a"}}}],
        expected=[{"_id": 1, "r": 1.0}],
        msg="$cosh should work in $project",
    ),
    StageTestCase(
        "expr_degreesToRadians",
        docs=[{"_id": 1, "a": 90}],
        pipeline=[{"$project": {"r": {"$degreesToRadians": "$a"}}}],
        expected=[{"_id": 1, "r": 1.5707963267948966}],
        msg="$degreesToRadians should work in $project",
    ),
    StageTestCase(
        "expr_radiansToDegrees",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$radiansToDegrees": "$a"}}}],
        expected=[{"_id": 1, "r": 57.29577951308232}],
        msg="$radiansToDegrees should work in $project",
    ),
    StageTestCase(
        "expr_sin",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$sin": "$a"}}}],
        expected=[{"_id": 1, "r": 0.8414709848078965}],
        msg="$sin should work in $project",
    ),
    StageTestCase(
        "expr_sinh",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$sinh": "$a"}}}],
        expected=[{"_id": 1, "r": 1.1752011936438014}],
        msg="$sinh should work in $project",
    ),
    StageTestCase(
        "expr_tan",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$tan": "$a"}}}],
        expected=[{"_id": 1, "r": 1.5574077246549023}],
        msg="$tan should work in $project",
    ),
    StageTestCase(
        "expr_tanh",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$tanh": "$a"}}}],
        expected=[{"_id": 1, "r": 0.7615941559557649}],
        msg="$tanh should work in $project",
    ),
    # Type.
    StageTestCase(
        "expr_convert",
        docs=[{"_id": 1, "a": "123"}],
        pipeline=[{"$project": {"r": {"$convert": {"input": "$a", "to": "int"}}}}],
        expected=[{"_id": 1, "r": 123}],
        msg="$convert should work in $project",
    ),
    StageTestCase(
        "expr_isNumber",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"r": {"$isNumber": "$a"}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$isNumber should work in $project",
    ),
    StageTestCase(
        "expr_toBool",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$project": {"r": {"$toBool": "$a"}}}],
        expected=[{"_id": 1, "r": True}],
        msg="$toBool should work in $project",
    ),
    StageTestCase(
        "expr_toDecimal",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"r": {"$toDecimal": "$a"}}}],
        expected=[{"_id": 1, "r": Decimal128("42")}],
        msg="$toDecimal should work in $project",
    ),
    StageTestCase(
        "expr_toDouble",
        docs=[{"_id": 1, "a": "3.14"}],
        pipeline=[{"$project": {"r": {"$toDouble": "$a"}}}],
        expected=[{"_id": 1, "r": 3.14}],
        msg="$toDouble should work in $project",
    ),
    StageTestCase(
        "expr_toInt",
        docs=[{"_id": 1, "a": 3.9}],
        pipeline=[{"$project": {"r": {"$toInt": "$a"}}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$toInt should work in $project",
    ),
    StageTestCase(
        "expr_toLong",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"r": {"$toLong": "$a"}}}],
        expected=[{"_id": 1, "r": Int64(42)}],
        msg="$toLong should work in $project",
    ),
    StageTestCase(
        "expr_toObjectId",
        docs=[{"_id": 1, "a": "507f1f77bcf86cd799439011"}],
        pipeline=[{"$project": {"r": {"$toObjectId": "$a"}}}],
        expected=[{"_id": 1, "r": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$toObjectId should work in $project",
    ),
    StageTestCase(
        "expr_type",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$project": {"r": {"$type": "$a"}}}],
        expected=[{"_id": 1, "r": "int"}],
        msg="$type should work in $project",
    ),
    StageTestCase(
        "expr_toUUID",
        docs=[{"_id": 1, "a": "12345678-1234-1234-1234-123456789abc"}],
        pipeline=[{"$project": {"r": {"$toUUID": "$a"}}}],
        expected=[{"_id": 1, "r": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc"))}],
        msg="$toUUID should work in $project",
    ),
    # Accumulator (as expressions in $project).
    StageTestCase(
        "expr_sum",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$project": {"r": {"$sum": "$a"}}}],
        expected=[{"_id": 1, "r": 6}],
        msg="$sum should work in $project",
    ),
    StageTestCase(
        "expr_avg",
        docs=[{"_id": 1, "a": [2, 4, 6]}],
        pipeline=[{"$project": {"r": {"$avg": "$a"}}}],
        expected=[{"_id": 1, "r": 4.0}],
        msg="$avg should work in $project",
    ),
    StageTestCase(
        "expr_min",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$project": {"r": {"$min": "$a"}}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$min should work in $project",
    ),
    StageTestCase(
        "expr_max",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$project": {"r": {"$max": "$a"}}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$max should work in $project",
    ),
    StageTestCase(
        "expr_first",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"r": {"$first": "$a"}}}],
        expected=[{"_id": 1, "r": 10}],
        msg="$first should work in $project",
    ),
    StageTestCase(
        "expr_last",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$project": {"r": {"$last": "$a"}}}],
        expected=[{"_id": 1, "r": 30}],
        msg="$last should work in $project",
    ),
    StageTestCase(
        "expr_stdDevPop",
        docs=[{"_id": 1, "a": [2, 4, 4, 4, 5, 5, 7, 9]}],
        pipeline=[{"$project": {"r": {"$stdDevPop": "$a"}}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$stdDevPop should work in $project",
    ),
    StageTestCase(
        "expr_stdDevSamp",
        docs=[{"_id": 1, "a": [1, 3]}],
        pipeline=[{"$project": {"r": {"$stdDevSamp": "$a"}}}],
        expected=[{"_id": 1, "r": 1.4142135623730951}],
        msg="$stdDevSamp should work in $project",
    ),
    StageTestCase(
        "expr_median",
        docs=[{"_id": 1, "a": [1, 2, 3, 4, 5]}],
        pipeline=[{"$project": {"r": {"$median": {"input": "$a", "method": "approximate"}}}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$median should work in $project",
    ),
    StageTestCase(
        "expr_percentile",
        docs=[{"_id": 1, "a": [1, 2, 3, 4, 5]}],
        pipeline=[
            {
                "$project": {
                    "r": {"$percentile": {"input": "$a", "p": [0.5], "method": "approximate"}}
                }
            }
        ],
        expected=[{"_id": 1, "r": [3.0]}],
        msg="$percentile should work in $project",
    ),
    # Set (additional).
    StageTestCase(
        "expr_setUnion",
        docs=[{"_id": 1, "a": [1, 2], "b": [2, 3]}],
        pipeline=[{"$project": {"r": {"$setUnion": ["$a", "$b"]}}}],
        expected=[{"_id": 1, "r": [1, 2, 3]}],
        msg="$setUnion should work in $project",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("test_case", pytest_params(PROJECT_EXPRESSION_TESTS))
def test_project_expression_cases(collection: Any, test_case: StageTestCase):
    """Test that expression operators work within $project."""
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
