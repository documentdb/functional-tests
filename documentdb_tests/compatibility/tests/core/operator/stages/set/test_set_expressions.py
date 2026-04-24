from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import pytest
from bson import Binary, Decimal128, Int64, ObjectId, Timestamp

from documentdb_tests.compatibility.tests.core.operator.stages.set.utils.set_common import (
    STAGE_NAMES,
    replace_stage_name,
)
from documentdb_tests.compatibility.tests.core.operator.stages.utils.stage_test_case import (
    StageTestCase,
    populate_collection,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Expression Support]: each expression operator produces the correct
# result when used as a computed field in $set.
SET_EXPRESSION_TESTS: list[StageTestCase] = [
    # Arithmetic.
    StageTestCase(
        "expr_abs",
        docs=[{"_id": 1, "a": -5}],
        pipeline=[{"$set": {"r": {"$abs": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$abs should work in $set",
    ),
    StageTestCase(
        "expr_add",
        docs=[{"_id": 1, "a": 3, "b": 4}],
        pipeline=[{"$set": {"r": {"$add": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$add should work in $set",
    ),
    StageTestCase(
        "expr_ceil",
        docs=[{"_id": 1, "a": 2.3}],
        pipeline=[{"$set": {"r": {"$ceil": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$ceil should work in $set",
    ),
    StageTestCase(
        "expr_divide",
        docs=[{"_id": 1, "a": 10, "b": 4}],
        pipeline=[{"$set": {"r": {"$divide": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.5}],
        msg="$divide should work in $set",
    ),
    StageTestCase(
        "expr_exp",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$set": {"r": {"$exp": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.0}],
        msg="$exp should work in $set",
    ),
    StageTestCase(
        "expr_floor",
        docs=[{"_id": 1, "a": 2.7}],
        pipeline=[{"$set": {"r": {"$floor": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$floor should work in $set",
    ),
    StageTestCase(
        "expr_ln",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[{"$set": {"r": {"$ln": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.302585092994046}],
        msg="$ln should work in $set",
    ),
    StageTestCase(
        "expr_log",
        docs=[{"_id": 1, "a": 100, "b": 10}],
        pipeline=[{"$set": {"r": {"$log": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$log should work in $set",
    ),
    StageTestCase(
        "expr_log10",
        docs=[{"_id": 1, "a": 1000}],
        pipeline=[{"$set": {"r": {"$log10": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$log10 should work in $set",
    ),
    StageTestCase(
        "expr_mod",
        docs=[{"_id": 1, "a": 10, "b": 3}],
        pipeline=[{"$set": {"r": {"$mod": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$mod should work in $set",
    ),
    StageTestCase(
        "expr_multiply",
        docs=[{"_id": 1, "a": 3, "b": 4}],
        pipeline=[{"$set": {"r": {"$multiply": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 12}],
        msg="$multiply should work in $set",
    ),
    StageTestCase(
        "expr_pow",
        docs=[{"_id": 1, "a": 2, "b": 3}],
        pipeline=[{"$set": {"r": {"$pow": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 8}],
        msg="$pow should work in $set",
    ),
    StageTestCase(
        "expr_round",
        docs=[{"_id": 1, "a": 2.567}],
        pipeline=[{"$set": {"r": {"$round": ["$a", 1]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.6}],
        msg="$round should work in $set",
    ),
    StageTestCase(
        "expr_sqrt",
        docs=[{"_id": 1, "a": 9}],
        pipeline=[{"$set": {"r": {"$sqrt": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$sqrt should work in $set",
    ),
    StageTestCase(
        "expr_subtract",
        docs=[{"_id": 1, "a": 10, "b": 3}],
        pipeline=[{"$set": {"r": {"$subtract": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$subtract should work in $set",
    ),
    StageTestCase(
        "expr_trunc",
        docs=[{"_id": 1, "a": 2.9}],
        pipeline=[{"$set": {"r": {"$trunc": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$trunc should work in $set",
    ),
    StageTestCase(
        "expr_sigmoid",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$set": {"r": {"$sigmoid": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.5}],
        msg="$sigmoid should work in $set",
    ),
    # Array.
    StageTestCase(
        "expr_arrayElemAt",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$set": {"r": {"$arrayElemAt": ["$a", 1]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 20}],
        msg="$arrayElemAt should work in $set",
    ),
    StageTestCase(
        "expr_arrayToObject",
        docs=[{"_id": 1, "a": [["k", "v"]]}],
        pipeline=[{"$set": {"r": {"$arrayToObject": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": {"k": "v"}}],
        msg="$arrayToObject should work in $set",
    ),
    StageTestCase(
        "expr_concatArrays",
        docs=[{"_id": 1, "a": [1], "b": [2]}],
        pipeline=[{"$set": {"r": {"$concatArrays": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$concatArrays should work in $set",
    ),
    StageTestCase(
        "expr_filter",
        docs=[{"_id": 1, "a": [1, 2, 3, 4]}],
        pipeline=[
            {"$set": {"r": {"$filter": {"input": "$a", "cond": {"$gt": ["$$this", 2]}}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": [3, 4]}],
        msg="$filter should work in $set",
    ),
    StageTestCase(
        "expr_firstN",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$set": {"r": {"$firstN": {"input": "$a", "n": 2}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$firstN should work in $set",
    ),
    StageTestCase(
        "expr_in",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[{"$set": {"r": {"$in": ["$a", [1, 2, 3]]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$in should work in $set",
    ),
    StageTestCase(
        "expr_indexOfArray",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$set": {"r": {"$indexOfArray": ["$a", 20]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$indexOfArray should work in $set",
    ),
    StageTestCase(
        "expr_isArray",
        docs=[{"_id": 1, "a": [1, 2]}],
        pipeline=[{"$set": {"r": {"$isArray": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$isArray should work in $set",
    ),
    StageTestCase(
        "expr_lastN",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$set": {"r": {"$lastN": {"input": "$a", "n": 2}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [2, 3]}],
        msg="$lastN should work in $set",
    ),
    StageTestCase(
        "expr_map",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[
            {"$set": {"r": {"$map": {"input": "$a", "in": {"$multiply": ["$$this", 2]}}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": [2, 4, 6]}],
        msg="$map should work in $set",
    ),
    StageTestCase(
        "expr_maxN_array",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$set": {"r": {"$maxN": {"input": "$a", "n": 2}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [3, 2]}],
        msg="$maxN should work in $set",
    ),
    StageTestCase(
        "expr_minN_array",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$set": {"r": {"$minN": {"input": "$a", "n": 2}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$minN should work in $set",
    ),
    StageTestCase(
        "expr_objectToArray",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$set": {"r": {"$objectToArray": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [{"k": "x", "v": 1}]}],
        msg="$objectToArray should work in $set",
    ),
    StageTestCase(
        "expr_range",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"r": {"$range": [0, 3]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [0, 1, 2]}],
        msg="$range should work in $set",
    ),
    StageTestCase(
        "expr_reduce",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[
            {
                "$set": {
                    "r": {
                        "$reduce": {
                            "input": "$a",
                            "initialValue": 0,
                            "in": {"$add": ["$$value", "$$this"]},
                        }
                    }
                }
            },
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": 6}],
        msg="$reduce should work in $set",
    ),
    StageTestCase(
        "expr_reverseArray",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$set": {"r": {"$reverseArray": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [3, 2, 1]}],
        msg="$reverseArray should work in $set",
    ),
    StageTestCase(
        "expr_size",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$set": {"r": {"$size": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$size should work in $set",
    ),
    StageTestCase(
        "expr_slice",
        docs=[{"_id": 1, "a": [1, 2, 3, 4]}],
        pipeline=[{"$set": {"r": {"$slice": ["$a", 2]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [1, 2]}],
        msg="$slice should work in $set",
    ),
    StageTestCase(
        "expr_sortArray",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[
            {"$set": {"r": {"$sortArray": {"input": "$a", "sortBy": 1}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": [1, 2, 3]}],
        msg="$sortArray should work in $set",
    ),
    StageTestCase(
        "expr_zip",
        docs=[{"_id": 1, "a": [1, 2], "b": [3, 4]}],
        pipeline=[{"$set": {"r": {"$zip": {"inputs": ["$a", "$b"]}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [[1, 3], [2, 4]]}],
        msg="$zip should work in $set",
    ),
    # Bitwise.
    StageTestCase(
        "expr_bitAnd",
        docs=[{"_id": 1, "a": 7, "b": 3}],
        pipeline=[{"$set": {"r": {"$bitAnd": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$bitAnd should work in $set",
    ),
    StageTestCase(
        "expr_bitNot",
        docs=[{"_id": 1, "a": Int64(5)}],
        pipeline=[{"$set": {"r": {"$bitNot": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Int64(-6)}],
        msg="$bitNot should work in $set",
    ),
    StageTestCase(
        "expr_bitOr",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$set": {"r": {"$bitOr": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$bitOr should work in $set",
    ),
    StageTestCase(
        "expr_bitXor",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$set": {"r": {"$bitXor": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 6}],
        msg="$bitXor should work in $set",
    ),
    # Boolean.
    StageTestCase(
        "expr_and",
        docs=[{"_id": 1, "a": True, "b": False}],
        pipeline=[{"$set": {"r": {"$and": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": False}],
        msg="$and should work in $set",
    ),
    StageTestCase(
        "expr_not",
        docs=[{"_id": 1, "a": False}],
        pipeline=[{"$set": {"r": {"$not": ["$a"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$not should work in $set",
    ),
    StageTestCase(
        "expr_or",
        docs=[{"_id": 1, "a": False, "b": True}],
        pipeline=[{"$set": {"r": {"$or": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$or should work in $set",
    ),
    # Comparisons.
    StageTestCase(
        "expr_cmp",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$set": {"r": {"$cmp": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$cmp should work in $set",
    ),
    StageTestCase(
        "expr_eq",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        pipeline=[{"$set": {"r": {"$eq": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$eq should work in $set",
    ),
    StageTestCase(
        "expr_gt",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$set": {"r": {"$gt": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$gt should work in $set",
    ),
    StageTestCase(
        "expr_gte",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        pipeline=[{"$set": {"r": {"$gte": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$gte should work in $set",
    ),
    StageTestCase(
        "expr_lt",
        docs=[{"_id": 1, "a": 3, "b": 5}],
        pipeline=[{"$set": {"r": {"$lt": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$lt should work in $set",
    ),
    StageTestCase(
        "expr_lte",
        docs=[{"_id": 1, "a": 5, "b": 5}],
        pipeline=[{"$set": {"r": {"$lte": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$lte should work in $set",
    ),
    StageTestCase(
        "expr_ne",
        docs=[{"_id": 1, "a": 5, "b": 3}],
        pipeline=[{"$set": {"r": {"$ne": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$ne should work in $set",
    ),
    # Conditional.
    StageTestCase(
        "expr_cond",
        docs=[{"_id": 1, "a": 10}],
        pipeline=[
            {"$set": {"r": {"$cond": [{"$gt": ["$a", 5]}, "big", "small"]}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": "big"}],
        msg="$cond should work in $set",
    ),
    StageTestCase(
        "expr_ifNull",
        docs=[{"_id": 1, "a": None}],
        pipeline=[{"$set": {"r": {"$ifNull": ["$a", "default"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "default"}],
        msg="$ifNull should work in $set",
    ),
    StageTestCase(
        "expr_switch",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[
            {
                "$set": {
                    "r": {
                        "$switch": {
                            "branches": [{"case": {"$eq": ["$a", 2]}, "then": "two"}],
                            "default": "other",
                        }
                    }
                }
            },
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": "two"}],
        msg="$switch should work in $set",
    ),
    # Date.
    StageTestCase(
        "expr_dateAdd",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[
            {"$set": {"r": {"$dateAdd": {"startDate": "$d", "unit": "day", "amount": 1}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": datetime(2024, 1, 2)}],
        msg="$dateAdd should work in $set",
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
            {"$set": {"r": {"$dateDiff": {"startDate": "$a", "endDate": "$b", "unit": "day"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": Int64(3)}],
        msg="$dateDiff should work in $set",
    ),
    StageTestCase(
        "expr_dateFromParts",
        docs=[{"_id": 1}],
        pipeline=[
            {"$set": {"r": {"$dateFromParts": {"year": 2024, "month": 6, "day": 15}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": datetime(2024, 6, 15)}],
        msg="$dateFromParts should work in $set",
    ),
    StageTestCase(
        "expr_dateFromString",
        docs=[{"_id": 1}],
        pipeline=[
            {"$set": {"r": {"$dateFromString": {"dateString": "2024-01-01"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": datetime(2024, 1, 1)}],
        msg="$dateFromString should work in $set",
    ),
    StageTestCase(
        "expr_dateSubtract",
        docs=[{"_id": 1, "d": datetime(2024, 1, 3, tzinfo=timezone.utc)}],
        pipeline=[
            {"$set": {"r": {"$dateSubtract": {"startDate": "$d", "unit": "day", "amount": 1}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": datetime(2024, 1, 2)}],
        msg="$dateSubtract should work in $set",
    ),
    StageTestCase(
        "expr_dateToParts",
        docs=[{"_id": 1, "d": datetime(2024, 3, 15, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$dateToParts": {"date": "$d"}}}}, {"$project": {"r": 1}}],
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
        msg="$dateToParts should work in $set",
    ),
    StageTestCase(
        "expr_dateToString",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[
            {"$set": {"r": {"$dateToString": {"date": "$d", "format": "%Y-%m-%d"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": "2024-01-01"}],
        msg="$dateToString should work in $set",
    ),
    StageTestCase(
        "expr_dateTrunc",
        docs=[{"_id": 1, "d": datetime(2024, 3, 15, 10, 30, tzinfo=timezone.utc)}],
        pipeline=[
            {"$set": {"r": {"$dateTrunc": {"date": "$d", "unit": "month"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": datetime(2024, 3, 1)}],
        msg="$dateTrunc should work in $set",
    ),
    StageTestCase(
        "expr_dayOfMonth",
        docs=[{"_id": 1, "d": datetime(2024, 3, 15, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$dayOfMonth": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 15}],
        msg="$dayOfMonth should work in $set",
    ),
    StageTestCase(
        "expr_dayOfWeek",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$dayOfWeek": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$dayOfWeek should work in $set",
    ),
    StageTestCase(
        "expr_dayOfYear",
        docs=[{"_id": 1, "d": datetime(2024, 2, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$dayOfYear": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 32}],
        msg="$dayOfYear should work in $set",
    ),
    StageTestCase(
        "expr_hour",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 14, 0, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$hour": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 14}],
        msg="$hour should work in $set",
    ),
    StageTestCase(
        "expr_isoDayOfWeek",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$isoDayOfWeek": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$isoDayOfWeek should work in $set",
    ),
    StageTestCase(
        "expr_isoWeek",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$isoWeek": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$isoWeek should work in $set",
    ),
    StageTestCase(
        "expr_isoWeekYear",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$isoWeekYear": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Int64(2024)}],
        msg="$isoWeekYear should work in $set",
    ),
    StageTestCase(
        "expr_millisecond",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 0, 0, 0, 123000, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$millisecond": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 123}],
        msg="$millisecond should work in $set",
    ),
    StageTestCase(
        "expr_minute",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 10, 45, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$minute": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 45}],
        msg="$minute should work in $set",
    ),
    StageTestCase(
        "expr_month",
        docs=[{"_id": 1, "d": datetime(2024, 7, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$month": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 7}],
        msg="$month should work in $set",
    ),
    StageTestCase(
        "expr_second",
        docs=[{"_id": 1, "d": datetime(2024, 1, 1, 0, 0, 30, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$second": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 30}],
        msg="$second should work in $set",
    ),
    StageTestCase(
        "expr_toDate",
        docs=[{"_id": 1, "a": Int64(1704067200000)}],
        pipeline=[{"$set": {"r": {"$toDate": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": datetime(2024, 1, 1)}],
        msg="$toDate should work in $set",
    ),
    StageTestCase(
        "expr_week",
        docs=[{"_id": 1, "d": datetime(2024, 1, 15, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$week": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$week should work in $set",
    ),
    StageTestCase(
        "expr_year",
        docs=[{"_id": 1, "d": datetime(2024, 6, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$set": {"r": {"$year": "$d"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2024}],
        msg="$year should work in $set",
    ),
    # Misc.
    StageTestCase(
        "expr_binarySize",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$binarySize": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$binarySize should work in $set",
    ),
    StageTestCase(
        "expr_bsonSize",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[{"$set": {"r": {"$bsonSize": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 12}],
        msg="$bsonSize should work in $set",
    ),
    StageTestCase(
        "expr_getField",
        docs=[{"_id": 1, "a": {"x": 42}}],
        pipeline=[
            {"$set": {"r": {"$getField": {"field": "x", "input": "$a"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": 42}],
        msg="$getField should work in $set",
    ),
    StageTestCase(
        "expr_let",
        docs=[{"_id": 1, "a": 5}],
        pipeline=[
            {"$set": {"r": {"$let": {"vars": {"x": "$a"}, "in": {"$multiply": ["$$x", 2]}}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": 10}],
        msg="$let should work in $set",
    ),
    StageTestCase(
        "expr_literal",
        docs=[{"_id": 1}],
        pipeline=[{"$set": {"r": {"$literal": "$notAFieldPath"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "$notAFieldPath"}],
        msg="$literal should work in $set",
    ),
    StageTestCase(
        "expr_toHashedIndexKey",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$toHashedIndexKey": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Int64(5347277839332858538)}],
        msg="$toHashedIndexKey should work in $set",
    ),
    # Object.
    StageTestCase(
        "expr_mergeObjects",
        docs=[{"_id": 1, "a": {"x": 1}, "b": {"y": 2}}],
        pipeline=[{"$set": {"r": {"$mergeObjects": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": {"x": 1, "y": 2}}],
        msg="$mergeObjects should work in $set",
    ),
    StageTestCase(
        "expr_setField",
        docs=[{"_id": 1, "a": {"x": 1}}],
        pipeline=[
            {"$set": {"r": {"$setField": {"field": "y", "input": "$a", "value": 2}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": {"x": 1, "y": 2}}],
        msg="$setField should work in $set",
    ),
    StageTestCase(
        "expr_unsetField",
        docs=[{"_id": 1, "a": {"x": 1, "y": 2}}],
        pipeline=[
            {"$set": {"r": {"$unsetField": {"field": "x", "input": "$a"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": {"y": 2}}],
        msg="$unsetField should work in $set",
    ),
    # Set.
    StageTestCase(
        "expr_allElementsTrue",
        docs=[{"_id": 1, "a": [True, True]}],
        pipeline=[{"$set": {"r": {"$allElementsTrue": ["$a"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$allElementsTrue should work in $set",
    ),
    StageTestCase(
        "expr_anyElementTrue",
        docs=[{"_id": 1, "a": [False, True]}],
        pipeline=[{"$set": {"r": {"$anyElementTrue": ["$a"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$anyElementTrue should work in $set",
    ),
    StageTestCase(
        "expr_setDifference",
        docs=[{"_id": 1, "a": [1, 2, 3], "b": [2]}],
        pipeline=[{"$set": {"r": {"$setDifference": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [1, 3]}],
        msg="$setDifference should work in $set",
    ),
    StageTestCase(
        "expr_setEquals",
        docs=[{"_id": 1, "a": [1, 2], "b": [2, 1]}],
        pipeline=[{"$set": {"r": {"$setEquals": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$setEquals should work in $set",
    ),
    StageTestCase(
        "expr_setIntersection",
        docs=[{"_id": 1, "a": [1, 2, 3], "b": [2, 3, 4]}],
        pipeline=[{"$set": {"r": {"$setIntersection": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [2, 3]}],
        msg="$setIntersection should work in $set",
    ),
    StageTestCase(
        "expr_setIsSubset",
        docs=[{"_id": 1, "a": [1, 2], "b": [1, 2, 3]}],
        pipeline=[{"$set": {"r": {"$setIsSubset": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$setIsSubset should work in $set",
    ),
    # String.
    StageTestCase(
        "expr_concat",
        docs=[{"_id": 1, "a": "hello", "b": " world"}],
        pipeline=[{"$set": {"r": {"$concat": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "hello world"}],
        msg="$concat should work in $set",
    ),
    StageTestCase(
        "expr_indexOfBytes",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$indexOfBytes": ["$a", "ll"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$indexOfBytes should work in $set",
    ),
    StageTestCase(
        "expr_indexOfCP",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$indexOfCP": ["$a", "ll"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2}],
        msg="$indexOfCP should work in $set",
    ),
    StageTestCase(
        "expr_ltrim",
        docs=[{"_id": 1, "a": "  hi"}],
        pipeline=[{"$set": {"r": {"$ltrim": {"input": "$a"}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "hi"}],
        msg="$ltrim should work in $set",
    ),
    StageTestCase(
        "expr_regexFind",
        docs=[{"_id": 1, "a": "hello 123"}],
        pipeline=[
            {"$set": {"r": {"$regexFind": {"input": "$a", "regex": "[0-9]+"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": {"match": "123", "idx": 6, "captures": []}}],
        msg="$regexFind should work in $set",
    ),
    StageTestCase(
        "expr_regexFindAll",
        docs=[{"_id": 1, "a": "a1b2"}],
        pipeline=[
            {"$set": {"r": {"$regexFindAll": {"input": "$a", "regex": "[0-9]"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[
            {
                "_id": 1,
                "r": [
                    {"match": "1", "idx": 1, "captures": []},
                    {"match": "2", "idx": 3, "captures": []},
                ],
            }
        ],
        msg="$regexFindAll should work in $set",
    ),
    StageTestCase(
        "expr_regexMatch",
        docs=[{"_id": 1, "a": "hello123"}],
        pipeline=[
            {"$set": {"r": {"$regexMatch": {"input": "$a", "regex": "[0-9]+"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": True}],
        msg="$regexMatch should work in $set",
    ),
    StageTestCase(
        "expr_replaceAll",
        docs=[{"_id": 1, "a": "aabbcc"}],
        pipeline=[
            {"$set": {"r": {"$replaceAll": {"input": "$a", "find": "b", "replacement": "x"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": "aaxxcc"}],
        msg="$replaceAll should work in $set",
    ),
    StageTestCase(
        "expr_replaceOne",
        docs=[{"_id": 1, "a": "aabbcc"}],
        pipeline=[
            {"$set": {"r": {"$replaceOne": {"input": "$a", "find": "b", "replacement": "x"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": "aaxbcc"}],
        msg="$replaceOne should work in $set",
    ),
    StageTestCase(
        "expr_rtrim",
        docs=[{"_id": 1, "a": "hi  "}],
        pipeline=[{"$set": {"r": {"$rtrim": {"input": "$a"}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "hi"}],
        msg="$rtrim should work in $set",
    ),
    StageTestCase(
        "expr_split",
        docs=[{"_id": 1, "a": "a,b,c"}],
        pipeline=[{"$set": {"r": {"$split": ["$a", ","]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": ["a", "b", "c"]}],
        msg="$split should work in $set",
    ),
    StageTestCase(
        "expr_strcasecmp",
        docs=[{"_id": 1, "a": "abc", "b": "ABC"}],
        pipeline=[{"$set": {"r": {"$strcasecmp": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0}],
        msg="$strcasecmp should work in $set",
    ),
    StageTestCase(
        "expr_strLenBytes",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$strLenBytes": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$strLenBytes should work in $set",
    ),
    StageTestCase(
        "expr_strLenCP",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$strLenCP": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 5}],
        msg="$strLenCP should work in $set",
    ),
    StageTestCase(
        "expr_substr",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$substr": ["$a", 1, 3]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "ell"}],
        msg="$substr should work in $set",
    ),
    StageTestCase(
        "expr_substrBytes",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$substrBytes": ["$a", 1, 3]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "ell"}],
        msg="$substrBytes should work in $set",
    ),
    StageTestCase(
        "expr_substrCP",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$substrCP": ["$a", 1, 3]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "ell"}],
        msg="$substrCP should work in $set",
    ),
    StageTestCase(
        "expr_toLower",
        docs=[{"_id": 1, "a": "HELLO"}],
        pipeline=[{"$set": {"r": {"$toLower": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "hello"}],
        msg="$toLower should work in $set",
    ),
    StageTestCase(
        "expr_toString",
        docs=[{"_id": 1, "a": 123}],
        pipeline=[{"$set": {"r": {"$toString": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "123"}],
        msg="$toString should work in $set",
    ),
    StageTestCase(
        "expr_toUpper",
        docs=[{"_id": 1, "a": "hello"}],
        pipeline=[{"$set": {"r": {"$toUpper": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "HELLO"}],
        msg="$toUpper should work in $set",
    ),
    StageTestCase(
        "expr_trim",
        docs=[{"_id": 1, "a": "  hi  "}],
        pipeline=[{"$set": {"r": {"$trim": {"input": "$a"}}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "hi"}],
        msg="$trim should work in $set",
    ),
    # Timestamp.
    StageTestCase(
        "expr_tsIncrement",
        docs=[{"_id": 1, "t": Timestamp(100, 5)}],
        pipeline=[{"$set": {"r": {"$tsIncrement": "$t"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Int64(5)}],
        msg="$tsIncrement should work in $set",
    ),
    StageTestCase(
        "expr_tsSecond",
        docs=[{"_id": 1, "t": Timestamp(100, 5)}],
        pipeline=[{"$set": {"r": {"$tsSecond": "$t"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Int64(100)}],
        msg="$tsSecond should work in $set",
    ),
    # Trigonometry.
    StageTestCase(
        "expr_acos",
        docs=[{"_id": 1, "a": 0.5}],
        pipeline=[{"$set": {"r": {"$acos": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.0471975511965979}],
        msg="$acos should work in $set",
    ),
    StageTestCase(
        "expr_acosh",
        docs=[{"_id": 1, "a": 2}],
        pipeline=[{"$set": {"r": {"$acosh": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.3169578969248166}],
        msg="$acosh should work in $set",
    ),
    StageTestCase(
        "expr_asin",
        docs=[{"_id": 1, "a": 0.5}],
        pipeline=[{"$set": {"r": {"$asin": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.5235987755982989}],
        msg="$asin should work in $set",
    ),
    StageTestCase(
        "expr_asinh",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$asinh": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.881373587019543}],
        msg="$asinh should work in $set",
    ),
    StageTestCase(
        "expr_atan",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$atan": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.7853981633974483}],
        msg="$atan should work in $set",
    ),
    StageTestCase(
        "expr_atan2",
        docs=[{"_id": 1, "a": 1, "b": 1}],
        pipeline=[{"$set": {"r": {"$atan2": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.7853981633974483}],
        msg="$atan2 should work in $set",
    ),
    StageTestCase(
        "expr_atanh",
        docs=[{"_id": 1, "a": 0.5}],
        pipeline=[{"$set": {"r": {"$atanh": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.5493061443340548}],
        msg="$atanh should work in $set",
    ),
    StageTestCase(
        "expr_cos",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$set": {"r": {"$cos": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.0}],
        msg="$cos should work in $set",
    ),
    StageTestCase(
        "expr_cosh",
        docs=[{"_id": 1, "a": 0}],
        pipeline=[{"$set": {"r": {"$cosh": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.0}],
        msg="$cosh should work in $set",
    ),
    StageTestCase(
        "expr_degreesToRadians",
        docs=[{"_id": 1, "a": 90}],
        pipeline=[{"$set": {"r": {"$degreesToRadians": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.5707963267948966}],
        msg="$degreesToRadians should work in $set",
    ),
    StageTestCase(
        "expr_radiansToDegrees",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$radiansToDegrees": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 57.29577951308232}],
        msg="$radiansToDegrees should work in $set",
    ),
    StageTestCase(
        "expr_sin",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$sin": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.8414709848078965}],
        msg="$sin should work in $set",
    ),
    StageTestCase(
        "expr_sinh",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$sinh": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.1752011936438014}],
        msg="$sinh should work in $set",
    ),
    StageTestCase(
        "expr_tan",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$tan": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.5574077246549023}],
        msg="$tan should work in $set",
    ),
    StageTestCase(
        "expr_tanh",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$tanh": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 0.7615941559557649}],
        msg="$tanh should work in $set",
    ),
    # Type.
    StageTestCase(
        "expr_convert",
        docs=[{"_id": 1, "a": "123"}],
        pipeline=[
            {"$set": {"r": {"$convert": {"input": "$a", "to": "int"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": 123}],
        msg="$convert should work in $set",
    ),
    StageTestCase(
        "expr_isNumber",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"r": {"$isNumber": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$isNumber should work in $set",
    ),
    StageTestCase(
        "expr_toBool",
        docs=[{"_id": 1, "a": 1}],
        pipeline=[{"$set": {"r": {"$toBool": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": True}],
        msg="$toBool should work in $set",
    ),
    StageTestCase(
        "expr_toDecimal",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"r": {"$toDecimal": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Decimal128("42")}],
        msg="$toDecimal should work in $set",
    ),
    StageTestCase(
        "expr_toDouble",
        docs=[{"_id": 1, "a": "3.14"}],
        pipeline=[{"$set": {"r": {"$toDouble": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3.14}],
        msg="$toDouble should work in $set",
    ),
    StageTestCase(
        "expr_toInt",
        docs=[{"_id": 1, "a": 3.9}],
        pipeline=[{"$set": {"r": {"$toInt": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$toInt should work in $set",
    ),
    StageTestCase(
        "expr_toLong",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"r": {"$toLong": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Int64(42)}],
        msg="$toLong should work in $set",
    ),
    StageTestCase(
        "expr_toObjectId",
        docs=[{"_id": 1, "a": "507f1f77bcf86cd799439011"}],
        pipeline=[{"$set": {"r": {"$toObjectId": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": ObjectId("507f1f77bcf86cd799439011")}],
        msg="$toObjectId should work in $set",
    ),
    StageTestCase(
        "expr_type",
        docs=[{"_id": 1, "a": 42}],
        pipeline=[{"$set": {"r": {"$type": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": "int"}],
        msg="$type should work in $set",
    ),
    StageTestCase(
        "expr_toUUID",
        docs=[{"_id": 1, "a": "12345678-1234-1234-1234-123456789abc"}],
        pipeline=[{"$set": {"r": {"$toUUID": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": Binary.from_uuid(UUID("12345678-1234-1234-1234-123456789abc"))}],
        msg="$toUUID should work in $set",
    ),
    # Accumulator (as expressions in $project).
    StageTestCase(
        "expr_sum",
        docs=[{"_id": 1, "a": [1, 2, 3]}],
        pipeline=[{"$set": {"r": {"$sum": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 6}],
        msg="$sum should work in $set",
    ),
    StageTestCase(
        "expr_avg",
        docs=[{"_id": 1, "a": [2, 4, 6]}],
        pipeline=[{"$set": {"r": {"$avg": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 4.0}],
        msg="$avg should work in $set",
    ),
    StageTestCase(
        "expr_min",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$set": {"r": {"$min": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1}],
        msg="$min should work in $set",
    ),
    StageTestCase(
        "expr_max",
        docs=[{"_id": 1, "a": [3, 1, 2]}],
        pipeline=[{"$set": {"r": {"$max": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 3}],
        msg="$max should work in $set",
    ),
    StageTestCase(
        "expr_first",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$set": {"r": {"$first": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 10}],
        msg="$first should work in $set",
    ),
    StageTestCase(
        "expr_last",
        docs=[{"_id": 1, "a": [10, 20, 30]}],
        pipeline=[{"$set": {"r": {"$last": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 30}],
        msg="$last should work in $set",
    ),
    StageTestCase(
        "expr_stdDevPop",
        docs=[{"_id": 1, "a": [2, 4, 4, 4, 5, 5, 7, 9]}],
        pipeline=[{"$set": {"r": {"$stdDevPop": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 2.0}],
        msg="$stdDevPop should work in $set",
    ),
    StageTestCase(
        "expr_stdDevSamp",
        docs=[{"_id": 1, "a": [1, 3]}],
        pipeline=[{"$set": {"r": {"$stdDevSamp": "$a"}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": 1.4142135623730951}],
        msg="$stdDevSamp should work in $set",
    ),
    StageTestCase(
        "expr_median",
        docs=[{"_id": 1, "a": [1, 2, 3, 4, 5]}],
        pipeline=[
            {"$set": {"r": {"$median": {"input": "$a", "method": "approximate"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": 3.0}],
        msg="$median should work in $set",
    ),
    StageTestCase(
        "expr_percentile",
        docs=[{"_id": 1, "a": [1, 2, 3, 4, 5]}],
        pipeline=[
            {"$set": {"r": {"$percentile": {"input": "$a", "p": [0.5], "method": "approximate"}}}},
            {"$project": {"r": 1}},
        ],
        expected=[{"_id": 1, "r": [3.0]}],
        msg="$percentile should work in $set",
    ),
    # Set (additional).
    StageTestCase(
        "expr_setUnion",
        docs=[{"_id": 1, "a": [1, 2], "b": [2, 3]}],
        pipeline=[{"$set": {"r": {"$setUnion": ["$a", "$b"]}}}, {"$project": {"r": 1}}],
        expected=[{"_id": 1, "r": [1, 2, 3]}],
        msg="$setUnion should work in $set",
    ),
]


@pytest.mark.aggregate
@pytest.mark.parametrize("stage_name", STAGE_NAMES)
@pytest.mark.parametrize("test_case", pytest_params(SET_EXPRESSION_TESTS))
def test_set_expression_cases(collection: Any, stage_name: str, test_case: StageTestCase):
    """Test that expression operators work within $set / $addFields."""
    populate_collection(collection, test_case)
    pipeline = replace_stage_name(test_case.pipeline, stage_name)
    result = execute_command(
        collection,
        {
            "aggregate": collection.name,
            "pipeline": pipeline,
            "cursor": {},
        },
    )
    assertResult(
        result,
        expected=test_case.expected,
        error_code=test_case.error_code,
        msg=f"{stage_name!r}: {test_case.msg!r}",
    )
