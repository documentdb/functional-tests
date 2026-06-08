"""
Representative BSON comparison engine wiring tests for $min.

A small sample of cross-type comparisons to confirm $min delegates to the BSON
comparison engine correctly. Not an exhaustive matrix — full BSON ordering
coverage lives in /core/data_types/bson_types/.

Also tests that $min accepts all BSON types as the comparison value
(input type acceptance).
"""

from datetime import datetime, timezone

import pytest
from bson import Binary, Code, Decimal128, Int64, MaxKey, MinKey, ObjectId, Regex, Timestamp

from documentdb_tests.compatibility.tests.core.operator.update.utils import UpdateTestCase
from documentdb_tests.framework.assertions import assertSuccess
from documentdb_tests.framework.executor import execute_command
from documentdb_tests.framework.parametrize import pytest_params

_DATE = datetime(2023, 6, 15, tzinfo=timezone.utc)

# Property [BSON Wiring]: $min delegates to the BSON comparison engine for cross-type ordering.
TESTS: list[UpdateTestCase] = [
    # Downward transition: Boolean < Date in BSON order (should update for $min).
    UpdateTestCase(
        "boolean_less_than_date_updates",
        setup_docs=[{"_id": 1, "val": _DATE}],
        query={"_id": 1},
        update={"$min": {"val": True}},
        expected={"_id": 1, "val": True},
        msg="$min should update when Boolean < Date in BSON order",
    ),
    # Upward transition: String > Number in BSON order (should NOT update for $min).
    UpdateTestCase(
        "string_vs_number_unchanged",
        setup_docs=[{"_id": 1, "val": 5}],
        query={"_id": 1},
        update={"$min": {"val": "hello"}},
        expected={"_id": 1, "val": 5},
        msg="$min should not update when String > Number in BSON order",
    ),
]

# Property [Input Type Acceptance]: $min accepts all BSON types as the comparison value.
INPUT_TYPE_TESTS: list[UpdateTestCase] = [
    UpdateTestCase(
        "input_type_double",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": 3.14}},
        expected={"_id": 1, "val": 3.14},
        msg="$min should accept double as comparison value",
    ),
    UpdateTestCase(
        "input_type_string",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": "hello"}},
        expected={"_id": 1, "val": "hello"},
        msg="$min should accept string as comparison value",
    ),
    UpdateTestCase(
        "input_type_document",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": {"key": "value"}}},
        expected={"_id": 1, "val": {"key": "value"}},
        msg="$min should accept embedded document as comparison value",
    ),
    UpdateTestCase(
        "input_type_array",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": [1, 2, 3]}},
        expected={"_id": 1, "val": [1, 2, 3]},
        msg="$min should accept array as comparison value",
    ),
    UpdateTestCase(
        "input_type_binary",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": Binary(b"\x00\x01")}},
        expected={"_id": 1, "val": b"\x00\x01"},
        msg="$min should accept Binary as comparison value",
    ),
    UpdateTestCase(
        "input_type_objectid",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": ObjectId("000000000000000000000001")}},
        expected={"_id": 1, "val": ObjectId("000000000000000000000001")},
        msg="$min should accept ObjectId as comparison value",
    ),
    UpdateTestCase(
        "input_type_bool_true",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": True}},
        expected={"_id": 1, "val": True},
        msg="$min should accept boolean true as comparison value",
    ),
    UpdateTestCase(
        "input_type_bool_false",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": False}},
        expected={"_id": 1, "val": False},
        msg="$min should accept boolean false as comparison value",
    ),
    UpdateTestCase(
        "input_type_datetime",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": datetime(2023, 1, 1, tzinfo=timezone.utc)}},
        expected={"_id": 1, "val": datetime(2023, 1, 1, tzinfo=timezone.utc)},
        msg="$min should accept datetime as comparison value",
    ),
    UpdateTestCase(
        "input_type_null",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": None}},
        expected={"_id": 1, "val": None},
        msg="$min should accept null as comparison value",
    ),
    UpdateTestCase(
        "input_type_regex",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": Regex("^abc", "i")}},
        expected={"_id": 1, "val": Regex("^abc", "i")},
        msg="$min should accept Regex as comparison value",
    ),
    UpdateTestCase(
        "input_type_int32",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": 42}},
        expected={"_id": 1, "val": 42},
        msg="$min should accept int32 as comparison value",
    ),
    UpdateTestCase(
        "input_type_int64",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": Int64(42)}},
        expected={"_id": 1, "val": Int64(42)},
        msg="$min should accept Int64 as comparison value",
    ),
    UpdateTestCase(
        "input_type_decimal128",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": Decimal128("42.5")}},
        expected={"_id": 1, "val": Decimal128("42.5")},
        msg="$min should accept Decimal128 as comparison value",
    ),
    UpdateTestCase(
        "input_type_timestamp",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": Timestamp(1, 1)}},
        expected={"_id": 1, "val": Timestamp(1, 1)},
        msg="$min should accept Timestamp as comparison value",
    ),
    UpdateTestCase(
        "input_type_javascript",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": Code("function(){}")}},
        expected={"_id": 1, "val": Code("function(){}")},
        msg="$min should accept JavaScript Code as comparison value",
    ),
    UpdateTestCase(
        "input_type_minkey",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": MinKey()}},
        expected={"_id": 1, "val": MinKey()},
        msg="$min should accept MinKey as comparison value",
    ),
    UpdateTestCase(
        "input_type_maxkey",
        setup_docs=[{"_id": 1, "val": MaxKey()}],
        query={"_id": 1},
        update={"$min": {"val": MaxKey()}},
        expected={"_id": 1, "val": MaxKey()},
        msg="$min should accept MaxKey as comparison value",
    ),
]


@pytest.mark.parametrize("test", pytest_params(TESTS))
def test_min_bson_wiring(collection, test: UpdateTestCase):
    """Smoke test: confirm $min is wired to the BSON comparison engine."""
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
def test_min_input_type_acceptance(collection, test: UpdateTestCase):
    """Test $min accepts all BSON types as comparison value."""
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
