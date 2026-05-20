"""Tests for $min accumulator — BSON comparison order and type distinction ($group)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.accumulators.utils import (
    AccumulatorTestCase,
)
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# ---------------------------------------------------------------------------
# Property [BSON Comparison Order]: $min compares values using BSON comparison
# order when documents contain different types. BSON order:
# MinKey < Number < String < Object < Array < Binary < ObjectId < Boolean
# < Date < Timestamp < Regex < Code < MaxKey.
# ---------------------------------------------------------------------------
MIN_BSON_ORDER_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "bson_minkey_vs_number",
        docs=[{"v": MinKey()}, {"v": 5}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min should pick MinKey over Number (MinKey < Number)",
    ),
    AccumulatorTestCase(
        "bson_number_vs_string",
        docs=[{"v": 100}, {"v": "hello"}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 100}],
        msg="$min should pick Number over String (Number < String)",
    ),
    AccumulatorTestCase(
        "bson_string_vs_object",
        docs=[{"v": "zzz"}, {"v": {"a": 1}}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": "zzz"}],
        msg="$min should pick String over Object (String < Object)",
    ),
    AccumulatorTestCase(
        "bson_object_vs_array",
        docs=[{"v": {"z": 99}}, {"v": [1]}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": {"z": 99}}],
        msg="$min should pick Object over Array (Object < Array)",
    ),
    AccumulatorTestCase(
        "bson_array_vs_binary",
        docs=[{"v": [999]}, {"v": Binary(b"\x00")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": [999]}],
        msg="$min should pick Array over Binary (Array < Binary)",
    ),
    AccumulatorTestCase(
        "bson_binary_vs_objectid",
        docs=[{"v": Binary(b"\xff" * 100)}, {"v": ObjectId("000000000000000000000001")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": b"\xff" * 100}],
        msg="$min should pick Binary over ObjectId (Binary < ObjectId)",
    ),
    AccumulatorTestCase(
        "bson_objectid_vs_boolean",
        docs=[{"v": ObjectId("ffffffffffffffffffffffff")}, {"v": False}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": ObjectId("ffffffffffffffffffffffff")}],
        msg="$min should pick ObjectId over Boolean (ObjectId < Boolean)",
    ),
    AccumulatorTestCase(
        "bson_boolean_vs_datetime",
        docs=[{"v": True}, {"v": datetime(2020, 1, 1, tzinfo=timezone.utc)}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": True}],
        msg="$min should pick Boolean over Date (Boolean < Date)",
    ),
    AccumulatorTestCase(
        "bson_datetime_vs_timestamp",
        docs=[
            {"v": datetime(9999, 12, 31, tzinfo=timezone.utc)},
            {"v": Timestamp(0, 1)},
        ],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": datetime(9999, 12, 31, tzinfo=timezone.utc)}],
        msg="$min should pick Date over Timestamp (Date < Timestamp)",
    ),
    AccumulatorTestCase(
        "bson_timestamp_vs_regex",
        docs=[{"v": Timestamp(4294967295, 4294967295)}, {"v": Regex("a")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Timestamp(4294967295, 4294967295)}],
        msg="$min should pick Timestamp over Regex (Timestamp < Regex)",
    ),
    AccumulatorTestCase(
        "bson_regex_vs_code",
        docs=[{"v": Regex("zzz")}, {"v": Code("a")}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Regex("zzz")}],
        msg="$min should pick Regex over Code (Regex < Code)",
    ),
    AccumulatorTestCase(
        "bson_code_vs_maxkey",
        docs=[{"v": Code("zzz")}, {"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": Code("zzz")}],
        msg="$min should pick Code over MaxKey (Code < MaxKey)",
    ),
    AccumulatorTestCase(
        "bson_minkey_vs_maxkey",
        docs=[{"v": MinKey()}, {"v": MaxKey()}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": MinKey()}],
        msg="$min should pick MinKey over MaxKey (full BSON range)",
    ),
    AccumulatorTestCase(
        "bson_false_vs_zero",
        docs=[{"v": False}, {"v": 0}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 0}],
        msg="$min should pick Number(0) over Boolean(false) (Number < Boolean)",
    ),
    AccumulatorTestCase(
        "bson_true_vs_one",
        docs=[{"v": True}, {"v": 1}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 1}],
        msg="$min should pick Number(1) over Boolean(true) (Number < Boolean)",
    ),
    AccumulatorTestCase(
        "bson_string_before_number",
        docs=[{"v": "hello"}, {"v": 100}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 100}],
        msg="$min should pick Number regardless of document order",
    ),
]


# ---------------------------------------------------------------------------
# Property [BSON Type Distinction]: values of different BSON types are distinct
# even when they appear similar. For $min, the lower BSON type wins.
# ---------------------------------------------------------------------------
MIN_TYPE_DISTINCTION_TESTS: list[AccumulatorTestCase] = [
    AccumulatorTestCase(
        "distinct_empty_string_vs_null",
        docs=[{"v": ""}, {"v": None}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": ""}],
        msg="$min should exclude null and return empty string",
    ),
    AccumulatorTestCase(
        "distinct_numeric_string",
        docs=[{"v": "123"}, {"v": 1_000_000}],
        pipeline=[{"$group": {"_id": None, "result": {"$min": "$v"}}}],
        expected=[{"_id": None, "result": 1_000_000}],
        msg="$min should pick Number over numeric-looking String (Number < String)",
    ),
]


# ---------------------------------------------------------------------------
# Combined success tests
# ---------------------------------------------------------------------------
MIN_GROUP_BSON_ORDER_SUCCESS_TESTS = MIN_BSON_ORDER_TESTS + MIN_TYPE_DISTINCTION_TESTS


@pytest.mark.parametrize("test_case", pytest_params(MIN_GROUP_BSON_ORDER_SUCCESS_TESTS))
def test_accumulator_min_group_bson_order(collection, test_case: AccumulatorTestCase):
    """Test $min accumulator BSON comparison order and type distinction with $group."""
    if test_case.docs:
        collection.insert_many(test_case.docs)
    result = execute_command(
        collection,
        {"aggregate": collection.name, "pipeline": test_case.pipeline, "cursor": {}},
    )
    assertSuccess(result, test_case.expected, msg=test_case.msg)
