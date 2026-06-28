"""
Representative BSON comparison engine wiring tests for $max.

A small sample of cross-type comparisons to confirm $max delegates to the BSON
comparison engine correctly. Not an exhaustive matrix — full BSON ordering
coverage lives in /core/data_types/bson_types/.

Also tests that $max accepts all BSON types as the comparison value
(input type acceptance).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

# Property [BSON Wiring]: $max delegates to the BSON comparison engine for cross-type ordering.
TESTS: list[UpdateTestCase] = [
    # Upward transition: Number > Null in BSON order (should update for $max).
    UpdateTestCase(
        "null_to_number_updates",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": 1}},
        expected={"_id": 1, "val": 1},
        msg="$max should update when Number > Null in BSON order",
    ),
    # Downward transition: String < ObjectId in BSON order (should NOT update for $max).
    UpdateTestCase(
        "string_vs_objectid_unchanged",
        setup_docs=[{"_id": 1, "val": ObjectId("000000000000000000000001")}],
        query={"_id": 1},
        update={"$max": {"val": "zzz"}},
        expected={"_id": 1, "val": ObjectId("000000000000000000000001")},
        msg="$max should not update when String < ObjectId in BSON order",
    ),
]

# Property [Input Type Acceptance]: $max accepts all BSON types as the comparison value.
INPUT_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "input_type_double",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": 3.14}},
        expected={"_id": 1, "val": 3.14},
        msg="$max should accept double as comparison value",
    ),
    UpdateTestCase(
        "input_type_string",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": "hello"}},
        expected={"_id": 1, "val": "hello"},
        msg="$max should accept string as comparison value",
    ),
    UpdateTestCase(
        "input_type_document",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": {"key": "value"}}},
        expected={"_id": 1, "val": {"key": "value"}},
        msg="$max should accept embedded document as comparison value",
    ),
    UpdateTestCase(
        "input_type_array",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": [1, 2, 3]}},
        expected={"_id": 1, "val": [1, 2, 3]},
        msg="$max should accept array as comparison value",
    ),
    UpdateTestCase(
        "input_type_binary",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": Binary(b"\x00\x01")}},
        expected={"_id": 1, "val": b"\x00\x01"},
        msg="$max should accept Binary as comparison value",
    ),
    UpdateTestCase(
        "input_type_objectid",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": ObjectId("000000000000000000000001")}},
        expected={"_id": 1, "val": ObjectId("000000000000000000000001")},
        msg="$max should accept ObjectId as comparison value",
    ),
    UpdateTestCase(
        "input_type_bool_true",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": True}},
        expected={"_id": 1, "val": True},
        msg="$max should accept boolean true as comparison value",
    ),
    UpdateTestCase(
        "input_type_bool_false",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": False}},
        expected={"_id": 1, "val": False},
        msg="$max should accept boolean false as comparison value",
    ),
    UpdateTestCase(
        "input_type_datetime",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": datetime(2023, 1, 1, tzinfo=timezone.utc)}},
        expected={"_id": 1, "val": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        msg="$max should accept datetime as comparison value",
    ),
    UpdateTestCase(
        "input_type_null",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": None}},
        expected={"_id": 1, "val": None},
        msg="$max should accept null as comparison value",
    ),
    UpdateTestCase(
        "input_type_regex",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": Regex("^abc", "i")}},
        expected={"_id": 1, "val": Regex("^abc", "i")},
        msg="$max should accept Regex as comparison value",
    ),
    UpdateTestCase(
        "input_type_int32",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": 42}},
        expected={"_id": 1, "val": 42},
        msg="$max should accept int32 as comparison value",
    ),
    UpdateTestCase(
        "input_type_int64",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": Int64(42)}},
        expected={"_id": 1, "val": Int64(42)},
        msg="$max should accept Int64 as comparison value",
    ),
    UpdateTestCase(
        "input_type_decimal128",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": Decimal128("42.5")}},
        expected={"_id": 1, "val": Decimal128("42.5")},
        msg="$max should accept Decimal128 as comparison value",
    ),
    UpdateTestCase(
        "input_type_timestamp",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": Timestamp(1, 1)}},
        expected={"_id": 1, "val": Timestamp(1, 1)},
        msg="$max should accept Timestamp as comparison value",
    ),
    UpdateTestCase(
        "input_type_javascript",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": Code("function(){}")}},
        expected={"_id": 1, "val": Code("function(){}")},
        msg="$max should accept JavaScript Code as comparison value",
    ),
    UpdateTestCase(
        "input_type_minkey",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": MinKey()}},
        expected={"_id": 1, "val": None},
        msg="$max should accept MinKey as comparison value",
    ),
    UpdateTestCase(
        "input_type_maxkey",
        setup_docs=[{"_id": 1, "val": None}],
        query={"_id": 1},
        update={"$max": {"val": MaxKey()}},
        expected={"_id": 1, "val": MaxKey()},
        msg="$max should accept MaxKey as comparison value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_max_bson_wiring(collection, test: UpdateTestCase):
    """Smoke test: confirm $max is wired to the BSON comparison engine."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)


@pytest.mark.parametrize("test", pytest_params(INPUT_TYPE_TESTS))
def test_max_input_type_acceptance(collection, test: UpdateTestCase):
    """Test $max accepts all BSON types as comparison value."""
    if test.setup_docs:
        collection.insert_many(test.setup_docs)

    execute_command(
        collection,
        {"update": collection.name, "updates": [{"q": test.query, "u": test.update}]},
    )

    result = execute_command(
        collection, {"find": collection.name, "filter": {"_id": test.expected["_id"]}}
    )
    assertSuccess(result, [test.expected], msg=test.msg)
