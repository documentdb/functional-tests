"""
Tests for $avg accumulator non-numeric type handling in $group context.

Covers all non-numeric BSON types (string, boolean, object, ObjectId, datetime,
Timestamp, Binary, Regex, Code, MinKey, MaxKey, arrays) and verifies they are
silently ignored and excluded from both sum and count.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertResult
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [Non-Numeric Types Ignored]: all non-numeric BSON types are
# silently ignored and excluded from both sum and count, producing null
# when no numeric values remain.
AVG_NON_NUMERIC_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "string",
        docs=[{"v": "hello"}, {"v": "world"}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore string values and return null",
    ),
    AccumulatorTestCase(
        "boolean_true",
        docs=[{"v": True}, {"v": True}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore boolean true without coercing to numeric",
    ),
    AccumulatorTestCase(
        "boolean_false",
        docs=[{"v": False}, {"v": False}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore boolean false without coercing to numeric",
    ),
    AccumulatorTestCase(
        "boolean_not_numeric",
        docs=[{"_id": 0, "v": False}, {"_id": 1, "v": True}],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="Booleans should not be treated as 0/1 in avg",
    ),
    AccumulatorTestCase(
        "object",
        docs=[{"v": {"x": 1}}, {"v": {"y": 2}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore plain objects",
    ),
    AccumulatorTestCase(
        "empty_object",
        docs=[{"v": {}}, {"v": {}}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore empty objects",
    ),
    AccumulatorTestCase(
        "objectid",
        docs=[{"v": ObjectId()}, {"v": ObjectId()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore ObjectId values",
    ),
    AccumulatorTestCase(
        "datetime",
        docs=[
            {"v": datetime(2023, 1, 1, tzinfo=timezone.utc)},
            {"v": datetime(2024, 1, 1, tzinfo=timezone.utc)},
        ],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore datetime values",
    ),
    AccumulatorTestCase(
        "timestamp",
        docs=[{"v": Timestamp(1, 1)}, {"v": Timestamp(2, 1)}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Timestamp values",
    ),
    AccumulatorTestCase(
        "binary",
        docs=[{"v": Binary(b"\x01")}, {"v": Binary(b"\x02")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Binary values",
    ),
    AccumulatorTestCase(
        "regex",
        docs=[{"v": Regex("abc")}, {"v": Regex("def")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Regex values",
    ),
    AccumulatorTestCase(
        "code",
        docs=[{"v": Code("x")}, {"v": Code("y")}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore Code values",
    ),
    AccumulatorTestCase(
        "minkey",
        docs=[{"v": MinKey()}, {"v": MinKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore MinKey values",
    ),
    AccumulatorTestCase(
        "maxkey",
        docs=[{"v": MaxKey()}, {"v": MaxKey()}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore MaxKey values",
    ),
    AccumulatorTestCase(
        "array",
        docs=[{"v": [1, 2, 3]}, {"v": [4, 5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore arrays without unwrapping",
    ),
    AccumulatorTestCase(
        "single_element_array",
        docs=[{"v": [42]}, {"v": [7]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should not unwrap single-element numeric arrays",
    ),
    AccumulatorTestCase(
        "empty_array",
        docs=[{"v": []}, {"v": []}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore empty arrays",
    ),
    AccumulatorTestCase(
        "nested_array",
        docs=[{"v": [[1, 2]]}, {"v": [[3]]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should ignore nested arrays",
    ),
    AccumulatorTestCase(
        "array_from_expression",
        docs=[{"v": 1}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": {"$literal": [1, 2, 3]}}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": None}],
        msg="$avg should treat array expressions as non-numeric",
    ),
    AccumulatorTestCase(
        "mixed_with_numerics",
        docs=[{"v": "hello"}, {"v": 10}, {"v": True}, {"v": 20}, {"v": [5]}],
        pipeline=[
            {"$group": {"_id": None, "result": {"$avg": "$v"}}},
            {"$project": {"_id": 0, "result": 1}},
        ],
        expected=[{"result": 15.0}],
        msg="$avg should compute average only over numeric values, ignoring non-numerics",
    ),
    AccumulatorTestCase(
        "all_non_numeric",
        docs=[
            {"_id": 0, "v": "a"},
            {"_id": 1, "v": True},
            {"_id": 2, "v": [1]},
            {"_id": 3, "v": {"x": 1}},
        ],
        pipeline=[{"$group": {"_id": None, "avg": {"$avg": "$v"}}}],
        expected=[{"_id": None, "avg": None}],
        msg="All non-numeric values should return null",
    ),
]


@pytest.mark.parametrize("test_case", pytest_params(AVG_NON_NUMERIC_TESTS))
def test_avg_non_numeric(collection, test_case: AccumulatorTestCase):
    """Test $avg non-numeric type handling in $group context."""
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
